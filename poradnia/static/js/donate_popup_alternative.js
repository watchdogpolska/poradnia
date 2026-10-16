document.addEventListener('DOMContentLoaded', function () {
    var altAlreadyDonated = Cookies.get('altAlreadyDonated');
    var altPopupShown = Cookies.get('altPopupShown');
    var container = document.getElementById('alt-popup-container');
    var backdrop = document.getElementById('alt-popup-backdrop');

    if (!(altAlreadyDonated || altPopupShown)) {
        container.classList.add('show');
        backdrop.classList.add('show');
        container.focus();
    }

    var checkbox = document.getElementById('altAlreadyDonated');
    if (checkbox) {
        checkbox.addEventListener('change', function () {
            if (this.checked) {
                Cookies.set('altAlreadyDonated', 'true', { expires: 30 });
            } else {
                Cookies.remove('altAlreadyDonated');
            }
        });
    }

    // Blocking the rest of the page with #alt-popup-backdrop (see the
    // template's CSS) only stops mouse clicks - without this, a keyboard
    // user could still Tab straight past the popup into content that's
    // visually hidden behind the backdrop. Traps Tab/Shift+Tab within the
    // popup's own focusable children and lets Escape close it, same
    // pattern as the attachment-text modal fix in wcag.js.
    document.addEventListener('keydown', function (event) {
        if (!container.classList.contains('show')) {
            return;
        }

        if (event.key === 'Escape') {
            closeAltPopup();
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

function closeAltPopup() {
    document.getElementById('alt-popup-container').classList.remove('show');
    document.getElementById('alt-popup-backdrop').classList.remove('show');
    Cookies.set('altPopupShown', 'true', { expires: 1 });
}
