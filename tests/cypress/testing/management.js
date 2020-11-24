const buildInsertQuery = (tableName, keyValuePairs) => {
  const columns = Object.keys(keyValuePairs);
  const values = Object.values(keyValuePairs);
  return `
    insert into ${tableName}
    (${columns.join(",")})
    values
    (${values.join(",")})`;
};

const withExtraQuotes = (str) => `"${str}"`;

const addSuperUserPrivileges = (cy) => (user) => {
  const { username } = user;
  cy.task(
    "db:query",
    `update users_user
     set is_staff=1, is_superuser=1
     where username="${username}"`
  );
};

const createCourt = (cy) => (court) => {
  // For now, use hardcoded constants for all other fields.
  // If need be, add them to the argument.
  const { id, name } = court;
  cy.task(
    "db:query",
    buildInsertQuery("judgements_court", {
      id,
      name: withExtraQuotes(name),
      created: withExtraQuotes("2010-01-01"),
      modified: withExtraQuotes("2010-01-01"),
      parser_key: withExtraQuotes("parser_key"),
      active: 1,
    })
  );
};

module.exports = { addSuperUserPrivileges, createCourt };
