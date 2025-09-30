const register = (cy) => ({
  firstName,
  lastName,
  username,
  email,
  password,
}) => {
  // Homepage.
  cy.visit("/");
  // Close any donate popup that might appear
  cy.closeDonatePopup();
  cy.contains("Rejestracja").click();
  
  // Ensure no popup is blocking the registration form
  cy.closeDonatePopup();

  // Register.
  cy.get('input[name="first_name"]').type(firstName);
  cy.get('input[name="last_name"]').type(lastName);
  cy.get('input[name="username"]').type(username);
  // Extra popup check before email input (common failure point)
  cy.closeDonatePopup();
  cy.get('input[name="email"]').type(email, {force: true});
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
  // Close any donate popup that might appear
  cy.closeDonatePopup();
  cy.contains("Zaloguj").click();
  
  // Ensure no popup is blocking the login form
  cy.closeDonatePopup();

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
