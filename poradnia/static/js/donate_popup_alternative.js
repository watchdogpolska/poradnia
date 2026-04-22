document.addEventListener('DOMContentLoaded', function () {
    var altAlreadyDonated = Cookies.get('altAlreadyDonated');
    var altPopupShown = Cookies.get('altPopupShown');
    if (!(altAlreadyDonated || altPopupShown)) {
        document.getElementById('alt-popup-container').classList.add('show');
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
});

function closeAltPopup() {
    document.getElementById('alt-popup-container').classList.remove('show');
    Cookies.set('altPopupShown', 'true', { expires: 1 });
}
