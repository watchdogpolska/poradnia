const register = (cy) => ({
  firstName,
  lastName,
  username,
  email,
  password,
}) => {
  // Homepage.
  cy.visit("/");
  cy.wait(1000); // wait for 1 second for donate popup to appear
  cy.get('body').then(($body) => {
    if ($body.find('button#donate-button:visible').length) {
      cy.get('#donate-button').click({force: true});
      cy.get('#popup-container').should('not.be.visible');
    }
  }); // close donate popup if it appears
  cy.contains("Rejestracja").click();

  // Register.
  cy.get('input[name="first_name"]').type(firstName);
  cy.get('input[name="last_name"]').type(lastName);
  cy.get('input[name="username"]').type(username);
  cy.get('input[name="email"]').type(email);
  cy.get('input[name="password1"]').type(password);
  cy.get('input[name="password2"]').type(password);
  cy.get('input[name="giodo"]').click();
  cy.get('input[name="signup"]').click();

  // Homepage.
  cy.visit("/");
};

const login = (cy) => ({ username, password }) => {
  // Homepage.
  cy.visit("/");
  cy.wait(1000); // wait for 1 second for donate popup to appear
  cy.get('body').then(($body) => {
    if ($body.find('button:contains("Zamknij"):visible').length) {
      cy.contains('Zamknij').click({force: true});
      cy.get('#popup-container').should('not.be.visible');
    }
  }); // close donate popup if it appears
  cy.contains("Zaloguj").click();

  // Login.
  cy.get('input[name="login"]').type(username);
  cy.get('input[name="password"]').type(password);
  cy.contains("input", "Zaloguj").click();

  // Homepage.
  cy.visit("/");
};

const logout = (cy) => () => {
  // Homepage.
  cy.visit("/");
  cy.contains("Wyloguj").click();

  // Logout.
  cy.contains("button", "Wyloguj").click();

  // Homepage.
  cy.visit("/");
};

module.exports = { register, login, logout };
