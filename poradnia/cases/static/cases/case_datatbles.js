;(function($) {
    $(function() {
        const table1 = document.getElementById("datatable_cases");
        if (table1) {
            var tableTop = $("#tableWrapper")[0].getBoundingClientRect().top;
            var viewportHeight = $(window).innerHeight();
            var maxHeight = viewportHeight - tableTop;
            $("#tableWrapper").css({
                maxHeight: maxHeight - 0,
            });
            // Subscribe "initComplete" event
            $('#datatable_cases').on('initComplete', function(event, table ) {
                // Code to resize input fields
                const tableWrapper = $("#tableWrapper");
                const headerCells = tableWrapper.find("th");
                headerCells.each(function() {
                    const input = $(this).find("input[type=text]");
                    $(this).css("padding", "0");
                    input.css("width", "100%");
                    input.css("box-sizing", "border-box");
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
                    status_free: function() { return $("input[name='check_status_free']").is(":checked") ? 1 : 0; },
                    status_assigned: function() { return $("input[name='check_status_assigned']").is(":checked") ? 1 : 0; },
                    status_moderated: function() { return $("input[name='check_status_moderated']").is(":checked") ? 1 : 0; },
                    status_closed: function() { return $("input[name='check_status_closed']").is(":checked") ? 1 : 0; },
                    handled_yes: function() { return $("input[name='check_handled_yes']").is(":checked") ? 1 : 0; },
                    handled_no: function() { return $("input[name='check_handled_no']").is(":checked") ? 1 : 0; },
                    has_project_yes: function() { return $("input[name='check_has_project_yes']").is(":checked") ? 1 : 0; },
                    has_project_no: function() { return $("input[name='check_has_project_no']").is(":checked") ? 1 : 0; },
                },
            );
            $('.filters input').on('change paste keyup', function() {
                // redraw the table
                $('#datatable_cases').DataTable().ajax.reload(null, false);
            });
        }
    });
})(jQuery);
