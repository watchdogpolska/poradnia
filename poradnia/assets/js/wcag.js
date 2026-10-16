// WCAG-mode-only script. Loaded in base.html only when ui_mode == "wcag",
// after script.min.js (needs Bootstrap/HTMX already loaded to hook their
// events).

// F004: fix the attachment-text modal's focus trap/Escape handling.
//
// base.html's own inline script already drives this modal through
// bootstrap.Modal's real API (.show()/.hide()), but that alone isn't
// enough here: Bootstrap 5's FocusTrap only recovers an escaped Tab via a
// 'focusin' event, and this modal sits right at the end of the page's
// focusable DOM (nothing comes after #attachment-text-modal-container in
// base.html). Tabbing past its one focusable child (the close button)
// moves focus to <body> - a state the browser reaches without ever firing
// 'focusin', so Bootstrap's own trap never gets a chance to correct it.
// Confirmed by reproducing this in isolation (a minimal page with just
// Bootstrap + this exact modal markup, outside the Django app) before
// writing this fix - it's a real gap in Bootstrap's FocusTrap for a modal
// with very few focusable children near the end of the document, not a
// one-off app bug. Once focus has left the modal this way, Escape also
// stops working, since Bootstrap's own Escape listener is bound to the
// modal element itself and a keydown on <body> never reaches it.
//
// This adds a redundant, explicit Tab-wrap + always-on Escape handler
// scoped to this one modal, layered on top of (not instead of) Bootstrap's
// own handling, plus an explicit focus-return to whichever attachment
// button opened the modal.
(function () {
    var MODAL_ID = "attachmentTextModal";
    var TRIGGER_SELECTOR = '[hx-target="#attachment-text-modal-container"]';
    var lastTrigger = null;

    document.addEventListener("click", function (event) {
        var trigger = event.target.closest(TRIGGER_SELECTOR);
        if (trigger) {
            lastTrigger = trigger;
        }
    });

    document.addEventListener("hidden.bs.modal", function (event) {
        if (event.target.id === MODAL_ID && lastTrigger) {
            lastTrigger.focus();
        }
    });

    function getModal() {
        return document.getElementById(MODAL_ID);
    }

    function isOpen(modal) {
        return !!modal && modal.classList.contains("show");
    }

    document.addEventListener("keydown", function (event) {
        var modal = getModal();
        if (!isOpen(modal)) {
            return;
        }

        if (event.key === "Escape") {
            bootstrap.Modal.getOrCreateInstance(modal).hide();
            return;
        }

        if (event.key !== "Tab") {
            return;
        }

        var focusable = modal.querySelectorAll(
            'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
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
        } else if (!modal.contains(document.activeElement)) {
            event.preventDefault();
            first.focus();
        }
    });
})();
