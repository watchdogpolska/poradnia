const { register } = require("../testing/auth");
const {
  addSuperUserPrivileges,
  createAdministrativeDivisionCategory,
  createAdministrativeDivisionUnit,
} = require("../testing/management");
const {
  submitCaseForm,
  submitAdviceForm,
  submitEventForm,
} = require("../testing/forms");
const Case = require("../testing/case");
const User = require("../testing/user");
const Advice = require("../testing/advice");
const AdministrativeDivisionUnit = require("../testing/administrative-division-unit");

// Each of these tests seeds one row for a given ajax_datatable-backed table,
// then confirms the initial ajax load actually renders that row - as opposed
// to the existing per-app specs, which only assert that the ajax endpoint is
// called on load/filter-change, without checking what ends up on screen.
describe("datatables", () => {
  beforeEach(() => {
    cy.task("db:clear");
    cy.viewport(1920, 1080);
  });

  it("renders a seeded row in the cases DataTable at /sprawy/table/", () => {
    const user = User.fromId("testUser");
    register(cy)(user);
    addSuperUserPrivileges(cy)(user);

    const case_ = Case.fromId("caseA");
    cy.contains("Nowa sprawa").click();
    cy.contains("form", "Treść").within(($form) => {
      submitCaseForm(cy)($form, case_);
    });

    cy.closeDonatePopup();
    cy.intercept({ pathname: "/sprawy/case_table_ajax_data/" }).as("dtAjax");
    cy.visit("/sprawy/table/");
    cy.wait("@dtAjax");

    cy.get("#datatable_cases tbody tr").should("have.length.greaterThan", 0);
    cy.get("#datatable_cases").contains(case_.title);
  });

  it("renders a seeded row in the letters DataTable at /listy/table/", () => {
    const user = User.fromId("testUser");
    register(cy)(user);
    addSuperUserPrivileges(cy)(user);

    // Creating a case creates its initial Letter (NewCaseCreateView's model
    // is Letter), so this alone is enough to seed the letters table too.
    const case_ = Case.fromId("caseA");
    cy.contains("Nowa sprawa").click();
    cy.contains("form", "Treść").within(($form) => {
      submitCaseForm(cy)($form, case_);
    });

    cy.closeDonatePopup();
    cy.intercept({ pathname: "/listy/letters_table_ajax_data/" }).as(
      "dtAjax"
    );
    cy.visit("/listy/table/");
    cy.wait("@dtAjax");

    cy.get("#datatable_letters tbody tr").should("have.length.greaterThan", 0);
    cy.get("#datatable_letters").contains(case_.title);
  });

  it("renders a seeded row in the advices DataTable at /porady/table/", () => {
    const user = User.fromId("testUser");
    register(cy)(user);
    addSuperUserPrivileges(cy)(user);

    const administrativeDivisionCategory = {
      id: 1,
      name: "admin-category",
      level: 3,
    };
    const [
      administrativeDivisionUnit,
    ] = AdministrativeDivisionUnit.batchFromIds(
      ["admin-division"],
      administrativeDivisionCategory
    );
    createAdministrativeDivisionCategory(cy)(administrativeDivisionCategory);
    createAdministrativeDivisionUnit(cy)(administrativeDivisionUnit);

    const case_ = Case.fromId("caseA");
    cy.contains("Nowa sprawa").click();
    cy.contains("form", "Treść").within(($form) => {
      submitCaseForm(cy)($form, case_);
    });

    const advice = {
      datetime: { year: 2020, month: "January", day: 1, hour: 12, minute: 30 },
      solved: 1,
      administrativeDivision: administrativeDivisionUnit.name,
      adviceAuthor: user,
      ...Advice.fromId("adviceA"),
    };
    cy.contains(".panel", "Dane statystyczne").contains("Otaguj sprawę").click();
    cy.contains("form", "Dane statystyczne").within(($form) => {
      submitAdviceForm(cy)($form, advice);
    });

    cy.closeDonatePopup();
    cy.intercept({ pathname: "/porady/advice_table_ajax_data/" }).as(
      "dtAjax"
    );
    cy.visit("/porady/table/");
    cy.wait("@dtAjax");

    cy.get("#datatable_advices tbody tr").should("have.length.greaterThan", 0);
    cy.get("#datatable_advices").contains(advice.subject);
  });

  it("renders a seeded row in the events DataTable at /wydarzenia/table/", () => {
    const user = User.fromId("testUser");
    register(cy)(user);
    addSuperUserPrivileges(cy)(user);

    const case_ = Case.fromId("caseA");
    cy.contains("Nowa sprawa").click();
    cy.contains("form", "Treść").within(($form) => {
      submitCaseForm(cy)($form, case_);
    });

    const event = {
      text: "event-text",
      datetime: { year: 2020, month: "January", day: 1, hour: 12, minute: 30 },
    };
    cy.contains("Wydarzenie").click();
    cy.contains("form", "Czas").within(($form) => {
      submitEventForm(cy)($form, event);
    });

    cy.closeDonatePopup();
    cy.intercept({ pathname: "/wydarzenia/events_table_ajax_data/" }).as(
      "dtAjax"
    );
    cy.visit("/wydarzenia/table/");
    cy.wait("@dtAjax");

    cy.get("#datatable_events tbody tr").should("have.length.greaterThan", 0);
    cy.get("#datatable_events").contains(event.text);
  });

  it("renders a seeded row in the users DataTable at /uzytkownik/table/", () => {
    const user = User.fromId("testUser");
    register(cy)(user);
    addSuperUserPrivileges(cy)(user);

    cy.closeDonatePopup();
    cy.intercept({ pathname: "/uzytkownik/users_table_ajax_data/" }).as(
      "dtAjax"
    );
    cy.visit("/uzytkownik/table/");
    cy.wait("@dtAjax");

    cy.get("#datatable_users tbody tr").should("have.length.greaterThan", 0);
    cy.get("#datatable_users").contains(user.username);
  });
});
