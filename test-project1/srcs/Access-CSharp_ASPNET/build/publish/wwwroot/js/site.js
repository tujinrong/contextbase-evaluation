"use strict";

// Web edit state survives server validation without coupling field changes to
// whole-page POSTs. Only rendered controls participate in the raw baseline.
document.querySelectorAll("form[data-track-changes]").forEach(form => {
    const original = form.dataset.draftBaseline ? JSON.parse(form.dataset.draftBaseline) : null;
    const serialize = () => JSON.stringify(Array.from(new FormData(form).entries()).filter(([name]) => name !== "__RequestVerificationToken"));
    const initial = serialize();
    let changed = false;
    let submitted = false;
    const syncDirty = () => {
        changed = original ? Object.entries(original).some(([name, value]) => {
            const field = form.elements.namedItem(name);
            return field ? String(field.value ?? "") !== value : false;
        }) : serialize() !== initial;
        form.dataset.dirty = changed ? "true" : "false";
        const state = form.querySelector("[data-save-state]");
        if (state && !form.querySelector("fieldset[disabled]")) state.textContent = changed ? "未保存の変更があります" : "未変更";
    };
    syncDirty();
    window.addEventListener("pageshow", () => { submitted = false; syncDirty(); });
    form.addEventListener("input", syncDirty);
    form.addEventListener("change", syncDirty);
    form.addEventListener("submit", event => {
        if (form.dataset.optionsState === "loading") {
            event.preventDefault();
            const status = form.querySelector("[data-options-status]");
            if (status) status.textContent = "候補を取得しています。少し待ってから保存してください。";
            return;
        }
        if (event.defaultPrevented) return;
        submitted = true;
    });
    window.addEventListener("beforeunload", event => {
        if (!changed || submitted) return;
        event.preventDefault(); event.returnValue = "";
    });
    form.querySelectorAll("[data-discard-confirm]").forEach(control => {
        control.addEventListener("click", event => {
            syncDirty();
            const message = control.dataset.discardConfirm === "reload"
                ? "最新情報を取得すると、入力中の変更は破棄されます。続けますか。"
                : "未保存の変更を破棄して一覧に戻りますか。";
            if (changed && !window.confirm(message)) event.preventDefault();
            else if (control.tagName === "A" && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey) submitted = true;
        });
    });

    if (!form.matches("[data-editor-form]")) return;
    let pending;
    let requestId = 0;
    const status = form.querySelector("[data-options-status]");
    const classSelect = form.elements.namedItem("Input.ClassId");
    const endDate = form.elements.namedItem("Input.EnrollmentEndDate");
    const updateOptions = async () => {
        const currentRequest = ++requestId;
        pending?.abort();
        const abort = new AbortController(); pending = abort;
        const enrollment = form.elements.namedItem("Input.EnrollmentStatusCode");
        if (endDate) {
            endDate.readOnly = ["01", "02"].includes(enrollment?.value);
            if (endDate.readOnly) endDate.value = "";
            syncDateHints();
        }
        const payload = new FormData();
        const keys = ["__RequestVerificationToken", "Input.Id", "Input.ExpectedVersion", "Input.SnapshotToken", "Input.SchoolYear", "Input.GradeCode", "Input.EnrollmentStatusCode", "Input.ClassId", "Input.AdmissionDate", "Input.EnrollmentEndDate"];
        keys.forEach(name => { const field = form.elements.namedItem(name); if (field) payload.set(name, field.value ?? ""); });
        form.dataset.optionsState = "loading"; form.setAttribute("aria-busy", "true");
        status?.classList.remove("error");
        if (status) status.textContent = "利用できるクラスと所属人数を取得しています…";
        let recoveryMessage = "候補を取得できませんでした。入力内容は保持しています。通信を確認して、年度・学年を選び直してください。";
        try {
            const response = await fetch(form.dataset.optionsUrl, { method: "POST", body: payload, credentials: "same-origin", headers: { "Accept": "application/json" }, signal: abort.signal });
            const data = response.headers.get("Content-Type")?.includes("application/json") ? await response.json().catch(() => null) : null;
            if (currentRequest !== requestId) return;
            if (!response.ok) { if (typeof data?.message === "string") recoveryMessage = data.message; throw new Error("request-failed"); }
            if (!Array.isArray(data?.classes)) throw new Error("invalid-response");
            const selected = classSelect?.value ?? "";
            if (classSelect) {
                classSelect.replaceChildren(new Option("未選択", ""), ...data.classes.map(item => new Option(item.text, item.value)));
                classSelect.value = data.clearClass ? "" : selected;
            }
            if (data.clearEndDate && endDate) { endDate.value = ""; endDate.readOnly = true; syncDateHints(); }
            const capacity = form.querySelector("[data-capacity]"); if (capacity) capacity.textContent = data.capacity;
            if (status) status.textContent = data.message || "候補を更新しました。";
            form.dataset.optionsState = "ready";
            syncDirty();
        } catch (error) {
            if (error.name === "AbortError" || currentRequest !== requestId) return;
            form.dataset.optionsState = "error";
            status?.classList.add("error");
            if (status) status.textContent = recoveryMessage;
        } finally {
            if (currentRequest === requestId) form.setAttribute("aria-busy", "false");
        }
    };
    form.querySelectorAll("[data-refresh-candidates]").forEach(input => input.addEventListener("change", updateOptions));
});

// Clear feedback and a busy state prevent accidental repeated POSTs. The server
// still owns authorization, optimistic versions and one-use confirmations.
document.querySelectorAll("form[method='post']").forEach(form => {
    form.addEventListener("submit", event => {
        if (event.defaultPrevented) return;
        if (form.dataset.submitting === "true") { event.preventDefault(); return; }
        form.dataset.submitting = "true"; form.setAttribute("aria-busy", "true");
        const button = event.submitter;
        if (button) { button.setAttribute("aria-disabled", "true"); button.dataset.originalText = button.textContent; button.textContent = "処理中…"; }
    });
});
window.addEventListener("pageshow", () => {
    document.querySelectorAll("form[data-submitting]").forEach(form => {
        delete form.dataset.submitting; form.setAttribute("aria-busy", "false");
        form.querySelectorAll("[data-original-text]").forEach(button => { button.textContent = button.dataset.originalText; button.removeAttribute("aria-disabled"); delete button.dataset.originalText; });
    });
});

// A date-only ISO value is never interpreted in the browser's local timezone.
// One calendar input owns the value; Japanese era text is a synchronized hint.
const japaneseDateFormat = new Intl.DateTimeFormat("ja-JP-u-ca-japanese", { era: "long", year: "numeric", month: "long", day: "numeric", timeZone: "UTC" });
const dateHints = Array.from(document.querySelectorAll("[data-birth-date],input[data-japanese-date]"), input => {
    const hint = input.matches("[data-birth-date]") ? document.querySelector("[data-birth-hint]")
        : Array.from(document.querySelectorAll("[data-japanese-date-for]")).find(item => item.dataset.japaneseDateFor === input.id);
    return { input, hint };
}).filter(item => item.hint);
function syncDateHints() {
    dateHints.forEach(({ input, hint }) => {
        if (!input.value) { hint.textContent = input.validity.badInput ? "日付を確認" : input.required ? "日付を選択" : "未設定"; return; }
        const date = /^\d{4}-\d{2}-\d{2}$/.test(input.value) ? new Date(input.value + "T00:00:00Z") : null;
        if (!date || Number.isNaN(date.getTime()) || date.toISOString().slice(0, 10) !== input.value) { hint.textContent = "日付を確認"; return; }
        hint.textContent = japaneseDateFormat.format(date);
    });
}
dateHints.forEach(({ input }) => {
    input.addEventListener("input", syncDateHints);
    input.addEventListener("change", syncDateHints);
    input.form?.addEventListener("reset", () => queueMicrotask(syncDateHints));
});
window.addEventListener("pageshow", syncDateHints);
syncDateHints();
const errorSummary = document.querySelector("[data-error-summary].validation-summary-errors");
if (errorSummary) { errorSummary.focus(); document.querySelectorAll(".input-validation-error").forEach(field => field.setAttribute("aria-invalid", "true")); }

// A search return restores only that browser tab/context's table position.
const results = document.querySelector("[data-search-context]");
if (results) {
    const key = "access-rebuilder-search:" + results.dataset.searchContext;
    let selected = "";
    const savePosition = () => { try { sessionStorage.setItem(key, JSON.stringify({ top: results.scrollTop, selected })); } catch { } };
    if (results.dataset.restoreScroll === "true") {
        try { const saved = JSON.parse(sessionStorage.getItem(key) ?? "null"); if (saved) { selected = String(saved.selected ?? ""); requestAnimationFrame(() => { results.scrollTop = Number(saved.top) || 0; results.querySelectorAll("tr[data-student-id]").forEach(row => row.classList.toggle("selected", row.dataset.studentId === selected)); }); } } catch { }
    } else { try { sessionStorage.removeItem(key); } catch { } }
    results.addEventListener("scroll", savePosition, { passive: true });
    results.querySelectorAll("tr[data-student-id]").forEach(row => row.addEventListener("click", () => { selected = row.dataset.studentId; results.querySelectorAll("tr[data-student-id]").forEach(other => other.classList.toggle("selected", other === row)); savePosition(); }));
}

// Master browsing stays on one Web page; filtering is presentation-only.
document.querySelectorAll("[data-tab-button]").forEach(button => button.addEventListener("click", () => {
    document.querySelectorAll("[data-tab-button]").forEach(other => other.setAttribute("aria-selected", String(other === button)));
    document.querySelectorAll("[data-tab-panel]").forEach(panel => panel.hidden = panel.id !== button.dataset.tabButton);
}));
document.querySelectorAll("[data-table-filter]").forEach(input => input.addEventListener("input", () => {
    const query = input.value.toLocaleLowerCase(); const table = document.getElementById(input.dataset.tableFilter);
    table?.querySelectorAll("tbody tr").forEach(row => row.hidden = !row.textContent.toLocaleLowerCase().includes(query));
}));
