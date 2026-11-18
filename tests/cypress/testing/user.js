// Builds an object required to register a user, setting
// all fields to readable values based on a provided `id`.
const strongPassword = () => {
  const bytes = crypto.getRandomValues(new Uint8Array(3));
  const suffix = Array.from(bytes, (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");
  return `A!9zX#${suffix}Q`;
};

const fromId = (id) => ({
  firstName: `${id}-firstName`,
  lastName: `${id}-lastName`,
  username: `${id}-username`,
  email: `${id}@email.com`,
  password: strongPassword(),
});

module.exports = { fromId };
