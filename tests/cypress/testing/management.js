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

const createAdministrativeDivisionCategory = (cy) => (category) => {
  const { id, name, level } = category;
  cy.task(
    "db:query",
    buildInsertQuery("teryt_tree_category", {
      id,
      name: withExtraQuotes(name),
      slug: withExtraQuotes(name),
      level,
    })
  );
};

// We're manually setting fields that are usually handled by django-mptt.
// This function should be kept as simple as possible, as long as it serves
// its purpose.
// For a flat tree, `lft` and `rght` should not overlap. Please use the helper
// function in `administrativeDivistionUnit` to create a batch of values.
const createAdministrativeDivisionUnit = (cy) => (unit) => {
  const { name, level, category, lft, rght } = unit;
  cy.task(
    "db:query",
    buildInsertQuery("teryt_tree_jednostkaadministracyjna", {
      // Id has a length limit.
      // If substrings are not unique, DB will reject a transaction.
      id: withExtraQuotes(name.slice(-7)),
      name: withExtraQuotes(name),
      slug: withExtraQuotes(name),
      level,
      category_id: category,
      updated_on: withExtraQuotes("2010-01-01"),
      active: 1,
      lft,
      rght,
      tree_id: 0,
    })
  );
};

module.exports = {
  addSuperUserPrivileges,
  createCourt,
  createAdministrativeDivisionCategory,
  createAdministrativeDivisionUnit,
};
