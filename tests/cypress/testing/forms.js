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

module.exports = { submitCaseForm, submitLetterForm };
