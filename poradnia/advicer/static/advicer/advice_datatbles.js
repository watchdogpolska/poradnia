;(function($) {
    $(function() {
        const table1 = document.getElementById("datatable_advices");
        if (table1) {
            var tableTop = $("#tableWrapper")[0].getBoundingClientRect().top;
            var viewportHeight = $(window).innerHeight();
            var maxHeight = viewportHeight - tableTop;
            $("#tableWrapper").css({
                maxHeight: maxHeight - 0,
            });
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
                    helped_yes: function() { return $("input[name='check_helped_yes']").is(":checked") ? 1 : 0; },
                    helped_no: function() { return $("input[name='check_helped_no']").is(":checked") ? 1 : 0; },
                    helped_blank: function() { return $("input[name='check_helped_blank']").is(":checked") ? 1 : 0; },
                    visible_yes: function() { return $("input[name='check_visible_yes']").is(":checked") ? 1 : 0; },
                    visible_no: function() { return $("input[name='check_visible_no']").is(":checked") ? 1 : 0; },
                },
            );
            $('.filters input').on('change paste keyup', function() {
                // redraw the table
                $('#datatable_advices').DataTable().ajax.reload(null, false);
            });
        }
    });
})(jQuery);
