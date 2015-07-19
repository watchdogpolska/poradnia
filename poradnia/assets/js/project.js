$(function(){
	var timepicker = new Pikaday(
	{
		field: document.querySelector('#id_time'),
		firstDay: 1,
		format: 'DD.MM.YYYY HH:mm:ss',
		minDate: new Date('2000-01-01'),
		maxDate: new Date('2020-12-31'),
		yearRange: [2000,2020],
		showTime: true,
		use24hour: true
	});
});

$(function () {
	$('[data-toggle="tooltip"]').tooltip()
})
