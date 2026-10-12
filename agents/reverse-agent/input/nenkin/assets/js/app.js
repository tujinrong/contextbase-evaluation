(() => {
    "use strict";

    const modalOpeners = new WeakMap();

    function toHalfWidthDigits(value) {
        return String(value ?? "").replace(/[\uFF10-\uFF19]/g, (character) =>
            String.fromCharCode(character.charCodeAt(0) - 0xfee0));
    }

    function normalizeDigits(value) {
        return toHalfWidthDigits(value).replace(/\D/g, "");
    }

    function normalizeDigitsInput(input) {
        if (!(input instanceof HTMLInputElement) && !(input instanceof HTMLTextAreaElement)) {
            return;
        }

        const before = input.value;
        const normalized = normalizeDigits(before);
        if (before === normalized) {
            return;
        }

        const selectionStart = input.selectionStart ?? before.length;
        const digitsBeforeCaret = normalizeDigits(before.slice(0, selectionStart)).length;
        input.value = normalized;
        if (document.activeElement === input && typeof input.setSelectionRange === "function") {
            input.setSelectionRange(digitsBeforeCaret, digitsBeforeCaret);
        }

        input.dispatchEvent(new Event("change", { bubbles: true }));
    }

    function bindDigitsOnly(root) {
        root.querySelectorAll("[data-digits-only]").forEach((input) => {
            if (!(input instanceof HTMLInputElement) || input.dataset.digitsOnlyBound === "true") {
                return;
            }

            input.dataset.digitsOnlyBound = "true";
            input.inputMode ||= "numeric";
            input.addEventListener("input", () => normalizeDigitsInput(input));
            input.addEventListener("blur", () => normalizeDigitsInput(input));
            input.addEventListener("focus", () => {
                if (!input.readOnly && !input.disabled && input.value) {
                    requestAnimationFrame(() => input.select());
                }
            });
            normalizeDigitsInput(input);
        });
    }

    function bindTextNormalization(root) {
        root.querySelectorAll("[data-trim], [data-uppercase]").forEach((input) => {
            if (!(input instanceof HTMLInputElement) && !(input instanceof HTMLTextAreaElement)) {
                return;
            }
            if (input.dataset.textNormalizationBound === "true") {
                return;
            }

            input.dataset.textNormalizationBound = "true";
            input.addEventListener("blur", () => {
                let value = input.value;
                if (input.hasAttribute("data-trim")) {
                    value = value.trim();
                }
                if (input.hasAttribute("data-uppercase")) {
                    value = value.toUpperCase();
                }
                if (input.value !== value) {
                    input.value = value;
                    input.dispatchEvent(new Event("change", { bubbles: true }));
                }
            });
        });
    }

    function modalById(id) {
        if (!id) {
            return null;
        }
        const modal = document.getElementById(id);
        return modal instanceof HTMLElement ? modal : null;
    }

    function modalForElement(element) {
        if (!(element instanceof Element)) {
            return null;
        }
        const ownModal = element.closest("[data-modal]");
        if (ownModal instanceof HTMLElement) {
            return ownModal;
        }
        return modalById(element.getAttribute("data-modal-close") || "");
    }

    function focusFirstControl(modal) {
        const requested = modal.querySelector("[data-modal-initial-focus]");
        const fallback = modal.querySelector(
            "button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])");
        const target = requested || fallback;
        if (target instanceof HTMLElement) {
            requestAnimationFrame(() => target.focus());
        }
    }

    function openModal(modalOrId, opener = null) {
        const modal = typeof modalOrId === "string" ? modalById(modalOrId) : modalOrId;
        if (!(modal instanceof HTMLElement)) {
            return false;
        }

        if (opener instanceof HTMLElement) {
            modalOpeners.set(modal, opener);
        }
        modal.hidden = false;
        modal.setAttribute("aria-hidden", "false");
        document.body.classList.add("modal-open");
        const bodyClass = modal.dataset.modalBodyClass;
        if (bodyClass) {
            document.body.classList.add(bodyClass);
        }
        focusFirstControl(modal);
        return true;
    }

    function closeModal(modalOrId) {
        const modal = typeof modalOrId === "string" ? modalById(modalOrId) : modalOrId;
        if (!(modal instanceof HTMLElement)) {
            return false;
        }

        modal.hidden = true;
        modal.setAttribute("aria-hidden", "true");
        const bodyClass = modal.dataset.modalBodyClass;
        if (bodyClass) {
            document.body.classList.remove(bodyClass);
        }
        if (!document.querySelector("[data-modal]:not([hidden])")) {
            document.body.classList.remove("modal-open");
        }
        const opener = modalOpeners.get(modal);
        if (opener instanceof HTMLElement && opener.isConnected) {
            requestAnimationFrame(() => opener.focus());
        }
        return true;
    }

    function bindModalControls(root) {
        root.querySelectorAll("[data-modal-open]").forEach((button) => {
            if (!(button instanceof HTMLElement) || button.dataset.modalOpenBound === "true") {
                return;
            }
            button.dataset.modalOpenBound = "true";
            button.addEventListener("click", () => openModal(button.getAttribute("data-modal-open") || "", button));
        });

        root.querySelectorAll("[data-modal-close]").forEach((button) => {
            if (!(button instanceof HTMLElement) || button.dataset.modalCloseBound === "true") {
                return;
            }
            button.dataset.modalCloseBound = "true";
            button.addEventListener("click", () => closeModal(modalForElement(button)));
        });

        root.querySelectorAll("[data-modal-backdrop]").forEach((backdrop) => {
            if (!(backdrop instanceof HTMLElement) || backdrop.dataset.modalBackdropBound === "true") {
                return;
            }
            backdrop.dataset.modalBackdropBound = "true";
            backdrop.addEventListener("click", () => closeModal(modalForElement(backdrop)));
        });
    }

    function bindCommonButtons(root) {
        root.querySelectorAll("[data-print]").forEach((button) => {
            if (!(button instanceof HTMLElement) || button.dataset.printBound === "true") {
                return;
            }
            button.dataset.printBound = "true";
            button.addEventListener("click", () => window.print());
        });
    }

    function bind(root = document) {
        bindDigitsOnly(root);
        bindTextNormalization(root);
        bindModalControls(root);
        bindCommonButtons(root);
    }

    document.addEventListener("keydown", (event) => {
        if (event.key !== "Escape") {
            return;
        }
        const openModals = document.querySelectorAll("[data-modal]:not([hidden])");
        const modal = openModals.item(openModals.length - 1);
        if (modal instanceof HTMLElement) {
            event.preventDefault();
            closeModal(modal);
        }
    });

    window.nenkinApp = {
        bind,
        bindDigitsOnly,
        closeModal,
        normalizeDigits,
        openModal,
        toHalfWidthDigits
    };

    // Keep the .NET migration helper name available while JSP pages are converted.
    window.jsbrmsBindDigitsOnly = bindDigitsOnly;

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => bind(document));
    } else {
        bind(document);
    }
})();
