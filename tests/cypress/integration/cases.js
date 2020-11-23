const { register, login, logout } = require("../testing/auth");
const { addSuperUserPrivileges } = require("../testing/management");
const {
  submitCaseForm,
  submitLetterForm,
  submitEventForm,
} = require("../testing/forms");
const Case = require("../testing/case");
const Letter = require("../testing/letter");
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
    const case_ = { attachment: "text_file1.txt", ...Case.fromId("case") };
    const letter = { attachment: "text_file2.txt", ...Letter.fromId("letter") };
    const event = {
      text: "event-text",
      datetime: { year: 2020, month: "January", day: 1, hour: 12, minute: 30 },
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

    // Add an event.
    cy.contains("Wydarzenie").click();
    cy.contains("form", "Czas").within(($form) => {
      submitEventForm(cy)($form, event);
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

  it("staff can search for a case", () => {
    const user = User.fromId("testUser");
    register(cy)(user);
    addSuperUserPrivileges(cy)(user);

    // Create a few cases.
    const cases = ["caseA", "caseB", "caseC"].map(Case.fromId);
    const caseA = cases[0];

    for (const case_ of cases) {
      cy.contains("Nowa sprawa").click();

      // Fill the case form.
      cy.contains("form", "Treść").within(($form) => {
        submitCaseForm(cy)($form, case_);
      });
    }

    // Find a case by title, using the simple search form.
    cy.contains("Wyszukaj").click();
    cy.get('input[type="search"]').clear().type("caseA");
    cy.contains("a", caseA.title).click();
    cy.contains(caseA.content);

    // Find a case by title, using the rich form.
    // Filter both by case title and client username.
    cy.contains("Wykaz spraw").click();
    // There's two sections with the text "Przedmiot".
    // Select the one with an input field.
    cy.contains("div", "Przedmiot")
      .filter(":has(input)")
      .within(($div) => {
        cy.get('input[type="text"]').clear().type("caseA");
      });
    cy.contains("div", "Klient").within(($div) => {
      // This block uses an autocomplete widget.
      cy.get(".selection").click();
      // After clicking, the input field should be focused.
      // Type the user's last name.
      // There should be a suggestion with the user's full name. Pressing Enter should select it.
      // NOTE: it may be tempting to make the test case click on a suggestion, instead of using Enter, but the widget
      // attaches the element outside of the selected div. It is possible to do it the other way around, but this
      // solution is simpler.
      cy.focused().type(user.lastName).type("{enter}");
    });

    cy.contains("Filtruj").click();
    cy.contains(caseA.title).click();
    cy.contains(caseA.content);
  });
});
