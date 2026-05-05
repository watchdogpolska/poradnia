document.addEventListener('DOMContentLoaded', function () {
    const table1 = document.getElementById("datatable_cases");
    if (!table1) return;
    const tableWrapper = document.getElementById("tableWrapper");
    const tableTop = tableWrapper.getBoundingClientRect().top;
    const viewportHeight = window.innerHeight;
    const maxHeight = viewportHeight - tableTop;
    tableWrapper.style.maxHeight = maxHeight + 'px';
    // Subscribe "initComplete" event
    $('#datatable_cases').on('initComplete', function (event, table) {
        // Code to resize input fields
        const headerCells = tableWrapper.querySelectorAll("th");
        headerCells.forEach(function (th) {
            th.style.padding = "0";
            const input = th.querySelector("input[type=text]");
            if (input) {
                input.style.width = "100%";
                input.style.boxSizing = "border-box";
            }
        });
    });
    // Initialize table
    AjaxDatatableViewUtils.initialize_table(
        $('#datatable_cases'),
        "/sprawy/case_table_ajax_data/",
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
            status_free: function() { return document.querySelector("input[name='check_status_free']").checked ? 1 : 0; },
            status_assigned: function() { return document.querySelector("input[name='check_status_assigned']").checked ? 1 : 0; },
            status_moderated: function() { return document.querySelector("input[name='check_status_moderated']").checked ? 1 : 0; },
            status_closed: function() { return document.querySelector("input[name='check_status_closed']").checked ? 1 : 0; },
            handled_yes: function() { return document.querySelector("input[name='check_handled_yes']").checked ? 1 : 0; },
            handled_no: function() { return document.querySelector("input[name='check_handled_no']").checked ? 1 : 0; },
            has_project_yes: function() { return document.querySelector("input[name='check_has_project_yes']").checked ? 1 : 0; },
            has_project_no: function() { return document.querySelector("input[name='check_has_project_no']").checked ? 1 : 0; },
            has_deadline_yes: function() { return document.querySelector("input[name='check_has_deadline_yes']").checked ? 1 : 0; },
            has_deadline_no: function() { return document.querySelector("input[name='check_has_deadline_no']").checked ? 1 : 0; },
            involved_staff_filter: function() { return document.querySelector("select[name='involved_staff_select']").value; },
        },
    );
    const filtersContainer = document.querySelector('.filters');
    if (filtersContainer) {
        filtersContainer.addEventListener('change', function () {
            $('#datatable_cases').DataTable().ajax.reload(null, false);
        });
    }
});
