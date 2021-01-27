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
      cy.get("select").selectContaining(adviceIssue.name);
    });
  }

  if (adviceArea) {
    cy.contains("div", "Problemy z zakresu prawa").within(($div) => {
      cy.get("select").selectContaining(adviceArea.name);
    });
  }

  cy.contains("div", "Czy pomogliśmy").within(($div) => {
    cy.get("select").select(solved ? "Tak" : "Nie");
  });

  cy.contains("div", "Jednostka podziału").within(($div) => {
    // Autocomplete form.
    // There may be a short delay between typing the text and the widget
    // filtering its options, hence `wait`.
    cy.get(".selection").click();
    cy.focused().type(administrativeDivision).wait(500).type("{enter}");
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
  cy.contains("div", "Czy pomogliśmy").within(($div) => {
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
        cy.get(".selection")
          .click()
          .focused()
          .type(administrativeDivision.name)
          .wait(500)
          .type("{enter}");
      }
    } else {
      // NOTE: this is a multiselect field.
      // `clear` seems to clean up all selections, but I have a feeling
      // that this approach may be a bit fragile.
      // Revisit if causes problems.
      cy.get(".selection").click().focused().clear().type("{esc}");
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
    cy.get(".selection").click();
    if (adviceAuthor) {
      cy.focused().type(adviceAuthor.firstName).wait(500).type("{enter}");
    } else {
      cy.focused().clear().type("{esc}");
    }
  });

  // If falsy, unselect all.
  cy.contains("div", "Problemy z zakresu prawa").within(($div) => {
    const selectElement = cy.get("select");
    if (adviceAreas) {
      selectElement.select(adviceAreas.map(({ name }) => name));
    } else {
      clearSelect(selectElement);
    }
  });

  // If falsy, unselect all.
  cy.contains("div", "Zakresy tematyczne").within(($div) => {
    const selectElement = cy.get("select");
    if (adviceIssues) {
      selectElement.select(adviceIssues.map(({ name }) => name));
    } else {
      clearSelect(selectElement);
    }
  });

  cy.contains("Filtruj").click();
};

// Credits: https://stackoverflow.com/a/56343368/7742560
const clearSelect = (selectElement) => {
  selectElement.invoke("val", "");
};

module.exports = {
  submitCaseForm,
  submitLetterForm,
  fillPikaForm,
  submitEventForm,
  submitCourtCaseForm,
  submitAdviceForm,
  submitAdviceFilterForm,
};
