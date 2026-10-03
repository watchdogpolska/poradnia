const { register } = require("../testing/auth");
const { addSuperUserPrivileges } = require("../testing/management");
const User = require("../testing/user");

describe("events", () => {
  beforeEach(() => {
    cy.task("db:clear");
    cy.viewport(1920, 1080);
  });

  it("filter toggles and the datepicker trigger a DataTables reload on /wydarzenia/table/", () => {
    const user = User.fromId("testUser");
    register(cy)(user);
    addSuperUserPrivileges(cy)(user);

    cy.closeDonatePopup();
    cy.intercept({ pathname: "/wydarzenia/events_table_ajax_data/" }).as(
      "dtAjax"
    );
    cy.visit("/wydarzenia/table/");

    // Initial DataTables load.
    cy.wait("@dtAjax");

    // Sidebar checkbox — native `change` listener on .filters.
    cy.get('input[name="check_deadline_yes"]').uncheck();
    cy.wait("@dtAjax");

    cy.get('input[name="check_deadline_yes"]').check();
    cy.wait("@dtAjax");

    // Datepicker — fn_daterange_widget_initialize injects
    // <input class="date_from"> / <input class="date_to"> into the
    // DataTables toolbar; the native change listener delegated on the
    // toolbar must pick these up and trigger a reload via table.api().draw().
    // Set the value directly and fire `change` ourselves instead of
    // `.type()`: native <input type="date"> splits into day/month/year
    // segments with its own keystroke-timing heuristic, which is flaky
    // under CI's slower/contended CPU (segments can reset instead of
    // advance, so the value never completes and `change` never fires).
    cy.get("input.date_from").invoke("val", "2020-01-01").trigger("change");
    cy.wait("@dtAjax");

    cy.get("input.date_to").invoke("val", "2020-12-31").trigger("change");
    cy.wait("@dtAjax");
  });
});
