jQuery(function() {
    var altAlreadyDonated = Cookies.get('altAlreadyDonated');
    var altPopupShown = Cookies.get('altPopupShown');
    // // for debug purposes
    // if (Cookies.get('altPopupShown')) {
    //     Cookies.remove('altPopupShown');
    //     Cookies.remove('altAlreadyDonated');
    // };
    if (!(altAlreadyDonated || altPopupShown)) {
        // Show the popup if the 'altPopupShown' or 'altAlreadyDonated' cookie is not set
        $('#alt-popup-container').fadeIn();
    }

    function adjustAltPopupContainer() {
        if ($(window).width() < 1000) {
            $('#alt-popup-container').css({
                'white-space': 'normal',
                'overflow': 'auto',
                'max-height': '90vh',
                'max-width': '90vw'
            });
        } else {
            $('#alt-popup-container').css('white-space', 'nowrap');
        }
    }

    // Call adjustAltPopupContainer when the document is ready and when the window is resized
    adjustAltPopupContainer();
    $(window).on('resize', adjustAltPopupContainer);

});

function closeAltPopup() {
    $('#alt-popup-container').fadeOut();
    // Set a cookie to remember that the popup has been shown, expires in 1 days (shorter than main popup)
    Cookies.set('altPopupShown', 'true', { expires: 1 });
}

document.getElementById('altAlreadyDonated').addEventListener('change', function() {
    if (this.checked) {
        Cookies.set('altAlreadyDonated', 'true', { expires: 30 }); // expires in 30 days (shorter than main popup)
    } else {
        Cookies.remove('altAlreadyDonated');
    }
});