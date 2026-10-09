document.addEventListener('DOMContentLoaded', function() {
			var menu_toogles = document.querySelectorAll('.navbar-toggler');
			Array.prototype.slice.call(menu_toogles).forEach(function(toggle) {
				toggle.addEventListener('click', function(e) {
					var target = document.querySelector(toggle.dataset.bsTarget)
					if(target)
						target.classList.toggle('show-sidebar');
					e.preventDefault();
				});
			});
		});