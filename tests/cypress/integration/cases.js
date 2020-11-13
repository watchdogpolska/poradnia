const { register, login, logout } = require("../testing/auth");
const User = require("../testing/user");

describe("cases", () => {
  beforeEach(() => {
    cy.task("db:clear");
  });

  it("user can open a new case, staff can act on it", () => {
    // Create user accounts.
    const userRequester = User.fromId("requester");
    const userStaff = User.fromId("staff");

    for (const user of [userRequester, userStaff]) {
      register(cy)(user);
      logout(cy)();
    }

    // Adding staff privileges has to be done manually.
    cy.task(
      "db:query",
      `update users_user
      set is_staff=1, is_superuser=1
      where username="${userStaff.username}"`
    );

    // Open a case as a non-staff user.
    login(cy)(userRequester);

    cy.visit("/");
    cy.contains("Nowa sprawa").click();

    // Fill the case form.
    cy.contains("form", "Treść").within(($form) => {
      cy.get('input[name="name"]').clear().type(`case-title`);
      cy.get('textarea[name="text"]').clear().type(`case-content`);
      cy.contains("input", "Zgłoś").click();
    });

    // Validate that the case has been registered and is visible.
    cy.contains("Wykaz spraw").click();
    cy.contains("case-title");

    logout(cy)();

    // Handle the case as staff.
    login(cy)(userStaff);
    cy.visit("/");
    cy.contains("Wykaz spraw").click();
    cy.contains("case-title").click();

    // Respond with a letter.
    cy.contains("form", "Przedmiot").within(($form) => {
      cy.get('input[name="name"]').clear().type(`letter-title`);
      cy.get('textarea[name="text"]').clear().type(`letter-content`);
      cy.contains("input", "Odpowiedz wszystkim").click();
    });

    logout(cy)();

    // Log as the requester again. Check if the letter is accessible.
    login(cy)(userRequester);
    cy.visit("/");

    cy.contains("Wykaz spraw").click();
    cy.contains("case-title").click();

    cy.contains("letter-content");
  });
});
