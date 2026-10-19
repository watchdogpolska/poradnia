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

// DAL ("Alight") autocomplete widget: missing role/aria-controls/names.
//
// django-autocomplete-light's dal_alight package (a stock pinned PyPI
// release, not a Piotr-owned fork - requirements/base.txt) renders
// <autocomplete-select-input> custom elements. Their connectedCallback()
// (read directly from site-packages/dal_alight/static/dal_alight/
// autocomplete-light.js) sets aria-haspopup="listbox", aria-autocomplete=
// "list" and aria-expanded on the inner <input slot="input">, but never
// sets role="combobox" - required by ARIA for those three attributes to
// be valid on an element whose implicit role is otherwise plain "textbox"
// (axe-core: aria-allowed-attr). That same input also has no accessible
// name of its own: crispy-forms renders a real <label for="id_X"> next to
// every one of these widgets (confirmed across every usage site in this
// app - case/letter/advice filters, permission forms), but for="id_X"
// targets the *original* <select id="id_X"> dal_alight hides and
// replaces, not the visible text input users actually type into
// (axe-core: aria-input-field-name). Adding role="combobox" then exposed
// a second, consequential gap: ARIA requires a combobox to carry
// aria-controls pointing at the popup it owns (axe-core:
// aria-required-attr), but boxBuild() creates that popup (a bare
// <div role="listbox">, never nested inside the custom element - it's
// appended straight to <body> on first open) without ever giving it an
// id, so there's nothing to point aria-controls at and the box itself
// has no name either (also aria-input-field-name, on the box this time).
//
// No Django template to override here - dal_alight ships no templates at
// all, only this JS (confirmed by listing the installed package's files).
// The custom element finishes its async upgrade at an unpredictable time
// (connectedCallback retries every 100ms for up to 2s waiting for its
// children to exist) and sets its own data-bound="true" marker once
// done - that's the one reliable "it's ready" signal, so this patches on
// that signal via MutationObserver rather than guessing a fixed delay.
// The popup box has no such marker and isn't created until first opened
// (boxBuild(), called lazily from draw()) - watched separately below via
// a childList observer on <body>, identifying which input a newly
// -appended box belongs to via the one input draw() just set
// aria-expanded="true" on in the same synchronous call (confirmed by
// reading draw()'s only two call sites - always a direct, synchronous
// reaction to that same instance's own input/keyboard event, never a
// decoupled/deferred call, so at most one input can be mid-open at once).
(function () {
    var boxIdCounter = 0;

    function labelTextFor(customEl) {
        var wrapper = customEl.closest('[id^="div_id_"]');
        var label = wrapper && wrapper.querySelector("label");
        return label ? label.textContent.trim() : null;
    }

    function patchInput(customEl) {
        var input = customEl.querySelector('[slot="input"]');
        if (!input || input.tagName !== "INPUT" || input.hasAttribute("role")) {
            return;
        }
        input.setAttribute("role", "combobox");
        var text = labelTextFor(customEl);
        if (text) {
            input.setAttribute("aria-label", text);
        }
    }

    function patchBox(box) {
        if (box.hasAttribute("aria-label")) {
            return;
        }
        var input = document.querySelector(
            'autocomplete-select-input input[aria-expanded="true"]'
        );
        if (!input) {
            return;
        }
        var id = "wcag-dal-box-" + ++boxIdCounter;
        box.setAttribute("id", id);
        input.setAttribute("aria-controls", id);
        var text = input.getAttribute("aria-label");
        if (text) {
            box.setAttribute("aria-label", text);
        }
    }

    document
        .querySelectorAll('autocomplete-select-input[data-bound="true"]')
        .forEach(patchInput);

    new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
            var target = mutation.target;
            if (
                target.tagName === "AUTOCOMPLETE-SELECT-INPUT" &&
                target.getAttribute("data-bound") === "true"
            ) {
                patchInput(target);
            }
        });
    }).observe(document.body, {
        attributes: true,
        attributeFilter: ["data-bound"],
        subtree: true,
    });

    new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
            mutation.addedNodes.forEach(function (node) {
                if (
                    node.nodeType === 1 &&
                    node.classList.contains("autocomplete-light-box")
                ) {
                    patchBox(node);
                }
            });
        });
    }).observe(document.body, { childList: true });
})();
