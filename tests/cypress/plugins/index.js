const db = require("./db");
const fetch = require("./fetch");

module.exports = (on, config) => {
  // Register tasks.
  // NOTE: each task takes a single, JSON-serializable object as an argument.
  // Functions are not allowed.
  on("task", {
    "db:query": db.query,
    "db:clear": db.clear,
    "fetch:get": fetch.get,
  });
};
