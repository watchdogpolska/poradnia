document.addEventListener('DOMContentLoaded', function () {
    const table1 = document.getElementById("datatable_advices");
    if (!table1) return;
    const tableWrapper = document.getElementById("tableWrapper");
    const tableTop = tableWrapper.getBoundingClientRect().top;
    const viewportHeight = window.innerHeight;
    const maxHeight = viewportHeight - tableTop;
    tableWrapper.style.maxHeight = maxHeight + 'px';
    // Subscribe "initComplete" event
    $('#datatable_advices').on('initComplete', function (event, table) {
        // Code to resize input fields
        const headerCells = tableWrapper.querySelectorAll("th");
        headerCells.forEach(function (th) {
            th.style.padding = "0";
            const input = th.querySelector("input[type=text]");
            if (input) {
                input.style.width = "100%";
                input.style.boxSizing = "border-box";
            }
            const select = th.querySelector("select");
            if (select) {
                select.style.boxSizing = "border-box";
                select.style.width = "100%";
            }
        });
    });
    // Initialize table
    AjaxDatatableViewUtils.initialize_table(
        $('#datatable_advices'),
        "/porady/advice_table_ajax_data/",
        {
            // extra_options (example)
            processing: true,
            serverSide: true,
            autoWidth: true,
            full_row_select: false,
            scrollX: true,
            // searching: false,
            scrollY: maxHeight - 250,
            // TODO make fixedColumns working !!!
            // fixedColumns: {
            //     left: 1,
            //     // right: 1
            // }
            "language": {
                "processing":     "Przetwarzanie...",
                "search":         "Szukaj:",
                "lengthMenu":     "Pokaż _MENU_ pozycji",
                "info":           "Pozycje od _START_ do _END_ z _TOTAL_ łącznie",
                "infoEmpty":      "Pozycji 0 z 0 dostępnych",
                "infoFiltered":   "(filtrowanie spośród _MAX_ dostępnych pozycji)",
                "infoPostFix":    "",
                "loadingRecords": "Wczytywanie...",
                "zeroRecords":    "Nie znaleziono pasujących pozycji",
                "emptyTable":     "Brak danych",
                "paginate": {
                    "first":      "Pierwsza",
                    "previous":   "Poprzednia",
                    "next":       "Następna",
                    "last":       "Ostatnia"
                },
                "aria": {
                    "sortAscending": ": aktywuj, by posortować kolumnę rosnąco",
                    "sortDescending": ": aktywuj, by posortować kolumnę malejąco"
                }
            },
        }, {
            // extra_data
            helped_yes: function() { return document.querySelector("input[name='check_helped_yes']").checked ? 1 : 0; },
            helped_no: function() { return document.querySelector("input[name='check_helped_no']").checked ? 1 : 0; },
            helped_blank: function() { return document.querySelector("input[name='check_helped_blank']").checked ? 1 : 0; },
            visible_yes: function() { return document.querySelector("input[name='check_visible_yes']").checked ? 1 : 0; },
            visible_no: function() { return document.querySelector("input[name='check_visible_no']").checked ? 1 : 0; },
        },
    );
    const filtersContainer = document.querySelector('.filters');
    if (filtersContainer) {
        filtersContainer.addEventListener('change', function () {
            $('#datatable_advices').DataTable().ajax.reload(null, false);
        });
    }
});
