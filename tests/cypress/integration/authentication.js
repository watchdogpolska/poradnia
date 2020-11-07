const { register, login, logout } = require("../testing/auth");

describe("authentication", () => {
  beforeEach(() => {
    cy.task("db:clearTables", ["account_emailaddress", "users_user"]);
  });

  it("user should be able to register and log in", () => {
    cy.visit("/");

    // Register the user.
    register(cy)(
      "FirstName",
      "LastName",
      "Username",
      "email@example.com",
      "password"
    );

    // Validate that the user's logged in.
    cy.visit("/");
    cy.contains("FirstName");

    logout(cy)();

    // Log in again.
    login(cy)("email@example.com", "password");

    // Validate that the user's logged in.
    cy.visit("/");
    cy.contains("FirstName");
  });
});
