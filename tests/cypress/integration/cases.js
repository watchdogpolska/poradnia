const { register, login, logout } = require("../testing/auth");
const { addSuperUserPrivileges } = require("../testing/management");
const { submitCaseForm, submitLetterForm } = require("../testing/forms");
const User = require("../testing/user");

describe("cases", () => {
  beforeEach(() => {
    cy.task("db:clear");
  });

  it("user can open a new case, staff can act on it", () => {
    // Create user accounts.
    const userRequester = User.fromId("requester");
    const userStaff = User.fromId("staff");
    // `case` is a reserved keyword.
    const case_ = {
      title: "case-title",
      content: "case-content",
      attachment: "text_file1.txt",
    };
    const letter = {
      title: "letter-title",
      content: "letter-content",
      attachment: "text_file2.txt",
    };

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
      submitCaseForm(cy)($form, case_);
    });

    // Filename should be displayed on the attachments list.
    cy.contains("text_file1.txt");

    // Validate that the case has been registered and is visible.
    cy.contains("Wykaz spraw").click();
    cy.contains(case_.title);

    logout(cy)();

    // Handle the case as staff.
    login(cy)(userStaff);
    cy.visit("/");
    cy.contains("Wykaz spraw").click();
    cy.contains(case_.title).click();

    // Get the attachment link and try to open it.
    // Downloading the file must be done by a task, rather than by the browser, to avoid crossing the web app's boundary.
    // It's discouraged to do it in cypress.
    cy.contains("a", case_.attachment)
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
      submitLetterForm(cy)($form, letter);
    });

    logout(cy)();

    // Log as the requester again. Check if the letter is accessible.
    login(cy)(userRequester);
    cy.visit("/");

    cy.contains("Wykaz spraw").click();
    cy.contains(case_.title).click();
    cy.contains(letter.content);

    // Fetch the attachment.
    cy.contains("a", letter.attachment)
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
