const { register, login, logout } = require("../testing/auth");
const { addSuperUserPrivileges } = require("../testing/management");
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
    addSuperUserPrivileges(cy)(userStaff);

    // Open a case as a non-staff user.
    login(cy)(userRequester);

    cy.visit("/");
    cy.contains("Nowa sprawa").click();

    // Fill the case form.
    cy.contains("form", "Treść").within(($form) => {
      cy.get('input[name="name"]').clear().type(`case-title`);
      cy.get('textarea[name="text"]').clear().type(`case-content`);
      cy.get('input[type="file"]')
        .filter(":visible")
        .first()
        .attachFile("text_file1.txt");
      cy.contains("input", "Zgłoś").click();
    });

    // Filename should be displayed on the attachments list.
    cy.contains("text_file1.txt");

    // Validate that the case has been registered and is visible.
    cy.contains("Wykaz spraw").click();
    cy.contains("case-title");

    logout(cy)();

    // Handle the case as staff.
    login(cy)(userStaff);
    cy.visit("/");
    cy.contains("Wykaz spraw").click();
    cy.contains("case-title").click();

    // Get the attachment link and try to open it.
    // Downloading the file must be done by a task, rather than by the browser, to avoid crossing the web app's boundary.
    // It's discouraged to do it in cypress.
    cy.contains("a", "text_file1.txt")
      .invoke("attr", "href")
      .then((href) =>
        cy
          .task("fetch:get", Cypress.config("baseUrl") + href)
          .then((content) => {
            expect(content).to.contain("text_file1.txt content");
          })
      );

    // Respond with a letter.
    cy.contains("form", "Przedmiot").within(($form) => {
      cy.get('input[name="name"]').clear().type(`letter-title`);
      cy.get('textarea[name="text"]').clear().type(`letter-content`);
      cy.get('input[type="file"]')
        .filter(":visible")
        .first()
        .attachFile("text_file2.txt");
      cy.contains("input", "Odpowiedz wszystkim").click();
    });

    logout(cy)();

    // Log as the requester again. Check if the letter is accessible.
    login(cy)(userRequester);
    cy.visit("/");

    cy.contains("Wykaz spraw").click();
    cy.contains("case-title").click();

    // Fetch the attachment.
    cy.contains("letter-content");
    cy.contains("a", "text_file2.txt")
      .invoke("attr", "href")
      .then((href) =>
        cy
          .task("fetch:get", Cypress.config("baseUrl") + href)
          .then((content) => {
            expect(content).to.contain("text_file2.txt content");
          })
      );
  });
});
