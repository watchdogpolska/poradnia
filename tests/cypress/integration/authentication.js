describe("authentication", () => {
  beforeEach(() => {
    cy.task("db:clearTables", ["account_emailaddress", "users_user"]);
  });

  it("user should be able to register and log in", () => {
    //
    // Register and log out.
    //

    // Home.
    cy.visit("/");
    cy.contains("Zarejestuj").click();

    // Register.
    cy.get('input[name="first_name"]').type("FirstName");
    cy.get('input[name="last_name"]').type("LastName");
    cy.get('input[name="username"]').type("Username");
    cy.get('input[name="email"]').type("email@example.com");
    cy.get('input[name="password1"]').type("password");
    cy.get('input[name="password2"]').type("password");
    cy.get('input[name="giodo"]').click();
    cy.get('input[name="signup"]').click();

    // Home.
    cy.contains("FirstName");
    cy.contains("Wyloguj").click();

    // Logout.
    cy.contains("button", "Wyloguj").click();

    //
    // Log in again.
    //

    // Home.
    cy.visit("/");
    cy.contains("Zaloguj").click();

    // Login.
    cy.get('input[name="login"]').type("email@example.com");
    cy.get('input[name="password"]').type("password");
    cy.contains("input", "Zaloguj").click();

    // Home.
    cy.contains("FirstName");
  });
});
