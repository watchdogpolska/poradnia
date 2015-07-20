$(function(){
	var fields = document.querySelectorAll('.datetimeinput');
	var fields_array = Array.prototype.slice.call(fields);
	fields_array.forEach(function(item){
		new Pikaday({
			field: item,
			firstDay: 1,
			format: 'DD.MM.YYYY HH:mm:ss',
			minDate: new Date('2000-01-01'),
			maxDate: new Date('2020-12-31'),
			yearRange: [2000,2020],
			showTime: true,
			use24hour: true
		});
	})
});

$(function () {
	$('[data-toggle="tooltip"]').tooltip()
})
