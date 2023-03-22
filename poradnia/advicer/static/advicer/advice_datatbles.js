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
                    // ...
                },
            );
        }
    });
})(jQuery);
// ;(function($) {
//     $(document).ready(function () {
//         const table1 = document.getElementById("datatable_advices");
//         if (table1) {
//             var tableTop = $("#tableWrapper")[0].getBoundingClientRect().top;
//             var viewportHeight = $(window).innerHeight();
//             var maxHeight = viewportHeight - tableTop;
//             $("#tableWrapper").css({
//                 maxHeight: maxHeight - 0,
//             });
//             AjaxDatatableViewUtils.initialize_table(
//                 $('#datatable_advices'),
//                 "/porady/advice_table_ajax_data/",
//                 {
//                     // extra_options (example)
//                     processing: false,
//                     autoWidth: true,
//                     full_row_select: false,
//                     scrollX: true,
//                     // searching: false,
//                     scrollY: maxHeight - 250,
//                     // TODO make fixedColumns working !!!
//                     // fixedColumns: {
//                     //     left: 1,
//                     //     // right: 1
//                     // }
//                 }, {
//                     // extra_data
//                     // ...
//                 },
//             );
//         }
//     });
// })(jQuery);
