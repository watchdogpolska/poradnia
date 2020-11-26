;(function($) {
    $(function () {
        var fields = document.querySelectorAll('.datetimeinput');
        var fields_array = Array.prototype.slice.call(fields);
        fields_array.forEach(function (item) {
            new Pikaday({
                field: item,
                firstDay: 1,
                format: 'DD.MM.YYYY HH:mm:ss',
                minDate: new Date('2000-01-01'),
                maxDate: new Date('2020-12-31'),
                yearRange: [2000, 2020],
                showTime: true,
                use24hour: true
            });
        });
    });

    $(function () {
        $('[data-toggle="tooltip"]').tooltip();
    });

    $(function () {
        function storageAvailable(type) {
            try {
                var storage = window[type],
                    x = "__storage_test__";
                storage.setItem(x, x);
                storage.removeItem(x);
                return true;
            } catch (e) {
                return (
                    e instanceof DOMException &&
                    // everything except Firefox
                    (e.code === 22 ||
                        // Firefox
                        e.code === 1014 ||
                        // test name field too, because code might not be present
                        // everything except Firefox
                        e.name === "QuotaExceededError" ||
                        // Firefox
                        e.name === "NS_ERROR_DOM_QUOTA_REACHED") &&
                    // acknowledge QuotaExceededError only if there's something already stored
                    window[type].length !== 0
                );
            }
        }

        if (!storageAvailable("localStorage")) {
            return;
        }

        function findByName(inputs, name) {
            return inputs.find(function (el) {
                return el.name == name;
            });
        }

        function loadInitalData(inputs, saveKey) {
            try {
                var formData = JSON.parse(localStorage.getItem(saveKey));
                if (formData) {
                    formData.forEach(function (inputData) {
                        var input = findByName(inputs, inputData.name);
                        if (input) {
                            input.value = inputData.value;
                        }
                    });
                }
            } catch (e) {
            }
        }

        function serializeForm(inputs) {
            return inputs.map(function (input) {
                return {name: input.name, value: input.value};
            });
        }

        function setupListeners(inputs, saveKey) {
            inputs.forEach(function (input) {
                input.addEventListener("input", function () {
                    var formData = serializeForm(inputs);
                    localStorage.setItem(saveKey, JSON.stringify(formData));
                });
            });
        }

        var forms = Array.from(document.querySelectorAll("[data-form-save]"));

        forms.forEach(function (element) {
            var saveKey = "form-" + element.getAttribute("data-form-save");
            var inputs = Array.from(element.querySelectorAll('input:not([type="hidden"]), textarea'));
            loadInitalData(inputs, saveKey);
            setupListeners(inputs, saveKey);
        });
    });
})(jQuery);
