// cypress/support/e2e.js

// Load custom commands (ESM import is the recommended pattern in Cypress ≥10)
import './commands';

// Optionally ignore uncaught exceptions from the AUT.
// You can remove this if you want failures on app errors.
Cypress.on('uncaught:exception', (_err, _runnable) => {
  // returning false here prevents Cypress from failing the test
  // eslint-disable-next-line no-console
  console.log('Uncaught exception temporarily ignored');
  return false;
});
