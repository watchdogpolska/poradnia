// Advice form: issues and areas depend on the selected scope (their
// autocompletes forward it), so changing the scope clears any already
// selected issues/areas and announces it via the #advice-scope-status
// live region.
document.addEventListener("DOMContentLoaded", function () {
  var scope = document.getElementById("id_scope");
  var status = document.getElementById("advice-scope-status");
  if (!scope) return;

  scope.addEventListener("change", function () {
    var cleared = false;
    ["id_issues", "id_area"].forEach(function (id) {
      var select = document.getElementById(id);
      var widget = select && select.closest("autocomplete-select");
      if (!widget) return;
      Array.from(widget.selected).forEach(function (choice) {
        widget.choiceUnselect(choice);
        cleared = true;
      });
    });
    if (cleared && status) {
      // Reset first so repeating the same message is announced again.
      status.textContent = "";
      setTimeout(function () {
        status.textContent = status.dataset.clearedMessage;
      }, 100);
    }
  });
});
