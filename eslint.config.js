const { FlatCompat } = require('@eslint/eslintrc');

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

module.exports = [
  ...compat.extends('next/core-web-vitals'),
  {
    ignores: ['node_modules/**', '.next/**', 'api/__pycache__/**'],
  },
];

