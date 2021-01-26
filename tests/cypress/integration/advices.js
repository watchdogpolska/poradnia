const { register, login, logout } = require("../testing/auth");
const {
  addSuperUserPrivileges,
  createCourt,
  createAdministrativeDivisionCategory,
  createAdministrativeDivisionUnit,
} = require("../testing/management");
const {
  submitAdviceForm,
  submitCaseForm,
  submitCourtCaseForm,
  submitLetterForm,
  submitEventForm,
} = require("../testing/forms");
const Case = require("../testing/case");
const Letter = require("../testing/letter");
const User = require("../testing/user");
const Advice = require("../testing/advice");

describe.only("advices", () => {
  beforeEach(() => {
    cy.task("db:clear");
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
    const administrativeDivisionUnits = [
      "adminDivisionA",
      "adminDivisionB",
      "adminDivisionC",
    ].map((name) => ({
      name,
      level: 3,
      category: administrativeDivisionCategory.id,
    }));

    const user = User.fromId("testUser");
    register(cy)(user);

    // Test specific db setup.
    addSuperUserPrivileges(cy)(user);
    createAdministrativeDivisionCategory(cy)(administrativeDivisionCategory);
    administrativeDivisionUnits.forEach((adminUnit) => {
      createAdministrativeDivisionUnit(cy)(adminUnit);
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
    const advices = {
      A: {
        case: cases[0],
        datetime,
        solved: 1,
        administrativeDivision: administrativeDivisionUnits[0].name,
        adviceAuthor: user,
        ...Advice.fromId("adviceA"),
      },

      B: {
        case: cases[1],
        datetime,
        solved: 1,
        administrativeDivision: administrativeDivisionUnits[1].name,
        adviceAuthor: user,
        ...Advice.fromId("adviceB"),
      },

      C: {
        case: cases[2],
        datetime,
        solved: 0,
        administrativeDivision: administrativeDivisionUnits[2].name,
        adviceAuthor: user,
        ...Advice.fromId("adviceC"),
      },
    };

    // For each advice, find its related case by title and fill an advice form.
    for (const advice of Object.values(advices)) {
      cy.contains("Wyszukaj").click();
      cy.get('input[type="search"]').clear().type(advice.case.title);
      cy.contains("a", advice.case.title).click();

      // Add an advice.
      cy.contains("Utwórz nową porade").click();
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
      const notExpectedAdvices = Object.values(advices).filter(
        (advice) => !expectedAdvices.includes(advice)
      );
      expectedAdvices.forEach((advice) => cy.contains(advice.subject));
      notExpectedAdvices.forEach((advice) =>
        cy.contains(advice.subject).should("not.exist")
      );
    };

    // Initially, all advices should be visible.
    validateContainsOnly([advices["A"], advices["B"], advices["C"]]);

    // Pressing the filter button with default values.
    cy.contains("Filtruj").click();
    validateContainsOnly([advices["A"], advices["B"], advices["C"]]);
  });
});
