const { register, login } = require("../testing/auth");
const { addSuperUserPrivileges } = require("../testing/management");
const User = require("../testing/user");

// Regression coverage for https://github.com/watchdogpolska/poradnia/issues/2200
// Typing into the `Czas od` / `Czas do` datepickers used to trigger an HTTP 500
// from `EventAjaxDatatableView` because `get_latest_by` returned a column name
// that wasn't declared in `column_defs`.
describe("events table", () => {
  beforeEach(() => {
    cy.task("db:clear");
    cy.viewport(1920, 1080);
  });

  it("date range filter does not 500 the AJAX endpoint (regression #2200)", () => {
    const userStaff = User.fromId("staff");
    register(cy)(userStaff);
    addSuperUserPrivileges(cy)(userStaff);
    // Re-login so the session picks up the freshly granted superuser flags.
    login(cy)(userStaff);

    cy.intercept("POST", "/wydarzenia/events_table_ajax_data/").as("eventsAjax");

    cy.visit("/wydarzenia/table/");

    // The page-load draw must succeed.
    cy.wait("@eventsAjax").its("response.statusCode").should("eq", 200);

    // Typing into `Czas od` triggers a redraw with `date_from` in the payload.
    cy.get("input.date_from").type("2020-01-01").trigger("change");

    cy.wait("@eventsAjax").then((interception) => {
      expect(interception.response.statusCode, "AJAX must not 500").to.eq(200);
      expect(interception.request.body).to.contain("date_from=2020-01-01");
      // Response must be a valid DataTables payload, not an HTML 500 page.
      expect(interception.response.body).to.have.property("recordsTotal");
      expect(interception.response.body).to.have.property("data");
    });

    // And same for `Czas do`.
    cy.get("input.date_to").type("2030-12-31").trigger("change");

    cy.wait("@eventsAjax").then((interception) => {
      expect(interception.response.statusCode, "AJAX must not 500").to.eq(200);
      expect(interception.request.body).to.contain("date_to=2030-12-31");
    });
  });
});
