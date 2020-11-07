const { register, login, logout } = require("../testing/auth");
const User = require("../testing/user");

describe("authentication", () => {
  beforeEach(() => {
    cy.task("db:clearTables", ["account_emailaddress", "users_user"]);
  });

  it("user should be able to register and log in", () => {
    const user = User.fromId("user");
    cy.visit("/");

    // Register the user.
    register(cy)(user);

    // Validate that the user's logged in.
    cy.visit("/");
    cy.contains(user.firstName);

    logout(cy)();

    // Log in again.
    login(cy)(user);

    // Validate that the user's logged in.
    cy.visit("/");
    cy.contains(user.firstName);
  });
});
