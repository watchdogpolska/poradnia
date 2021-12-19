const register = (cy) => ({
  firstName,
  lastName,
  username,
  email,
  password,
}) => {
  // Homepage.
  cy.visit("/");
  cy.contains("Zarejestruj").click();

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
