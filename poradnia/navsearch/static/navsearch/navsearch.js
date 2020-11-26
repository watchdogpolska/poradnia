;(function($) {
    $(document).ready(function () {
        $('.navsearch').each(function(){
            $navsearch = $(this);
            $input =  $navsearch.find('.navsearch__input');
            $results = $navsearch.find('.navsearch__results');
            $url = $navsearch.data('autocomplete-url');
            $input.on('keyup, keydown', _.debounce(function(event) {
                var keywords = $input.val();

                $.getJSON($url, {q: keywords}, function(response) {
                    // Clear
                    $results.empty();

                    response.results.forEach(function(group) {
                        // Create
                        $group = $('<div class="panel panel-default">');
                        $group_title = $('<div class="panel-heading"></div>')
                        $group_list = $('<div class="list-group"></div>');

                        // Bind
                        $group_title.text(group.text);
                        group.children.forEach(function(item) {
                            // Create
                            var $item = $('<a class="list-group-item">');

                            // Bind
                            $item.attr('href', item.url)
                                .text(item.text);

                            // Append
                            $group_list.append($item);
                        })

                        // Append
                        $group.append($group_title);
                        $group.append($group_list);
                        $results.append($group);
                    });
                });
            }, 300))
        })
    });
})(jQuery);
