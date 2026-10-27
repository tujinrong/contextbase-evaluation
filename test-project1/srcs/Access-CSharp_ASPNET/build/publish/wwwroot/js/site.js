"use strict";

// Keep browser edits local until a POST succeeds; leaving an edited form follows
// the source application's discard-confirmation interaction.
document.querySelectorAll("form[data-track-changes]").forEach(form => {
    // Raw values, not normalized values, determine whether the original edit
    // snapshot changed. The same baseline survives candidate/error redraws.
    const original = form.dataset.draftBaseline ? JSON.parse(form.dataset.draftBaseline) : null;
    const serialize = () => JSON.stringify(Array.from(new FormData(form).entries()).filter(([name]) => name !== "__RequestVerificationToken"));
    const initial = serialize();
    let changed = false;
    let submitted = false;
    const syncDirty = () => {
        changed = original ? Object.entries(original).some(([name, value]) => {
            const field = form.elements.namedItem(name);
            return String(field?.value ?? "") !== value;
        }) : serialize() !== initial;
        form.dataset.dirty = changed ? "true" : "false";
    };
    syncDirty();
    form.addEventListener("input", syncDirty);
    form.addEventListener("change", syncDirty);
    form.addEventListener("submit", () => { submitted = true; });
    window.addEventListener("beforeunload", event => {
        if (!changed || submitted) return;
        event.preventDefault();
        event.returnValue = "";
    });
    document.querySelectorAll("[data-discard-confirm]").forEach(control => {
        control.addEventListener("click", event => {
            syncDirty();
            const message = control.dataset.discardConfirm === "reload"
                ? "最新情報を再読み込みすると入力中の変更は破棄されます。続行しますか。"
                : control.dataset.discardConfirm === "reset" ? "入力内容を取り消しますか。" : "変更内容を破棄して戻りますか。";
            if (changed && !window.confirm(message)) event.preventDefault();
            else submitted = true;
        });
    });
    form.querySelectorAll("[data-refresh-candidates]").forEach(input => {
        input.addEventListener("change", () => {
            if (input.name === "Input.EnrollmentStatusCode") {
                const endDate = form.querySelector("[name='Input.EnrollmentEndDate']");
                if (endDate && ["01", "02"].includes(input.value)) endDate.value = "";
            }
            const refresh = form.querySelector("[data-candidate-submit]");
            if (refresh) form.requestSubmit(refresh);
        });
    });
});

// Refresh after edit/save reuses the applied context and restores its list
// position. A new SEARCH or CLEAR explicitly starts from the top.
const results = document.querySelector("[data-search-context]");
if (results) {
    const key = "access-rebuilder-search:" + results.dataset.searchContext;
    let selected = "";
    const savePosition = () => {
        try { sessionStorage.setItem(key, JSON.stringify({ top: results.scrollTop, selected })); } catch { /* Storage may be disabled. */ }
    };
    if (results.dataset.restoreScroll === "true") {
        try {
            const saved = JSON.parse(sessionStorage.getItem(key) ?? "null");
            if (saved) {
                selected = String(saved.selected ?? "");
                requestAnimationFrame(() => {
                    results.scrollTop = Number(saved.top) || 0;
                    results.querySelectorAll("tr[data-student-id]").forEach(row => row.classList.toggle("selected", row.dataset.studentId === selected));
                });
            }
        } catch { /* Invalid or unavailable session storage starts at the top. */ }
    } else {
        try { sessionStorage.removeItem(key); } catch { /* Storage may be disabled. */ }
    }
    results.addEventListener("scroll", savePosition, { passive: true });
    results.querySelectorAll("tr[data-student-id]").forEach(row => {
        row.addEventListener("click", () => {
            selected = row.dataset.studentId;
            results.querySelectorAll("tr[data-student-id]").forEach(other => other.classList.toggle("selected", other === row));
            savePosition();
        });
    });
}
