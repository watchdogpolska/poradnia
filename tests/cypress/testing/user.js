// Builds an object required to register a user, setting
// all fields to readable values based on a provided `id`.
const strongPassword = () =>
  `A!9zX#${Math.random().toString(36).slice(2, 8)}Q`;

const fromId = (id) => ({
  firstName: `${id}-firstName`,
  lastName: `${id}-lastName`,
  username: `${id}-username`,
  email: `${id}@email.com`,
  password: strongPassword(),
});

module.exports = { fromId };
