// tests/cypress.config.js
const { defineConfig } = require('cypress');
const db = require('./cypress/plugins/db');
const fetchTasks = require('./cypress/plugins/fetch');

module.exports = defineConfig({
  e2e: {
    // Preserve your current baseUrl:
    baseUrl: 'http://web:8000',

    /**
     * Keep existing spec layout so you don't have to rename files now.
     * You can later switch to cypress/e2e and *.cy.js if you prefer.
     */
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',

    // Make sure we use the new support entrypoint used by Cypress >=10
    supportFile: 'cypress/support/e2e.js',

    /**
     * Migration of your old plugins/index.js to setupNodeEvents.
     * All tasks are registered here now.
     */
    setupNodeEvents(on, config) {
      on('task', {
        'db:query': db.query,
        'db:clear': db.clear,
        'fetch:get': fetchTasks.get,
      });
      return config;
    },
  },
});
