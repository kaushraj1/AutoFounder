#!/usr/bin/env python3
"""Split the large AutoFounder AI ``CLAUDE.md`` into modular spec files.

``CLAUDE.md`` is loaded into agent context every session, so keeping it lean
matters. This tool extracts the deep-reference sections into ``.claude/specs/``
and rewrites ``CLAUDE.md`` as a lean index that links to them.

Design
------
* ``CLAUDE.md`` is the source of truth. It is parsed by its **numbered**
  headers (``## 13. ...``, including ``## 45b. ...``); headers inside fenced
  code blocks are ignored.
* Each section is routed to a spec file via :data:`SPEC_PLAN` below — this is
  the "reasoning" baked in as configuration; the script only executes it.
* ``reuse`` specs are hand-curated and richer than ``CLAUDE.md``. They are
  **never written**, only linked from the new index.
* ``create`` specs are generated from the extracted sections. An existing one
  is **skipped** (preserved) unless ``--force`` is passed.
* ``CLAUDE.md`` is always **backed up** before any write, and section numbers
  are preserved in every heading so ``§N`` cross-references stay valid.
* If any section would be dropped (unrouted), the run aborts before writing —
  no content is silently lost.

Usage
-----
    python split_claude.py            # dry-run (default): print the plan, write nothing
    python split_claude.py --write    # perform the split (backs up CLAUDE.md first)
    python split_claude.py --write --force   # also overwrite existing generated specs
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths (resolved relative to this script, so it runs from any working dir)    #
# --------------------------------------------------------------------------- #
BASE = Path(__file__).resolve().parent
DEFAULT_CLAUDE = BASE / ".claude" / "CLAUDE.md"
DEFAULT_SPECS = BASE / ".claude" / "specs"


# --------------------------------------------------------------------------- #
# Section routing config — WHAT goes WHERE. Edit this, not the logic below.    #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class SpecTarget:
    """One destination spec file and the CLAUDE.md sections it owns."""

    file: str          # filename under specs/
    title: str         # H1 title used for generated (``create``) specs
    mode: str          # "create" | "reuse"
    sections: list[str]  # CLAUDE.md section keys (e.g. ["7", "45b"])
    desc: str          # one-line description shown in the nav table


# Sections kept verbatim INSIDE the lean CLAUDE.md (needed every session).
INLINE_SECTIONS: list[str] = ["1", "2", "40", "41", "42"]

# Ordered routing plan. ``reuse`` = existing curated file (link only, never
# written). ``create`` = generated from extracted sections.
SPEC_PLAN: list[SpecTarget] = [
    SpecTarget("architecture.md", "Architecture", "create",
               ["4", "5", "6", "11", "29", "37"],
               "10-layer architecture, workflow, components, data & comms flow"),
    SpecTarget("agents.md", "Agents & Orchestration", "create",
               ["7", "8", "9", "10", "30", "32", "33"],
               "Agent roster, LangGraph orchestration, memory, prompts, tools, RAG"),
    SpecTarget("stack.md", "Tech Stack", "reuse",
               ["13", "14", "15", "17", "18"],
               "Backend, frontend, auth, infra & cloud technology choices"),
    SpecTarget("api-design.md", "API Design", "reuse",
               ["12"],
               "REST/WebSocket contract, envelopes, errors, pagination"),
    SpecTarget("database.md", "Database", "reuse",
               ["19"],
               "Multi-tenant schemas, isolation, Alembic, Redis keys"),
    SpecTarget("integrations.md", "Integrations", "reuse",
               ["16", "31", "43"],
               "Third-party services, LLM providers & model routing"),
    SpecTarget("deployment.md", "Deployment & CI/CD", "reuse",
               ["27", "28"],
               "AWS ECS Fargate, Terraform, environments, pipeline"),
    SpecTarget("mobile.md", "Mobile", "reuse",
               [],
               "Expo (React Native) app conventions"),
    SpecTarget("governance.md", "Governance & Compliance", "create",
               ["34", "35", "39"],
               "6-stage guardrails, compliance, multi-tenancy rules"),
    SpecTarget("operations.md", "Operations & Observability", "create",
               ["20", "21", "22", "23", "24", "25", "26", "36", "38"],
               "Queues, observability, errors, scaling, performance, cost"),
    SpecTarget("product.md", "Product & Roadmap", "create",
               ["3", "44", "45", "45b", "46", "47", "49"],
               "Business objective, pricing, phases, market, risks, future"),
    SpecTarget("decisions.md", "Architecture Decisions", "create",
               ["48"],
               "Reconciliations vs prior design (authoritative decisions)"),
]


# --------------------------------------------------------------------------- #
# Parsing                                                                      #
# --------------------------------------------------------------------------- #
@dataclass
class Section:
    """A single ``## N. Title`` section and its full raw text (incl. heading)."""

    key: str
    title: str
    text: str


_SECTION_RE = re.compile(r"^## (\d+[a-z]?)\.\s+(.*)$")
_FENCE_RE = re.compile(r"^\s*```")


def parse_claude_md(content: str) -> tuple[str, list[Section]]:
    """Split ``content`` into (preamble, sections).

    A section boundary is a top-level numbered header (``## 13. ...``) that is
    NOT inside a fenced code block. Everything before the first such header is
    the preamble. Section text is preserved verbatim, including its heading and
    any trailing ``---`` rule.
    """
    lines = content.splitlines(keepends=True)
    sections: list[Section] = []
    current: Section | None = None
    buf: list[str] = []
    preamble = ""
    in_fence = False

    for line in lines:
        if _FENCE_RE.match(line):
            in_fence = not in_fence
        match = None if in_fence else _SECTION_RE.match(line)
        if match:
            # Flush whatever we were accumulating before this new header.
            if current is None:
                preamble = "".join(buf)
            else:
                current.text = "".join(buf)
                sections.append(current)
            current = Section(key=match.group(1), title=match.group(2).strip(), text="")
            buf = [line]
        else:
            buf.append(line)

    # Flush the final block.
    if current is None:
        preamble = "".join(buf)
    else:
        current.text = "".join(buf)
        sections.append(current)

    return preamble, sections


# --------------------------------------------------------------------------- #
# Validation — guarantees no section is silently dropped                       #
# --------------------------------------------------------------------------- #
def validate_routing(sections: list[Section]) -> tuple[list[str], list[str]]:
    """Return (warnings, drops). ``drops`` are fatal in --write mode."""
    warnings: list[str] = []
    drops: list[str] = []
    doc_keys = {s.key for s in sections}

    routed: set[str] = set(INLINE_SECTIONS)
    seen_create: dict[str, str] = {}

    for target in SPEC_PLAN:
        for key in target.sections:
            routed.add(key)
            if key not in doc_keys:
                warnings.append(f"configured §{key} ({target.file}) not found in CLAUDE.md")
            if target.mode == "create":
                if key in INLINE_SECTIONS:
                    warnings.append(f"§{key} is both inline and in create spec {target.file}")
                if key in seen_create:
                    warnings.append(
                        f"§{key} routed to two create specs: {seen_create[key]} and {target.file}"
                    )
                else:
                    seen_create[key] = target.file

    for key in INLINE_SECTIONS:
        if key not in doc_keys:
            warnings.append(f"inline §{key} not found in CLAUDE.md")

    for key in sorted(doc_keys, key=_sort_key):
        if key not in routed:
            drops.append(f"§{key} is not routed anywhere — it would be DROPPED")

    return warnings, drops


def _sort_key(key: str) -> tuple[int, str]:
    """Sort '45b' right after '45'."""
    match = re.match(r"(\d+)([a-z]?)", key)
    return (int(match.group(1)), match.group(2)) if match else (0, key)


# --------------------------------------------------------------------------- #
# Building output                                                              #
# --------------------------------------------------------------------------- #
def build_spec(target: SpecTarget, by_key: dict[str, Section], today: str) -> str:
    """Render a generated (``create``) spec file from its owned sections."""
    covers = ", ".join(f"§{k}" for k in target.sections)
    header = (
        f"# {target.title} Spec — AutoFounder AI\n\n"
        f"> Extracted from `CLAUDE.md` {covers} by `split_claude.py` ({today}).\n"
        f"> `CLAUDE.md` is the lean index; this file holds the detail.\n"
        f"> Section numbers (`§N`) are preserved so cross-references stay valid.\n\n"
        f"---\n\n"
    )
    body = "".join(by_key[k].text for k in target.sections if k in by_key)
    return header + body.lstrip("\n").rstrip() + "\n"


def build_lean_claude(preamble: str, by_key: dict[str, Section], today: str) -> str:
    """Render the new lean CLAUDE.md: preamble + inline sections + nav table."""
    note = (
        "> **This file is a lean index.** The detailed reference now lives in "
        "[`.claude/specs/`](specs/). Section numbers are non-contiguous below "
        "because the detail sections were extracted — use the spec map to find them.\n"
    )

    parts: list[str] = [preamble.rstrip("\n"), "", note]

    # Orientation sections first (1, 2).
    for key in ("1", "2"):
        if key in by_key and key in INLINE_SECTIONS:
            parts.append(by_key[key].text.rstrip("\n"))

    # Navigation table.
    nav = ["## Specification Map", "",
           "Detailed reference, extracted from this document. "
           "Open the relevant spec before working in that area.", "",
           "| Topic | Spec | Covers |", "|---|---|---|"]
    for target in SPEC_PLAN:
        covers = ", ".join(f"§{k}" for k in target.sections) if target.sections else "—"
        nav.append(f"| {target.desc} | [`specs/{target.file}`](specs/{target.file}) | {covers} |")
    nav.append("\n---")
    parts.append("\n".join(nav))

    # Remaining inline sections (40, 41, 42).
    for key in INLINE_SECTIONS:
        if key in ("1", "2"):
            continue
        if key in by_key:
            parts.append(by_key[key].text.rstrip("\n"))

    parts.append(
        f"*Lean index generated by `split_claude.py` on {today}. "
        f"Full prior version preserved at `CLAUDE.md.backup`.*\n"
    )
    return "\n\n".join(p for p in parts if p) + "\n"


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #
def next_backup_path(path: Path) -> Path:
    """``CLAUDE.md.backup``, or ``.backup.1``, ``.backup.2``... if taken."""
    candidate = Path(str(path) + ".backup")
    counter = 1
    while candidate.exists():
        candidate = Path(str(path) + f".backup.{counter}")
        counter += 1
    return candidate


def show(path: Path) -> str:
    """Display a path relative to the repo when possible."""
    try:
        return path.relative_to(BASE).as_posix()
    except ValueError:
        return str(path)


# --------------------------------------------------------------------------- #
# Entry point                                                                  #
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

    parser = argparse.ArgumentParser(
        description="Split AutoFounder AI CLAUDE.md into modular specs (safe, reversible)."
    )
    parser.add_argument("--write", action="store_true",
                        help="perform the split (default: dry-run, writes nothing)")
    parser.add_argument("--force", action="store_true",
                        help="overwrite existing GENERATED specs (never touches 'reuse' specs)")
    parser.add_argument("--claude", default=str(DEFAULT_CLAUDE), help="path to CLAUDE.md")
    parser.add_argument("--specs", default=str(DEFAULT_SPECS), help="path to specs dir")
    args = parser.parse_args(argv)

    dry_run = not args.write
    claude_md = Path(args.claude)
    specs_dir = Path(args.specs)

    if not claude_md.exists():
        print(f"[ERROR] CLAUDE.md not found at {show(claude_md)}", file=sys.stderr)
        return 1

    content = claude_md.read_text(encoding="utf-8")
    preamble, sections = parse_claude_md(content)
    by_key = {s.key: s for s in sections}
    today = datetime.now().strftime("%Y-%m-%d")

    mode = "DRY-RUN (no files written)" if dry_run else "WRITE"
    print(f"=== split_claude.py — {mode} ===")
    print(f"Source : {show(claude_md)}  ({len(sections)} sections, {len(content):,} chars)")
    print(f"Specs  : {show(specs_dir)}\n")

    # --- Safety: never drop content ---------------------------------------- #
    warnings, drops = validate_routing(sections)
    for warn in warnings:
        print(f"[WARN] {warn}")
    for drop in drops:
        print(f"[DROP] {drop}")
    if drops and not dry_run:
        print("\n[ERROR] Refusing to write: the section routing would drop content. "
              "Fix SPEC_PLAN/INLINE_SECTIONS so every section is routed.", file=sys.stderr)
        return 2
    if warnings or drops:
        print()

    # --- Plan per spec file ------------------------------------------------- #
    print(f"[KEEP] CLAUDE.md inline sections: {', '.join('§' + k for k in INLINE_SECTIONS)}\n")

    to_write: list[tuple[SpecTarget, Path]] = []
    for target in SPEC_PLAN:
        dest = specs_dir / target.file
        covers = ", ".join(f"§{k}" for k in target.sections) if target.sections else "—"
        if target.mode == "reuse":
            if dest.exists():
                print(f"[REUSE] {show(dest):<28} untouched (curated)        <- {covers}")
            else:
                print(f"[WARN ] {show(dest):<28} reuse spec MISSING         <- {covers}")
        else:  # create
            if dest.exists() and not args.force:
                print(f"[SKIP ] {show(dest):<28} exists (use --force)       <- {covers}")
            else:
                verb = "OVERWRITE" if dest.exists() else "NEW"
                print(f"[{verb:<5}] {show(dest):<28} generate                   <- {covers}")
                to_write.append((target, dest))

    # --- Size projection ---------------------------------------------------- #
    lean = build_lean_claude(preamble, by_key, today)
    reduction = 100 * (1 - len(lean) / len(content)) if content else 0
    print(f"\nCLAUDE.md size: {len(content):,} -> {len(lean):,} chars "
          f"({reduction:.0f}% smaller)")

    if dry_run:
        print("\n[DRY-RUN] Nothing written. Re-run with --write to apply.")
        return 0

    # --- Write -------------------------------------------------------------- #
    backup = next_backup_path(claude_md)
    shutil.copy2(claude_md, backup)
    print(f"\n[OK] backup -> {show(backup)}")

    specs_dir.mkdir(parents=True, exist_ok=True)
    for target, dest in to_write:
        dest.write_text(build_spec(target, by_key, today), encoding="utf-8")
        print(f"[OK] wrote  -> {show(dest)}")

    claude_md.write_text(lean, encoding="utf-8")
    print(f"[OK] rewrote -> {show(claude_md)} (lean index)")
    print(f"\nDone. {len(to_write)} spec(s) generated. Revert with: "
          f"copy \"{show(backup)}\" \"{show(claude_md)}\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
