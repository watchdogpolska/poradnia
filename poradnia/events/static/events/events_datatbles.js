AjaxDatatableViewUtils.init({
    search_icon_html: '<i class="fa fa-search"></i>',
    language: {
    },
    fn_daterange_widget_initialize: function(table, data) {
        var wrapper = table.closest('.dataTables_wrapper');
        var toolbar = wrapper.find(".toolbar");
        toolbar.html(
            '<div class="daterange" style="float: left; margin-right: 6px;">' +
                '<span class="from"><label>Czas od</label>: ' +
                    '<input type="date" class="date_from datepicker"></span>' +
                '<span class="to"><label>&nbsp do</label>: ' +
                    '<input type="date" class="date_to datepicker"></span>' +
            '</div>'
        );
        toolbar.find('.date_from, .date_to').on('change', function(event) {
            // Annotate table with values retrieved from date widgets
            table.data('date_from', wrapper.find('.date_from').val());
            table.data('date_to', wrapper.find('.date_to').val());
            // Redraw table
            table.api().draw();
        });
    }
});

;(function($) {
    $(function() {
        const table1 = document.getElementById("datatable_events");
        if (table1) {
            var tableTop = $("#tableWrapper")[0].getBoundingClientRect().top;
            var viewportHeight = $(window).innerHeight();
            var maxHeight = viewportHeight - tableTop;
            $("#tableWrapper").css({
                maxHeight: maxHeight - 0,
            });
            // Subscribe "initComplete" event
            $('#datatable_events').on('initComplete', function(event, table ) {
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
                $('#datatable_events'),
                "/wydarzenia/events_table_ajax_data/",
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
                    deadline_yes: function() { return $("input[name='check_deadline_yes']").is(":checked") ? 1 : 0; },
                    deadline_no: function() { return $("input[name='check_deadline_no']").is(":checked") ? 1 : 0; },
                    completed_yes: function() { return $("input[name='check_completed_yes']").is(":checked") ? 1 : 0; },
                    completed_no: function() { return $("input[name='check_completed_no']").is(":checked") ? 1 : 0; },
                    public_yes: function() { return $("input[name='check_public_yes']").is(":checked") ? 1 : 0; },
                    public_no: function() { return $("input[name='check_public_no']").is(":checked") ? 1 : 0; },
                    courtsession_yes: function() { return $("input[name='check_courtsession_yes']").is(":checked") ? 1 : 0; },
                    courtsession_no: function() { return $("input[name='check_courtsession_no']").is(":checked") ? 1 : 0; },
                    // involved_staff_filter: function() { return $("select[name='involved_staff_select']").val(); },
                },
            );
            $('.filters input, .filters select').on('change paste keyup', function() {
                // redraw the table
                $('#datatable_events').DataTable().ajax.reload(null, false);
            });
        }
    });
})(jQuery);
