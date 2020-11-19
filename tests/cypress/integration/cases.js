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

  it("user can open a case with an attachment, staff can access the attachment", () => {
    // Create user accounts.
    const userStaff = User.fromId("staff");
    const userRequester = User.fromId("requester");

    for (const user of [userRequester, userStaff]) {
      register(cy)(user);
      logout(cy)();
    }

    addSuperUserPrivileges(cy)(userStaff);

    login(cy)(userRequester);

    // Open a case with an attachment.
    cy.visit("/");
    cy.contains("Nowa sprawa").click();
    cy.contains("form", "Treść").within(($form) => {
      cy.get('input[name="name"]').clear().type(`case-title`);
      cy.get('textarea[name="text"]').clear().type(`case-content`);
      cy.get('input[type="file"]')
        .filter(":visible")
        .first()
        .attachFile("text_file.txt");
      cy.contains("input", "Zgłoś").click();
    });

    // Filename should be displayed on the attachments list.
    cy.contains("text_file.txt");

    logout(cy)();

    // View the case as staff.
    login(cy)(userStaff);
    cy.visit("/");
    cy.contains("Wykaz spraw").click();
    cy.contains("case-title").click();

    // Get the attachment link and try to open it.
    // Downloading the file must be done by a task, rather than by the browser, to avoid crossing the web app's boundary.
    // It's discouraged to do it in cypress.
    cy.contains("a", "text_file.txt")
      .invoke("attr", "href")
      .then((href) =>
        cy
          .task("fetch:get", Cypress.config("baseUrl") + href)
          .then((content) => {
            expect(content).to.contain("Text file content.");
          })
      );
  });
});
