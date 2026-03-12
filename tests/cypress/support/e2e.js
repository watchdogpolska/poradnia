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

// Check the MFA bypass cookie before each test - good for debugging tests
// beforeEach(() => {
//   cy.task('log', `E2E secret = ${Cypress.env('E2E_MFA_BYPASS_SECRET')}`)
// })

// Set the MFA bypass cookie before each test, using the secret from environment
beforeEach(() => {
  cy.setCookie('e2e_bypass_mfa', Cypress.env('E2E_MFA_BYPASS_SECRET'), { path: '/' })
})

