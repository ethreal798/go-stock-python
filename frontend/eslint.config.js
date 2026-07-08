/**
 * ESLint 配置文件
 * 
 * 基于 ESLint 9.x 扁平配置系统（Flat Config）
 * 
 * @see https://eslint.org/docs/latest/use/configure/configuration-files-new
 * @see https://typescript-eslint.io/getting-started
 */

import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";

export default [
  // 构建产物和依赖目录不进行代码检查
  {
    ignores: ["dist", "node_modules"],
  },

  // TypeScript 和 React 代码检查
  {
    files: ["**/*.{ts,tsx}"],

    extends: [
      js.configs.recommended,
      ...tseslint.configs.recommended,
      reactHooks.configs["recommended-latest"],
    ],

    languageOptions: {
      ecmaVersion: 2020,
      globals: {
        ...globals.browser,
        ...globals.node,
      },
      parserOptions: {
        project: ["./tsconfig.app.json", "./tsconfig.node.json"],
        tsconfigRootDir: import.meta.dirname,
      },
    },

    plugins: {
      "react-refresh": reactRefresh,
    },

    rules: {
      // React 热更新规则
      "react-refresh/only-export-components": [
        "warn",
        { allowConstantExport: true },
      ],

      // TypeScript 规则
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-unused-vars": [
        "warn",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
        },
      ],

      // 代码风格规则
      "prefer-const": "warn",
      "no-var": "error",
      "prefer-template": "warn",
      "prefer-arrow-callback": "warn",
    },
  },
];