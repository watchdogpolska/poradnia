const mysql = require("mysql2");
const { withPromiseLogging } = require("../testing/logging");

// Run an array of functions returning Promises sequentially.
// Function N+1 will be executed after function N resolves.
// Rejects on the first error encountered.
const sequencePromises = (promiseFns) =>
  promiseFns.reduce((left, right) => left.then(right), Promise.resolve());

// Execute a single query on a mysql connection.
// See https://github.com/mysqljs/mysql for details.
const query = withPromiseLogging("db:query")(
  (sqlQuery) =>
    new Promise((resolve, reject) => {
      const connection = mysql.createConnection({
        host: "db",
        user: "root",
        password: "password",
        database: "test_poradnia",
      });

      connection.connect((err) => {
        if (err) {
          reject(err);
        }
      });

      connection.query(sqlQuery, (err, results, fields) => {
        if (err) {
          reject(err);
        } else {
          resolve(results);
        }
      });

      connection.end();
    })
);

// Clear all rows in tables provided.
// The function is not aware of relations between tables.
// If TableA references TableB, TableA should appear before TableB in the argument.
const clearTables = (tables) => {
  // Create functions that will trigger queries, but do not execute them until scheduled.
  const lazyDeletes = tables.map((table) => (previousQueryResult) =>
    query(`delete from ${table}`)
  );

  // By convention, cypress plugins mustn't return `undefined`.
  // `null` is fine.
  return sequencePromises(lazyDeletes).then(() => null);
};

// Clears tables of content created during tests.
// List of tables manually curated.
// TODO: consider defining the dependency tree and clearing all tables.
const clear = () =>
  clearTables([
    "advicer_advice_area",
    "advicer_advice_issues",
    "advicer_advice",
    "teryt_tree_jednostkaadministracyjna",
    "teryt_tree_category",
    "django_admin_log",
    "records_record",
    "letters_attachment",
    "letters_letter",
    "events_event",
    "judgements_courtsession",
    "judgements_courtcase",
    "judgements_court",
    "cases_caseuserobjectpermission",
    "cases_case",
    "account_emailaddress",
    "users_user",
  ]);

module.exports = { query, clear };
