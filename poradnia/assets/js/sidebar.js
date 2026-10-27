document.addEventListener('DOMContentLoaded', function() {
			var menu_toogles = document.querySelectorAll('.navbar-toggler');
			Array.prototype.slice.call(menu_toogles).forEach(function(toggle) {
				toggle.addEventListener('click', function(e) {
					var target = document.querySelector(toggle.dataset.bsTarget)
					if(target) {
						var expanded = target.classList.toggle('show-sidebar');
						// Previously managed by Bootstrap's own collapse JS
						// (via data-bs-toggle="collapse", removed from the
						// button - see base.html's comment on why) -
						// replicated here so the toggle still reports its
						// state to assistive tech.
						toggle.classList.toggle('collapsed', !expanded);
						toggle.setAttribute('aria-expanded', expanded);
					}
					e.preventDefault();
				});
			});
		});