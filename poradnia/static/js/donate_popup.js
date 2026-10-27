document.addEventListener('DOMContentLoaded', function () {
    var alreadyDonated = Cookies.get('alreadyDonated');
    var popupShown = Cookies.get('popupShown');
    var container = document.getElementById('popup-container');
    var backdrop = document.getElementById('popup-backdrop');

    if (!(alreadyDonated || popupShown)) {
        container.classList.add('show');
        backdrop.classList.add('show');
        container.focus();
    }

    var checkbox = document.getElementById('alreadyDonated');
    if (checkbox) {
        checkbox.addEventListener('change', function () {
            if (this.checked) {
                Cookies.set('alreadyDonated', 'true', { expires: 60 });
            } else {
                Cookies.remove('alreadyDonated');
            }
        });
    }

    // Blocking the rest of the page with #popup-backdrop (see the
    // template's CSS) only stops mouse clicks - without this, a keyboard
    // user could still Tab straight past the popup into content that's
    // visually hidden behind the backdrop. Traps Tab/Shift+Tab within the
    // popup's own focusable children and lets Escape close it, same
    // pattern as donate_popup_alternative.js / wcag.js's modal fix.
    document.addEventListener('keydown', function (event) {
        if (!container.classList.contains('show')) {
            return;
        }

        if (event.key === 'Escape') {
            closePopup();
            return;
        }

        if (event.key !== 'Tab') {
            return;
        }

        var focusable = container.querySelectorAll(
            'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );
        if (focusable.length === 0) {
            return;
        }

        var first = focusable[0];
        var last = focusable[focusable.length - 1];

        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
        } else if (!container.contains(document.activeElement)) {
            event.preventDefault();
            first.focus();
        }
    });
});

function closePopup() {
    document.getElementById('popup-container').classList.remove('show');
    document.getElementById('popup-backdrop').classList.remove('show');
    Cookies.set('popupShown', 'true', { expires: 1 });
}
