const db = require("./db");

module.exports = (on, config) => {
  // Register tasks.
  // NOTE: each task takes a single, JSON-serializable object as an argument.
  // Functions are not allowed.
  on("task", {
    "db:query": db.query,
    "db:clearTables": db.clearTables,
  });
};
