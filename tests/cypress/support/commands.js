import 'cypress-file-upload';

// Select an option containing `text`.
// Standard `select` command expects an exact match.
// This command allows you to select an option that contains the given text or 
// matches a regex.
if (!Cypress.Commands._commands || !Cypress.Commands._commands['selectContaining']) {
  Cypress.Commands.add(
    'selectContaining',
    { prevSubject: 'element' },
    (subject, textOrRegex) => {
      const re =
        textOrRegex instanceof RegExp
          ? textOrRegex
          : new RegExp(String(textOrRegex), 'i');

      const $select = Cypress.$(subject);
      const $match = $select
        .find('option')
        .filter((_, el) => re.test(Cypress.$(el).text()));

      if ($match.length === 0) {
        throw new Error(`selectContaining: no <option> matching ${re} found`);
      }

      const value = $match.first().val();
      return cy.wrap(subject).select(value, { force: true });
    }
  );
}

// Command to close any visible donate popup
Cypress.Commands.add('closeDonatePopup', () => {
  // Simple approach: check if popups exist and are visible, then close them
  cy.get('body').then(($body) => {
    // Handle primary popup
    if ($body.find('#popup-container:visible').length) {
      if ($body.find('button#donate-button:visible').length) {
        cy.get('#donate-button').click({force: true});
      } else {
        cy.get('#popup-container').invoke('hide');
      }
    }
    
    // Handle alternative popup
    if ($body.find('#alt-popup-container:visible').length) {
      if ($body.find('button#alt-donate-button:visible').length) {
        cy.get('#alt-donate-button').click({force: true});
      } else {
        cy.get('#alt-popup-container').invoke('hide');
      }
    }
  });
  
  // Brief wait for any animations to complete
  cy.wait(300);
});
