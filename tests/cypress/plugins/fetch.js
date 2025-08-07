// tests/cypress/plugins/fetch.js
const get = async (url) => {
  const res = await fetch(url);
  return res.text();
};
module.exports = { get };
