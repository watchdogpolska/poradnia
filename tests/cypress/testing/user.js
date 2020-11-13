// Builds an object required to register a user, setting
// all fields to readable values based on a provided `id`.
const fromId = (id) => ({
  firstName: `${id}-firstName`,
  lastName: `${id}-lastName`,
  username: `${id}-username`,
  email: `${id}@email.com`,
  password: `${id}-password`,
});

module.exports = { fromId };
