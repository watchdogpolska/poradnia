const { register, login, logout } = require("../testing/auth");
const User = require("../testing/user");

describe("authentication", () => {
  beforeEach(() => {
    cy.task("db:clear");
    cy.viewport(1920,1080);
  });

  it("user should be able to register and log in", () => {
    const user = User.fromId("user");
    cy.visit("/");
    cy.closeDonatePopup(); // Ensure no popup is blocking

    // Register the user.
    register(cy)(user);

    // Validate that the user's logged in.
    cy.visit("/");
    cy.closeDonatePopup(); // Ensure no popup is blocking
    cy.contains(user.firstName);

    logout(cy)();

    // Log in again.
    login(cy)(user);

    // Validate that the user's logged in.
    cy.visit("/");
    cy.closeDonatePopup(); // Ensure no popup is blocking
    cy.contains(user.firstName);
  });
});
