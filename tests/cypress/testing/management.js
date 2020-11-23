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
    `insert into judgements_court
    (id, name, created, modified, parser_key, active)
    values
    (${id}, "${name}", "2010-01-01", "2010-01-01", "parser_key", 1)`
  );
};

module.exports = { addSuperUserPrivileges, createCourt };
