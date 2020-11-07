const mysql = require("mysql");

// Run an array of functions returning Promises sequentially.
// Function N+1 will be executed after function N resolves.
// Rejects on the first error encountered.
const sequencePromises = (promiseFns) =>
  promiseFns.reduce((left, right) => left.then(right), Promise.resolve());

// Execute a single query on a mysql connection.
// See https://github.com/mysqljs/mysql for details.
const query = (sqlQuery) =>
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
  });

// Clear all rows in tables provided.
// The function is not aware of relations between tables.
// If TableA references TableB, TableA should appear before TableB in the argument.
const clearTables = (tables) =>
  sequencePromises(tables.map((table) => query(`delete from ${table}`))).then(
    () => null
  );

module.exports = { query, clearTables };
