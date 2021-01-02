module.exports = {
  env: {
    browser: true,
    es2021: true
  },
  plugins: [],
  extends: [
    'semistandard'
  ],
  parserOptions: {
    ecmaVersion: 12,
    sourceType: 'module'
  },
  rules: {
    camelcase: 'off'
  }
};
