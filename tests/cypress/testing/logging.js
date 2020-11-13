// Adds logging to a function returning a promise.
// Logs a message when:
//  - the function is called
//  - the promise fulfills
const withPromiseLogging = (fnMessage) => (fn) => (...args) => {
  console.log(`> ${fnMessage}(${args})`);
  const p = fn(...args);
  return p
    .catch((err) => {
      console.log(`<! ${fnMessage}(${err})`);
      throw err;
    })
    .then((ret) => {
      console.log(`< ${fnMessage}(${JSON.stringify({ ret })})`);
      return ret;
    });
};

module.exports = { withPromiseLogging };
