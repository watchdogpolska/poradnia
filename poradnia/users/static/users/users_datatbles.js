;(function($) {
    $(function() {
        const table1 = document.getElementById("datatable_users");
        if (table1) {
            var tableTop = $("#tableWrapper")[0].getBoundingClientRect().top;
            var viewportHeight = $(window).innerHeight();
            var maxHeight = viewportHeight - tableTop;
            $("#tableWrapper").css({
                maxHeight: maxHeight - 0,
            });

            // Subscribe "initComplete" event
            $('#datatable_users').on('initComplete', function(event, table ) {
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
                $('#datatable_users'),
                "/uzytkownik/users_table_ajax_data/",
                {
                    processing: true,
                    serverSide: true,
                    autoWidth: true,
                    full_row_select: false,
                    scrollX: true,
                    scrollY: maxHeight - 250,
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
                },
            );
        }
    });
})(jQuery);
