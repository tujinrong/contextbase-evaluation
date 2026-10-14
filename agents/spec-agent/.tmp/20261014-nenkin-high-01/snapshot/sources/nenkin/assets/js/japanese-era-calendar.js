(() => {
    const eras = [
        { symbol: "R", shortName: "令", fullName: "令和", start: Date.UTC(2019, 4, 1), end: null, startYear: 2019 },
        { symbol: "H", shortName: "平", fullName: "平成", start: Date.UTC(1989, 0, 8), end: Date.UTC(2019, 3, 30), startYear: 1989 },
        { symbol: "S", shortName: "昭", fullName: "昭和", start: Date.UTC(1926, 11, 25), end: Date.UTC(1989, 0, 7), startYear: 1926 },
        { symbol: "T", shortName: "大", fullName: "大正", start: Date.UTC(1912, 6, 30), end: Date.UTC(1926, 11, 24), startYear: 1912 },
        { symbol: "M", shortName: "明", fullName: "明治", start: Date.UTC(1868, 8, 8), end: Date.UTC(1912, 6, 29), startYear: 1868 }
    ];
    const eraPattern = "(明治|大正|昭和|平成|令和|明|大|昭|平|令|M|T|S|H|R)";
    const calendarClass = "era-calendar";
    let calendar = null;
    let activeInput = null;
    let visibleYear = 0;
    let visibleMonth = 0;

    function toHalfWidthDigits(value) {
        return String(value || "")
            .replace(/[\uFF10-\uFF19]/g, (char) => String.fromCharCode(char.charCodeAt(0) - 0xfee0))
            .replace(/\u3000/g, " ");
    }

    function createUtcDate(year, month, day) {
        const date = new Date(Date.UTC(year, month - 1, day));
        if (date.getUTCFullYear() !== year || date.getUTCMonth() !== month - 1 || date.getUTCDate() !== day) {
            return null;
        }

        return date;
    }

    function parseIsoDate(value) {
        const match = String(value || "").trim().match(/^(\d{4})-(\d{2})-(\d{2})/);
        return match ? createUtcDate(Number(match[1]), Number(match[2]), Number(match[3])) : null;
    }

    function formatIsoDate(date) {
        return [
            date.getUTCFullYear(),
            String(date.getUTCMonth() + 1).padStart(2, "0"),
            String(date.getUTCDate()).padStart(2, "0")
        ].join("-");
    }

    function calendarModeFor(inputOrMode) {
        const value = typeof inputOrMode === "string"
            ? inputOrMode
            : inputOrMode instanceof HTMLElement
                ? inputOrMode.dataset.eraCalendarMode
                : "";
        return value === "western" || value === "gregorian" ? "western" : "japanese";
    }

    function formatWesternDate(date) {
        return [
            date.getUTCFullYear(),
            String(date.getUTCMonth() + 1).padStart(2, "0"),
            String(date.getUTCDate()).padStart(2, "0")
        ].join("/");
    }

    function resolveEra(date) {
        const time = date.getTime();
        return eras.find((era) => time >= era.start && (era.end === null || time <= era.end)) || null;
    }

    function resolveEraSymbol(value) {
        const text = String(value || "").toUpperCase();
        return eras.find((era) =>
            era.symbol === text ||
            era.shortName === value ||
            era.fullName === value) || null;
    }

    function formatEraDate(date) {
        const era = resolveEra(date);
        const year = date.getUTCFullYear();
        const month = date.getUTCMonth() + 1;
        const day = date.getUTCDate();
        if (!era) {
            return formatWesternDate(date);
        }

        const eraYear = year - era.startYear + 1;
        return `${era.symbol} ${String(eraYear).padStart(2, "0")}/${String(month).padStart(2, "0")}/${String(day).padStart(2, "0")}`;
    }

    function formatDisplayDate(date, inputOrMode) {
        return calendarModeFor(inputOrMode) === "western" ? formatWesternDate(date) : formatEraDate(date);
    }

    function formatEraMonth(date) {
        const era = resolveEra(date);
        const month = date.getUTCMonth() + 1;
        if (!era) {
            return `${date.getUTCFullYear()}年 ${month}月`;
        }

        return `${era.fullName}${date.getUTCFullYear() - era.startYear + 1}年 ${month}月`;
    }

    function formatWesternMonth(date) {
        return `${date.getUTCFullYear()}年 ${date.getUTCMonth() + 1}月`;
    }

    function formatCalendarMonth(date, inputOrMode) {
        return calendarModeFor(inputOrMode) === "western" ? formatWesternMonth(date) : formatEraMonth(date);
    }

    function formatCalendarSubMonth(date, inputOrMode) {
        return calendarModeFor(inputOrMode) === "western" ? formatEraMonth(date) : formatWesternMonth(date);
    }

    function buildEraDate(eraText, eraYearText, monthText, dayText) {
        const era = resolveEraSymbol(eraText);
        const eraYear = eraYearText === "元" ? 1 : Number(eraYearText);
        if (!era || !Number.isInteger(eraYear) || eraYear <= 0) {
            return null;
        }

        const date = createUtcDate(era.startYear + eraYear - 1, Number(monthText), Number(dayText));
        if (!date || date.getTime() < era.start || (era.end !== null && date.getTime() > era.end)) {
            return null;
        }

        return date;
    }

    function parseAccessEraDate(value) {
        const text = toHalfWidthDigits(value).trim();
        if (!text) {
            return null;
        }

        const compact = text.replace(/\s+/g, "");
        const compactWestern = compact.match(/^(\d{4})(\d{2})(\d{2})$/);
        if (compactWestern) {
            return createUtcDate(Number(compactWestern[1]), Number(compactWestern[2]), Number(compactWestern[3]));
        }

        const compactEra = compact.match(new RegExp(`^${eraPattern}(元|\\d{1,2})(\\d{2})(\\d{2})$`, "i"));
        if (compactEra) {
            return buildEraDate(compactEra[1], compactEra[2], compactEra[3], compactEra[4]);
        }

        const western = text.match(/^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$/);
        if (western) {
            return createUtcDate(Number(western[1]), Number(western[2]), Number(western[3]));
        }

        const normalized = text
            .replace(/[年月.-]/g, "/")
            .replace(/日/g, "")
            .replace(/\s+/g, " ")
            .trim();
        const eraMatch = normalized.match(new RegExp(`^${eraPattern}\\s*(元|\\d{1,2})/(\\d{1,2})/(\\d{1,2})$`, "i"));
        if (!eraMatch) {
            return null;
        }

        return buildEraDate(eraMatch[1], eraMatch[2], eraMatch[3], eraMatch[4]);
    }

    function formatAccessEraDate(value, inputOrMode = "japanese") {
        const text = String(value || "").trim();
        if (!text) {
            return "";
        }

        const date = parseAccessEraDate(text) || parseIsoDate(text);
        return date ? formatDisplayDate(date, inputOrMode) : text;
    }

    function selectedDateFor(input) {
        const hidden = hiddenInputFor(input);
        const hiddenDate = hidden ? parseIsoDate(hidden.value) || parseAccessEraDate(hidden.value) : null;
        const inputDate = parseAccessEraDate(input.value) || parseIsoDate(input.value);
        const today = new Date();
        return inputDate || hiddenDate || createUtcDate(today.getFullYear(), today.getMonth() + 1, today.getDate());
    }

    function ensureCalendar() {
        if (calendar) {
            return calendar;
        }

        calendar = document.createElement("div");
        calendar.className = calendarClass;
        calendar.hidden = true;
        calendar.setAttribute("role", "dialog");
        calendar.setAttribute("aria-modal", "false");
        document.body.appendChild(calendar);
        calendar.addEventListener("click", handleCalendarClick);
        return calendar;
    }

    function closeCalendar() {
        if (!calendar) {
            return;
        }

        calendar.hidden = true;
        activeInput = null;
    }

    function positionCalendar(input) {
        const popup = ensureCalendar();
        const rect = input.getBoundingClientRect();
        const viewportPadding = 8;
        const availableWidth = Math.max(240, window.innerWidth - (viewportPadding * 2));
        const popupWidth = Math.min(Math.max(rect.width, 286), availableWidth);
        const minimumLeft = window.scrollX + viewportPadding;
        const maximumLeft = window.scrollX + window.innerWidth - popupWidth - viewportPadding;
        const requestedLeft = rect.left + window.scrollX;
        popup.style.left = `${Math.round(Math.max(minimumLeft, Math.min(requestedLeft, maximumLeft)))}px`;
        popup.style.width = `${Math.round(popupWidth)}px`;
        popup.style.minWidth = "0";
        const popupHeight = popup.offsetHeight;
        const belowTop = rect.bottom + window.scrollY + 4;
        const aboveTop = rect.top + window.scrollY - popupHeight - 4;
        const fitsBelow = rect.bottom + popupHeight + 4 <= window.innerHeight - viewportPadding;
        const fitsAbove = rect.top - popupHeight - 4 >= viewportPadding;
        popup.style.top = `${Math.round(!fitsBelow && fitsAbove ? aboveTop : belowTop)}px`;
    }

    function renderCalendar(input) {
        const popup = ensureCalendar();
        const mode = calendarModeFor(input);
        const selectedDate = selectedDateFor(input);
        const firstDate = createUtcDate(visibleYear, visibleMonth + 1, 1);
        const previousMonth = new Date(Date.UTC(visibleYear, visibleMonth - 1, 1));
        const nextMonth = new Date(Date.UTC(visibleYear, visibleMonth + 1, 1));
        const daysInMonth = new Date(Date.UTC(visibleYear, visibleMonth + 1, 0)).getUTCDate();
        const startDay = firstDate.getUTCDay();
        const selectedIso = selectedDate ? formatIsoDate(selectedDate) : "";
        const today = new Date();
        const todayIso = formatIsoDate(createUtcDate(today.getFullYear(), today.getMonth() + 1, today.getDate()));
        let dayHtml = "";

        for (let index = 0; index < startDay; index++) {
            dayHtml += '<span class="era-calendar__empty"></span>';
        }

        for (let day = 1; day <= daysInMonth; day++) {
            const date = createUtcDate(visibleYear, visibleMonth + 1, day);
            const iso = formatIsoDate(date);
            const classes = [
                "era-calendar__day",
                date.getUTCDay() === 0 ? "is-sunday" : "",
                iso === selectedIso ? "is-selected" : "",
                iso === todayIso ? "is-today" : ""
            ].filter(Boolean).join(" ");
            dayHtml += `<button class="${classes}" type="button" data-era-date="${iso}" aria-label="${formatDisplayDate(date, mode)}"><span>${day}</span></button>`;
        }

        const monthTitle = formatCalendarMonth(firstDate, mode);
        const monthSubTitle = formatCalendarSubMonth(firstDate, mode);
        const monthSubTitleHtml = monthSubTitle && monthSubTitle !== monthTitle
            ? `<span>${monthSubTitle}</span>`
            : "";

        popup.innerHTML = `
            <div class="era-calendar__header">
                <button class="era-calendar__nav" type="button" data-era-month="${previousMonth.getUTCFullYear()}-${previousMonth.getUTCMonth()}" aria-label="前の月">&lt;</button>
                <div class="era-calendar__title">
                    <strong>${monthTitle}</strong>
                    ${monthSubTitleHtml}
                </div>
                <button class="era-calendar__nav" type="button" data-era-month="${nextMonth.getUTCFullYear()}-${nextMonth.getUTCMonth()}" aria-label="次の月">&gt;</button>
            </div>
            <div class="era-calendar__weekdays" aria-hidden="true">
                <span>日</span><span>月</span><span>火</span><span>水</span><span>木</span><span>金</span><span>土</span>
            </div>
            <div class="era-calendar__days">
                ${dayHtml}
            </div>`;
        positionCalendar(input);
    }

    function openCalendar(input) {
        activeInput = input;
        const selectedDate = selectedDateFor(input);
        visibleYear = selectedDate.getUTCFullYear();
        visibleMonth = selectedDate.getUTCMonth();
        renderCalendar(input);
        ensureCalendar().hidden = false;
        positionCalendar(input);
    }

    function hiddenInputFor(input) {
        const hiddenId = input.getAttribute("data-era-hidden-input");
        if (!hiddenId) {
            return null;
        }

        const hidden = document.getElementById(hiddenId);
        return hidden instanceof HTMLInputElement ? hidden : null;
    }

    function displayInputForHidden(hidden) {
        if (!hidden.id) {
            return null;
        }

        const input = document.querySelector(`[data-era-hidden-input="${CSS.escape(hidden.id)}"]`);
        return input instanceof HTMLInputElement ? input : null;
    }

    function syncHiddenFromDisplay(input) {
        const hidden = hiddenInputFor(input);
        if (!hidden) {
            return;
        }

        const text = input.value.trim();
        if (!text) {
            hidden.value = "";
        } else {
            const date = parseAccessEraDate(text) || parseIsoDate(text);
            hidden.value = date ? formatIsoDate(date) : text;
        }

        hidden.dispatchEvent(new Event("input", { bubbles: true }));
        hidden.dispatchEvent(new Event("change", { bubbles: true }));
    }

    function syncDisplayForHidden(hidden) {
        const input = displayInputForHidden(hidden);
        if (!input) {
            return;
        }

        input.value = formatAccessEraDate(hidden.value, input);
    }

    function normalizeDisplayInput(input) {
        const date = parseAccessEraDate(input.value) || parseIsoDate(input.value);
        if (date) {
            input.value = formatDisplayDate(date, input);
        }

        syncHiddenFromDisplay(input);
    }

    function handleCalendarClick(event) {
        const target = event.target instanceof Element ? event.target.closest("button") : null;
        if (!(target instanceof HTMLButtonElement) || !activeInput) {
            return;
        }

        const month = target.getAttribute("data-era-month");
        if (month) {
            const [yearText, monthText] = month.split("-");
            visibleYear = Number(yearText);
            visibleMonth = Number(monthText);
            renderCalendar(activeInput);
            return;
        }

        const iso = target.getAttribute("data-era-date");
        if (!iso) {
            return;
        }

        const selectedInput = activeInput;
        const date = parseIsoDate(iso);
        selectedInput.value = date ? formatDisplayDate(date, selectedInput) : iso;
        syncHiddenFromDisplay(selectedInput);
        selectedInput.dispatchEvent(new Event("input", { bubbles: true }));
        selectedInput.dispatchEvent(new Event("change", { bubbles: true }));
        closeCalendar();
        selectedInput.focus();
    }

    function bindInput(input) {
        if (!(input instanceof HTMLInputElement) || input.dataset.eraCalendarBound === "true") {
            return;
        }

        input.dataset.eraCalendarBound = "true";
        const hidden = hiddenInputFor(input);
        if (hidden && !input.value) {
            input.value = formatAccessEraDate(hidden.value, input);
        } else {
            input.value = formatAccessEraDate(input.value, input);
            syncHiddenFromDisplay(input);
        }

        input.addEventListener("blur", () => normalizeDisplayInput(input));
        input.addEventListener("change", () => normalizeDisplayInput(input));
        input.addEventListener("keydown", (event) => {
            if ((event.altKey && event.key === "ArrowDown") || event.key === "F4") {
                event.preventDefault();
                openCalendar(input);
            }
        });

        hidden?.addEventListener("change", () => syncDisplayForHidden(hidden));
    }

    function bindButton(button) {
        if (!(button instanceof HTMLButtonElement) || button.dataset.eraCalendarButtonBound === "true") {
            return;
        }

        button.dataset.eraCalendarButtonBound = "true";
        button.addEventListener("click", () => {
            const input = document.getElementById(button.getAttribute("data-era-calendar-toggle") || "");
            if (input instanceof HTMLInputElement) {
                openCalendar(input);
                input.focus();
            }
        });
    }

    function bind(root = document) {
        ensureCalendar();
        root.querySelectorAll("[data-era-calendar]").forEach(bindInput);
        root.querySelectorAll("[data-era-calendar-toggle]").forEach(bindButton);
    }

    document.addEventListener("mousedown", (event) => {
        if (!calendar || calendar.hidden) {
            return;
        }

        const target = event.target;
        if (target instanceof Node &&
            (calendar.contains(target) ||
                (activeInput && activeInput.contains(target)) ||
                (target instanceof Element && target.closest("[data-era-calendar-toggle]")))) {
            return;
        }

        closeCalendar();
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && calendar && !calendar.hidden) {
            closeCalendar();
        }
    });

    window.addEventListener("resize", () => {
        if (calendar && !calendar.hidden && activeInput) {
            positionCalendar(activeInput);
        }
    });

    window.addEventListener("scroll", () => {
        if (calendar && !calendar.hidden && activeInput) {
            positionCalendar(activeInput);
        }
    }, true);

    const publicApi = {
        bind,
        format: formatAccessEraDate,
        formatDisplay: formatDisplayDate,
        formatWestern: formatWesternDate,
        formatIsoDate,
        parse: parseAccessEraDate,
        syncDisplayForHidden
    };

    window.nenkinEraDate = publicApi;
    // Retain the .NET migration name while screens are moved to JSP.
    window.jsbrmsEraDate = publicApi;

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => bind(document));
    } else {
        bind(document);
    }
})();
