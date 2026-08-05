(function () {
    "use strict";

    function cellValue(cell) {
        var text = cell.textContent.trim();
        var numeric = parseFloat(text.replace(/\s/g, "").replace(",", "."));
        return isNaN(numeric) ? text.toLowerCase() : numeric;
    }

    function sortTable(table, columnIndex, ascending) {
        var tbody = table.tBodies[0];
        var rows = Array.prototype.slice.call(tbody.rows);
        var pinned = rows.filter(function (row) {
            return row.dataset.pinned === "1";
        });
        var sortable = rows.filter(function (row) {
            return row.dataset.pinned !== "1";
        });

        sortable.sort(function (rowA, rowB) {
            var a = cellValue(rowA.cells[columnIndex]);
            var b = cellValue(rowB.cells[columnIndex]);
            if (a < b) {
                return ascending ? -1 : 1;
            }
            if (a > b) {
                return ascending ? 1 : -1;
            }
            return 0;
        });

        sortable.concat(pinned).forEach(function (row) {
            tbody.appendChild(row);
        });
    }

    document.addEventListener("click", function (event) {
        var th = event.target.closest(".sortable-table th[data-sort-key]");
        if (!th) {
            return;
        }
        var table = th.closest("table");
        var headerRow = th.parentElement;
        var columnIndex = Array.prototype.indexOf.call(headerRow.children, th);
        var ascending = th.getAttribute("aria-sort") !== "ascending";

        Array.prototype.forEach.call(headerRow.children, function (header) {
            header.removeAttribute("aria-sort");
        });
        th.setAttribute("aria-sort", ascending ? "ascending" : "descending");

        sortTable(table, columnIndex, ascending);
    });
})();
