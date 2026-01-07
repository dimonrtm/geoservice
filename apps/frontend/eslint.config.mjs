import js from "@eslint/js";
import globals from "globals";
import vue from "eslint-plugin-vue";
import tseslint from "typescript-eslint";
import eslintConfigPrettier from "eslint-config-prettier/flat";

export default tseslint.config(
  // что игнорируем
  { ignores: ["node_modules/**", "dist/**", "coverage/**"] },

  // базовые рекомендации ESLint
  js.configs.recommended,

  // рекомендации typescript-eslint (flat)
  ...tseslint.configs.recommended,

  // рекомендации для Vue (flat) — ВАЖНО: это массив, нужен spread
  ...vue.configs["flat/recommended"],

  // наши настройки под проект
  {
    files: ["**/*.{js,mjs,cjs,ts,tsx,vue}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: globals.browser,
      parserOptions: {
        // Vue парсится vue-eslint-parser внутри eslint-plugin-vue,
        // а TS внутри <script> — этим парсером:
        parser: tseslint.parser,
      },
    },
    rules: {
      // пример: можно ужесточить некоторые вещи
      "vue/no-unused-vars": "error",
      "no-console": "off",
    },
  },

  // ВАЖНО: prettier-конфиг ставим ПОСЛЕДНИМ, чтобы выключить конфликтующие правила
  eslintConfigPrettier
);
