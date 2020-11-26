require("cypress-file-upload");

// Select an option containing `text`.
// Standard `select` command expects an exact match.
//
// Credits: https://stackoverflow.com/a/52219275/7742560
Cypress.Commands.add(
  "selectContaining",
  { prevSubject: "element" },
  (subject, text, options) => {
    return cy
      .wrap(subject)
      .contains("option", text, options)
      .then((option) => cy.wrap(subject).select(option.text().trim()));
  }
);
