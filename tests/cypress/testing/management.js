const addSuperUserPrivileges = (cy) => (user) => {
  const { username } = user;
  cy.task(
    "db:query",
    `update users_user
      set is_staff=1, is_superuser=1
      where username="${username}"`
  );
};

module.exports = { addSuperUserPrivileges };
