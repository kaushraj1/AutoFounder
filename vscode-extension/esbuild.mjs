// Build script for the AutoFounder AI VS Code extension.
//
//   node esbuild.mjs                 -> dev bundle (dist/extension.js, sourcemaps)
//   node esbuild.mjs --production    -> minified bundle for packaging
//   node esbuild.mjs --watch         -> incremental rebuild on change (F5 debugging)
//   node esbuild.mjs --tests         -> bundle the unit tests to dist/test/all.test.js
//
// The `vscode` module is provided by the extension host at runtime and must never
// be bundled. `ws` ships two optional native add-ons (bufferutil / utf-8-validate)
// that are not required for correctness — mark them external to keep the bundle clean.

import esbuild from "esbuild";
import { readdirSync } from "node:fs";

const watch = process.argv.includes("--watch");
const tests = process.argv.includes("--tests");
const production = process.argv.includes("--production");

/** @type {import('esbuild').BuildOptions} */
const base = {
  bundle: true,
  format: "cjs",
  platform: "node",
  target: "node18",
  external: ["vscode", "bufferutil", "utf-8-validate"],
  logLevel: "info",
};

async function buildExtension() {
  const options = {
    ...base,
    entryPoints: ["src/extension.ts"],
    outfile: "dist/extension.js",
    sourcemap: !production,
    minify: production,
  };

  if (watch) {
    const ctx = await esbuild.context(options);
    await ctx.watch();
    console.log("[esbuild] watching for changes…");
    return;
  }

  await esbuild.build(options);
}

async function buildTests() {
  const dir = "src/test/unit";
  const files = readdirSync(dir).filter((f) => f.endsWith(".test.ts"));

  // Bundle every test file into ONE explicit output. `node --test <single-file>`
  // is supported on Node 18+, unlike directory/glob args (Node 21+), so this runs
  // identically in CI (Node 20) and locally — no shell- or Node-version-specific
  // glob expansion.
  await esbuild.build({
    ...base,
    stdin: {
      contents: files.map((f) => `import "./${f}";`).join("\n"),
      resolveDir: dir,
      sourcefile: "all.test.ts",
      loader: "ts",
    },
    outfile: "dist/test/all.test.js",
    sourcemap: true,
  });
}

try {
  await (tests ? buildTests() : buildExtension());
} catch (err) {
  console.error(err);
  process.exit(1);
}
