jQuery(function() {
    var alreadyDonated = Cookies.get('alreadyDonated');
    var popupShown = Cookies.get('popupShown');
    // // for debug purposes
    // if (Cookies.get('popupShown')) {
    //     Cookies.remove('popupShown');
    //     Cookies.remove('alreadyDonated');
    // };
    if (!(alreadyDonated || popupShown)) {
        // Show the popup if the 'popupShown' or 'alreadyDonated' cookie is not set
        $('#popup-container').fadeIn();
    }
});

function closePopup() {
    $('#popup-container').fadeOut();
    // Set a cookie to remember that the popup has been shown, expires in 1 day
    Cookies.set('popupShown', 'true', { expires: 1 });
}

document.getElementById('alreadyDonated').addEventListener('change', function() {
    if (this.checked) {
        Cookies.set('alreadyDonated', 'true', { expires: 60 }); // expires in 60 days
    } else {
        Cookies.remove('alreadyDonated');
    }
});
