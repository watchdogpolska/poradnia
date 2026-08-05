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

    function yearSelectValue(id) {
        var el = document.getElementById(id);
        return el ? el.value : null;
    }

    function startExport(baseUrl, year) {
        window.location.href = baseUrl + "?year=" + encodeURIComponent(year);
    }

    var pendingExportUrl = null;

    function openYearMismatchModal(exportUrl, casesYear, tagsYear) {
        pendingExportUrl = exportUrl;

        var casesRadio = document.getElementById("dashboard-export-year-cases");
        var tagsRadio = document.getElementById("dashboard-export-year-tags");
        casesRadio.value = casesYear;
        tagsRadio.value = tagsYear;
        casesRadio.checked = true;
        document.getElementById("dashboard-export-year-cases-value").textContent = casesYear;
        document.getElementById("dashboard-export-year-tags-value").textContent = tagsYear;

        window.jQuery("#dashboard-export-year-modal").modal("show");
    }

    document.addEventListener("click", function (event) {
        var exportBtn = event.target.closest("#dashboard-export-btn");
        if (exportBtn) {
            var exportUrl = exportBtn.dataset.exportUrl;
            var casesYear = yearSelectValue("cases-year");
            var tagsYear = yearSelectValue("advices-year");

            if (casesYear && tagsYear && casesYear !== tagsYear) {
                openYearMismatchModal(exportUrl, casesYear, tagsYear);
            } else {
                startExport(exportUrl, casesYear || tagsYear || exportBtn.dataset.currentYear);
            }
            return;
        }

        var confirmBtn = event.target.closest("#dashboard-export-year-confirm");
        if (confirmBtn && pendingExportUrl) {
            var checked = document.querySelector(
                'input[name="dashboard-export-year-choice"]:checked'
            );
            window.jQuery("#dashboard-export-year-modal").modal("hide");
            if (checked) {
                startExport(pendingExportUrl, checked.value);
            }
        }
    });
})();
