// When creating many instances, their `lft` and `rght` fields should not
// overlap, as long as all items are on the same level.
// This function takes care of that. It should be called at most once per test.
const batchFromIds = (ids, category) =>
  ids.map((id, i) => ({
    name: id,
    lft: 2 * i,
    rght: 2 * i + 1,
    level: 3,
    category: category.id,
  }));

module.exports = { batchFromIds };
