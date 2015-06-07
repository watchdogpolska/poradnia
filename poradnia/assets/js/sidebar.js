document.addEventListener('DOMContentLoaded', function() {
			var menu_toogles = document.querySelectorAll('.navbar-toggle');
			Array.prototype.slice.call(menu_toogles).forEach(function(toggle) {
				toggle.addEventListener('click', function(e) {
					var target = document.querySelector(toggle.dataset.target)
					if(target)
						target.classList.toggle('show-sidebar');
					e.preventDefault();
				});
			});
		});