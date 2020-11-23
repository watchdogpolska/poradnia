// Function filling forms with provided inputs.
// Submits the form in the final step.
//
// Each function expects to be executed from within a `within` call selecting
// the correct form.

const submitCaseForm = (cy) => (form, { title, content, attachment }) => {
  cy.get('input[name="name"]').clear().type(title);
  cy.get('textarea[name="text"]').clear().type(content);
  if (attachment) {
    cy.get('input[type="file"]')
      .filter(":visible")
      .first()
      .attachFile(attachment);
  }
  cy.contains("input", "Zgłoś").click();
};

const submitLetterForm = (cy) => (form, { title, content, attachment }) => {
  cy.get('input[name="name"]').clear().type(title);
  cy.get('textarea[name="text"]').clear().type(content);
  if (attachment) {
    cy.get('input[type="file"]')
      .filter(":visible")
      .first()
      .attachFile(attachment);
  }
  cy.contains("input", "Odpowiedz wszystkim").click();
};

// Fill a pikaday calendar.
// Uses class selectors instead of text selectors because labels are non-deterministic (i.e. the month label is
// displayed as the current month). This may require changing the test if class names change (rather unlikely), but
// at least it won't require a change every month, or some locale-specific current datetime parsing logic.
//
// Named "fill*" instead of "submit*" because it doesn't submit anything. It's a single field, not a standalone form.
const fillPikaForm = (cy) => (form, { year, month, day, hour, minute }) => {
  // Pika seems to close upon selecting a day.
  // Start with time selection, select day in very the last step.
  // All items are `toString`ed because cypress expects an exact match upon calling `select`.
  cy.get(".pika-select-hour").select(hour.toString());
  cy.get(".pika-select-minute").select(minute.toString());
  cy.get(".pika-select-month").select(month.toString());
  cy.get(".pika-select-year").select(year.toString());
  cy.get(".pika-table").contains(day).click();
};

const submitEventForm = (cy) => (form, { datetime, text }) => {
  cy.contains("div", "Przedmiot").within(($div) => {
    cy.get('textarea[name="text"]').clear().type(text);
  });
  // Click on the timeselect input. It will open a calender popup.
  cy.contains("Czas").click();

  // The popup is attached to body, outside of this element. Get the body to escape from the `within` block temporarily.
  // TODO: consider attaching the popup to the clicked input.
  cy.document().within(($doc) => {
    cy.get(".pika-single").within(($pika) => fillPikaForm(cy)($pika, datetime));
  });

  cy.contains("Zapisz").click();
};

const submitCourtCaseForm = (cy) => (form, { court, signature }) => {
  cy.contains("div", "Sąd").within(($div) => {
    cy.get("select").select(court);
  });

  cy.contains("div", "Signature").within(($div) => {
    cy.get('input[type="text"]').clear().type(signature);
  });

  cy.contains("Zapisz").click();
};

module.exports = {
  submitCaseForm,
  submitLetterForm,
  fillPikaForm,
  submitEventForm,
  submitCourtCaseForm,
};
