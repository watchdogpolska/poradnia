const { register, login, logout } = require("../testing/auth");
const {
  addSuperUserPrivileges,
  createCourt,
  createAdministrativeDivisionCategory,
  createAdministrativeDivisionUnit,
  createAdviceArea,
  createAdviceIssue,
} = require("../testing/management");
const {
  submitAdviceForm,
  submitAdviceFilterForm,
  submitCaseForm,
  submitCourtCaseForm,
  submitLetterForm,
  submitEventForm,
} = require("../testing/forms");
const Case = require("../testing/case");
const Letter = require("../testing/letter");
const User = require("../testing/user");
const Advice = require("../testing/advice");
const AdministrativeDivisionUnit = require("../testing/administrative-division-unit");

describe.only("advices", () => {
  beforeEach(() => {
    cy.task("db:clear");
    cy.viewport(1920,1080);
  });

  it("staff can search for an advice", () => {
    const datetime = {
      year: 2020,
      month: "January",
      day: 1,
      hour: 12,
      minute: 30,
    };

    // Teryt.
    const administrativeDivisionCategory = {
      id: 1,
      name: "admin-category",
      level: 3,
    };
    const administrativeDivisionUnits = AdministrativeDivisionUnit.batchFromIds(
      ["adminDivisionA", "adminDivisionB", "adminDivisionC"],
      administrativeDivisionCategory
    );

    // Advice metadata.
    const adviceAreas = [
      "adviceAreaA",
      "adviceAreaB",
      "adviceAreaC",
    ].map((name) => ({ name }));
    const adviceIssues = [
      "adviceIssueA",
      "adviceIssueB",
      "adviceIssueC",
    ].map((name) => ({ name }));

    const user = User.fromId("testUser");
    register(cy)(user);

    // Test specific db setup.
    addSuperUserPrivileges(cy)(user);
    createAdministrativeDivisionCategory(cy)(administrativeDivisionCategory);
    administrativeDivisionUnits.forEach((adminUnit) => {
      createAdministrativeDivisionUnit(cy)(adminUnit);
    });
    adviceAreas.forEach((adviceArea) => {
      createAdviceArea(cy)(adviceArea);
    });
    adviceIssues.forEach((adviceIssue) => {
      createAdviceIssue(cy)(adviceIssue);
    });

    // Create a few cases.
    const cases = ["caseA", "caseB", "caseC"].map(Case.fromId);

    for (const case_ of cases) {
      cy.contains("Nowa sprawa").click();

      // Fill the case form.
      cy.contains("form", "Treść").within(($form) => {
        submitCaseForm(cy)($form, case_);
      });
    }

    // Create a few advices.
    const advices = [
      {
        case: cases[0],
        datetime,
        solved: 1,
        administrativeDivision: administrativeDivisionUnits[0].name,
        adviceArea: adviceAreas[0],
        adviceIssue: adviceIssues[0],
        adviceAuthor: user,
        ...Advice.fromId("adviceA"),
      },

      {
        case: cases[1],
        datetime,
        solved: 1,
        administrativeDivision: administrativeDivisionUnits[1].name,
        adviceArea: adviceAreas[1],
        adviceIssue: adviceIssues[1],
        adviceAuthor: user,
        ...Advice.fromId("adviceB"),
      },

      {
        case: cases[2],
        datetime,
        solved: 0,
        administrativeDivision: administrativeDivisionUnits[2].name,
        adviceArea: adviceAreas[2],
        adviceIssue: adviceIssues[2],
        adviceAuthor: user,
        ...Advice.fromId("adviceC"),
      },
    ];

    // For each advice, find its related case by title and fill an advice form.
    for (const advice of advices) {
      cy.contains("Wyszukaj").click();
      cy.get('input[type="search"]').clear().type(advice.case.title);
      cy.contains("a", advice.case.title).click();

      // Add an advice.
      cy.contains("Otaguj sprawę").click();
      cy.contains("form", "Dane statystyczne").within(($form) => {
        submitAdviceForm(cy)($form, advice);
      });
    }

    // Search for advices using the rich form with filters.
    cy.contains("Rejestr porad").click();

    // This function is expected to be executed on the advice form.
    // For each expected advice, validate that its subject is visible.
    // For all remaining advices - validate that its subject is not visible.
    const validateContainsOnly = (expectedAdvices) => {
      const notExpectedAdvices = advices.filter(
        (advice) => !expectedAdvices.includes(advice)
      );
      expectedAdvices.forEach((advice) => cy.contains(advice.subject));
      notExpectedAdvices.forEach((advice) =>
        cy.contains(advice.subject).should("not.exist")
      );
    };

    // Initially, all advices should be visible.
    validateContainsOnly(advices);

    // Filter with default values.
    // This step tests the form filling function, to some extent.
    cy.get("form")
      .filter(':has(input[value="Zastosuj filtr"])')
      .within(($form) => {
        submitAdviceFilterForm(cy)($form, {});
      });
    validateContainsOnly(advices);

    // Filtering by whether a case has been marked as solved.
    // The simplest filter there is.
    cy.get("form")
      .filter(':has(input[value="Zastosuj filtr"])')
      .within(($form) => {
        submitAdviceFilterForm(cy)($form, { solved: true });
      });
    validateContainsOnly([advices[0], advices[1]]);

    // Disable the previous filter and set new fields.
    // Test a combination of multiple filters.
    cy.get("form")
      .filter(':has(input[value="Zastosuj filtr"])')
      .within(($form) => {
        submitAdviceFilterForm(cy)($form, {
          administrativeDivisions: [
            administrativeDivisionUnits[0],
            administrativeDivisionUnits[1],
          ],
          subject: "advice", // Non null, but matches all advices.
        });
      });
    validateContainsOnly([advices[0], advices[1]]);

    // Another combination - multiselect by adviceArea and adviceIssue.
    cy.get("form")
      .filter(':has(input[value="Zastosuj filtr"])')
      .within(($form) => {
        submitAdviceFilterForm(cy)($form, {
          adviceAreas: [adviceAreas[0], adviceAreas[1]],
          adviceIssues: [adviceIssues[1], adviceIssues[2]],
        });
      });
    validateContainsOnly([advices[1]]);
  });
});
