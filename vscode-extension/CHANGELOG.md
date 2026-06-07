# Changelog

All notable changes to the AutoFounder AI VS Code extension are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-06-07

Initial release — Phase 6 (AF-072 → AF-078).

### Added
- **AF-072** Activation core: command palette, activity-bar view, and Supabase
  Auth PKCE sign-in with the JWT stored in `SecretStorage` (plus a dev-token
  fallback). Typed, envelope-aware REST client.
- **AF-073** Runs sidebar tree view with status icons, pillar progress, and a live
  cost badge; status-bar cost ticker.
- **AF-074** HITL gate notifications with inline Approve / Reject.
- **AF-075** `Generate Component` / `Generate API Endpoint` commands that stream
  into a new editor tab.
- **AF-076** Live token-streaming webview panel (WebSocket with polling fallback).
- **AF-077** `Open Lean Canvas / ERD / OpenAPI Spec` artifact quick-open.
- **AF-078** `vsce` package/publish GitHub Actions workflow with automatic version
  bump on merge to `main`.
