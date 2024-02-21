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

const submitTinymceLetterForm = (cy) => (form, { title, content, attachment }) => {
  cy.get('input[name="name"]').clear().type(title);
//  cy.get('body[id="tinymce"]').clear().type(content);
  cy.get('iframe[id="id_html_ifr"]').type(content);
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
  // applied {force: true} as per https://stackoverflow.com/questions/60660879/cypress-and-select2-jquery-plugin
  cy.get(".pika-select-hour").select(hour.toString(), {force: true});
  cy.get(".pika-select-minute").select(minute.toString(), {force: true});
  cy.get(".pika-select-month").select(month.toString(), {force: true});
  cy.get(".pika-select-year").select(year.toString(), {force: true});
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

const submitAdviceForm = (cy) => (
  form,
  {
    subject,
    comment,
    datetime,
    solved,
    administrativeDivision,
    adviceAuthor,
    adviceIssue,
    adviceArea,
  }
) => {
  if (adviceIssue) {
    cy.contains("div", "Zakresy tematyczne").within(($div) => {
      selectAutocompleteOptionContaining(
        cy.get(".selection"),
        adviceIssue.name
      );
    });
  }

  if (adviceArea) {
    cy.contains("div", "Problemy z zakresu prawa").within(($div) => {
      selectAutocompleteOptionContaining(cy.get(".selection"), adviceArea.name);
    });
  }

  cy.contains("div", "Czy udzieliliśmy porady").within(($div) => {
    cy.get("select").select(solved ? "Tak" : "Nie");
  });

  cy.contains("div", "Jednostka podziału").within(($div) => {
    selectAutocompleteOptionContaining(
      cy.get(".selection"),
      administrativeDivision
    );
  });

  cy.contains("div", "Przedmiot").within(($div) => {
    cy.get('input[type="text"]').clear().type(subject);
  });

  cy.contains("div", "Komentarz").within(($div) => {
    cy.get('textarea[name="comment"]').clear().type(comment);
  });

  // Datetime selection. See `submitEventForm` for details.
  cy.contains("Udzielona o").click();
  cy.document().within(($doc) => {
    cy.get(".pika-single").within(($pika) => fillPikaForm(cy)($pika, datetime));
  });

  cy.contains("div", "Radzący").within(($div) => {
    cy.get("select").selectContaining(adviceAuthor.firstName);
  });

  cy.contains("Zapisz").click();
};

// Fill the filters.
// Where applicable, undefined / invalid values will fall back to default
// values / empty filters, e.g. `solved` will be set to "Nieznane" (null
// filter) for any non-boolean value.
const submitAdviceFilterForm = (cy) => (
  form,
  {
    solved,
    administrativeDivisions,
    subject,
    adviceAuthor,
    adviceIssues,
    adviceAreas,
  }
) => {
  // If not true/false, set to a noop filter.
  cy.contains("div", "Czy udzieliliśmy porady").within(($div) => {
    cy.get("select").select(
      solved === true ? "Tak" : solved === false ? "Nie" : "Nieznane"
    );
  });

  // If falsy, clear all input.
  cy.contains("div", "Gmina").within(($div) => {
    // Multi-select autocomplete form.
    // See other autocomplete forms for more info.
    if (administrativeDivisions) {
      for (const administrativeDivision of administrativeDivisions) {
        // Re-select the field on every iteration.
        // Less fragile than depending on current state.
        selectAutocompleteOptionContaining(
          cy.get(".selection"),
          administrativeDivision.name
        );
      }
    } else {
      clearAutocompleteField(cy.get(".selection"));
    }
  });

  // If falsy, fill with an empty string.
  cy.contains("div", "Przedmiot").within(($div) => {
    const clearInput = cy.get('input[type="text"]').clear();
    if (subject) {
      clearInput.type(subject);
    }
  });

  // If falsy, clear input.
  cy.contains("div", "Radzący").within(($div) => {
    const selectionEl = cy.get(".selection");
    if (adviceAuthor) {
      selectAutocompleteOptionContaining(selectionEl, adviceAuthor.firstName);
    } else {
      clearAutocompleteField(selectionEl);
    }
  });

  // If falsy, unselect all.
  cy.contains("div", "Problemy z zakresu prawa").within(($div) => {
    if (adviceAreas) {
      for (const adviceArea of adviceAreas) {
        selectAutocompleteOptionContaining(
          cy.get(".selection"),
          adviceArea.name
        );
      }
    } else {
      clearAutocompleteField(cy.get(".selection"));
    }
  });

  // If falsy, unselect all.
  cy.contains("div", "Zakresy tematyczne").within(($div) => {
    if (adviceIssues) {
      for (const adviceIssue of adviceIssues) {
        selectAutocompleteOptionContaining(
          cy.get(".selection"),
          adviceIssue.name
        );
      }
    } else {
      clearAutocompleteField(cy.get(".selection"));
    }
  });

  cy.contains("Zastosuj filtr").click();
};

// Credits: https://stackoverflow.com/a/56343368/7742560
const clearSelect = (selectElement) => {
  selectElement.invoke("val", "");
};

// Expected to be invoked inside a div containing one autocomplete field.
// Waits a bit before pressing enter to give the async operation some time
// to complete.
// If flaky, consider increasing the timeout.
const selectAutocompleteOptionContaining = (selectionElement, text) => {
  selectionElement.click().focused().type(text).wait(1000).type("{enter}");
};

// Works with multiselect fields.
// `clear` seems to clean up all selections, but I have a feeling
// that this approach may be a bit fragile.
// Revisit if causes problems.
const clearAutocompleteField = (selectionElement) => {
  selectionElement.click().focused().clear().wait(500).type("{esc}");
};

module.exports = {
  submitCaseForm,
  submitLetterForm,
  submitTinymceLetterForm,
  fillPikaForm,
  submitEventForm,
  submitCourtCaseForm,
  submitAdviceForm,
  submitAdviceFilterForm,
};
