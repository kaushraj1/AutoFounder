// Extends the shared root flat config and adds Node globals for the `.mjs` build
// script (the root config only wires the TS-aware rules, which switch `no-undef`
// off for `.ts`; plain `.mjs` files need the Node globals declared explicitly).

import root from "../eslint.config.mjs";

export default [
  ...root,
  {
    files: ["**/*.mjs"],
    languageOptions: {
      globals: {
        process: "readonly",
        console: "readonly",
        URL: "readonly",
        Buffer: "readonly",
      },
    },
  },
];
