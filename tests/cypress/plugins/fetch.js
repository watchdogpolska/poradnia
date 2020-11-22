const fetch = require("node-fetch");

const get = (url) => fetch(url).then((res) => res.text());
module.exports = { get };
