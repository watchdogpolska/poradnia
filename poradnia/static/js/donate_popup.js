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

    function adjustPopupContainer() {
        if ($(window).width() < 1000) {
            $('#popup-container').css({
                'white-space': 'normal',
                'overflow': 'auto',
                'max-height': '90vh',
                'max-width': '90vw'
            });
        } else {
            $('#popup-container').css('white-space', 'nowrap');
        }
    }

    // Call adjustPopupContainer when the document is ready and when the window is resized
    adjustPopupContainer();
    $(window).on('resize', adjustPopupContainer);

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
