document.addEventListener('DOMContentLoaded', function () {
    var alreadyDonated = Cookies.get('alreadyDonated');
    var popupShown = Cookies.get('popupShown');
    if (!(alreadyDonated || popupShown)) {
        document.getElementById('popup-container').classList.add('show');
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
});

function closePopup() {
    document.getElementById('popup-container').classList.remove('show');
    Cookies.set('popupShown', 'true', { expires: 1 });
}
