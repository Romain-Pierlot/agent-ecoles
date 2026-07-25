import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
  // Garde-fou contre les couleurs hex codées en dur (cf.
  // docs/Design_system/REFERENCE.md, section 2) : une couleur hex en dur
  // dans un composant a causé plusieurs bugs invisibles à la relecture
  // pendant la refonte terracotta (ex. une ombre CSS qui gardait l'ancienne
  // couleur). Toujours passer par un token. Exceptions légitimes (registres
  // de dégradés type NOTATION_GRADIENTS) : désactiver ligne par ligne avec
  // un commentaire expliquant pourquoi.
  {
    files: ["src/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-syntax": [
        "error",
        {
          selector: "Literal[value=/#[0-9a-fA-F]{6}\\b/]",
          message:
            "Couleur hex en dur : utiliser un token (voir docs/Design_system/REFERENCE.md). Si c'est un registre de référence légitime, désactiver cette ligne avec une justification.",
        },
        {
          selector: "TemplateElement[value.raw=/#[0-9a-fA-F]{6}\\b/]",
          message:
            "Couleur hex en dur : utiliser un token (voir docs/Design_system/REFERENCE.md). Si c'est un registre de référence légitime, désactiver cette ligne avec une justification.",
        },
      ],
    },
  },
]);

export default eslintConfig;
