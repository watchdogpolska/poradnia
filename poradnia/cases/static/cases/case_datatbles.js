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
            AjaxDatatableViewUtils.initialize_table(
                $('#datatable_cases'),
                "/sprawy/case_table_ajax_data/",
                {
                    // extra_options (example)
                    processing: false,
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
