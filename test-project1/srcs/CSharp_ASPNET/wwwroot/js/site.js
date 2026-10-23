// UI-10..13; EV-REG-003/005/007. The server revalidates every save and delete.
(() => {
    const editor = document.querySelector('[data-editor-form]');
    const duplicateDialog = document.querySelector('#REG-032');
    const deleteDialog = document.querySelector('#delete-dialog');
    const discardDialog = document.querySelector('#discard-dialog');
    const duplicateToken = editor?.querySelector('[name="Input.DuplicateToken"]');
    const operationReason = editor?.querySelector('[name="Input.OperationReason"]');
    const duplicateReason = document.querySelector('#duplicate-reason');
    const approvedForms = new WeakSet();
    const disabledByBusy = new Set();
    let dirty = false;
    let leaving = false;
    let submitting = false;
    let activeDialog = null;
    let returnFocus = null;
    let pendingDiscard = null;
    const original = editor ? JSON.parse(editor.dataset.originalValues) : null;
    const canEdit = !!editor && !document.querySelector('#REG-027').disabled;
    const editableControls = () => editor && canEdit ? [...editor.querySelectorAll('input[name],select[name],textarea[name]')]
        .filter(control => control.type !== 'hidden' && control.name.startsWith('Input.')) : [];
    function updateDirty() {
        dirty = editableControls().some(control => {
            const value = control.name.slice(6).split('.').reduce((item, key) => item?.[key], original);
            return control.value.replace(/\r\n/g, '\n') !== String(value ?? '').replace(/\r\n/g, '\n');
        });
        return dirty;
    }
    function closeDialog() {
        if (activeDialog) activeDialog.close();
    }
    function openDialog(dialog, trigger) {
        if (!dialog || submitting) return;
        if (activeDialog === dialog) return;
        if (activeDialog) closeDialog();
        returnFocus = trigger || document.activeElement;
        activeDialog = dialog;
        dialog.hidden = false;
        dialog.showModal(); // Native modal dialogs make the background inert.
        dialog.querySelector('[data-dialog-cancel]')?.focus();
    }
    function cancelDialog(dialog) {
        if (dialog === duplicateDialog) {
            if (duplicateToken) duplicateToken.value = '';
            if (operationReason && duplicateReason) operationReason.value = duplicateReason.value;
            updateDirty();
        }
        pendingDiscard = null;
        closeDialog();
    }
    function askDiscard(trigger, message, action) {
        pendingDiscard = action;
        document.querySelector('#discard-description').textContent = message || '保存していない変更を破棄しますか。';
        openDialog(discardDialog, trigger);
    }
    for (const dialog of document.querySelectorAll('dialog.dialog-state')) {
        dialog.addEventListener('cancel', event => {
            event.preventDefault();
            cancelDialog(dialog);
        });
        dialog.addEventListener('close', () => {
            dialog.hidden = true;
            if (activeDialog === dialog) {
                activeDialog = null;
                if (returnFocus?.isConnected && !returnFocus.disabled) returnFocus.focus();
                returnFocus = null;
            }
        });
        dialog.querySelectorAll('[data-dialog-cancel]').forEach(button => button.addEventListener('click', () => cancelDialog(dialog)));
        dialog.addEventListener('keydown', event => {
            if (event.key === 'Enter' && !event.target.closest('button') && event.target.tagName !== 'TEXTAREA') {
                event.preventDefault(); // Enter must not implicitly confirm a destructive operation.
            }
            if (event.key !== 'Tab') return;
            const focusable = [...dialog.querySelectorAll('button,input,select,textarea,a[href],[tabindex]')]
                .filter(control => !control.disabled && control.tabIndex >= 0 && control.getClientRects().length > 0);
            const first = focusable[0], last = focusable.at(-1);
            if (event.shiftKey && (document.activeElement === first || !dialog.contains(document.activeElement))) {
                event.preventDefault(); last?.focus();
            } else if (!event.shiftKey && (document.activeElement === last || !dialog.contains(document.activeElement))) {
                event.preventDefault(); first?.focus();
            }
        });
    }
    document.querySelector('[data-confirm-discard]')?.addEventListener('click', () => {
        const action = pendingDiscard;
        pendingDiscard = null;
        closeDialog();
        action?.();
    });
    document.querySelector('[data-open-delete]')?.addEventListener('click', event => openDialog(deleteDialog, event.currentTarget));
    duplicateReason?.addEventListener('input', () => duplicateReason.setCustomValidity(''));
    if (editor) {
        const changed = event => {
            if (event.target.name !== 'Input.OperationReason' && duplicateToken) duplicateToken.value = '';
            updateDirty();
        };
        editor.addEventListener('input', changed);
        editor.addEventListener('change', changed);
        updateDirty();
        window.addEventListener('beforeunload', event => {
            if (updateDirty() && !leaving) { event.preventDefault(); event.returnValue = ''; }
        });
    }
    for (const form of document.forms) {
        form.addEventListener('submit', event => {
            const button = event.submitter;
            if (submitting) { event.preventDefault(); return; }
            if (form === editor && activeDialog === duplicateDialog) {
                if (!button?.hasAttribute('data-confirm-duplicate')) { event.preventDefault(); return; }
                duplicateReason.setCustomValidity(duplicateReason.value.trim() ? '' : '確認理由を入力してください。');
                if (!duplicateReason.reportValidity()) { event.preventDefault(); return; }
                operationReason.value = duplicateReason.value;
                updateDirty();
            }
            if (form.hasAttribute('data-delete-form') && !button?.hasAttribute('data-confirm-delete')) {
                event.preventDefault(); return;
            }
            if (editor && !approvedForms.has(form) && (form.hasAttribute('data-reset-form') || (form !== editor && !form.hasAttribute('data-delete-form') && updateDirty()))) {
                event.preventDefault();
                askDiscard(button, form.dataset.discardMessage, () => {
                    approvedForms.add(form);
                    form.requestSubmit(button || undefined);
                });
                return;
            }
            approvedForms.delete(form);
            const prompt = button?.dataset.confirm || form.dataset.confirm;
            if (prompt && !window.confirm(prompt)) { event.preventDefault(); return; }
            leaving = true;
            submitting = true;
            form.setAttribute('aria-busy', 'true');
            document.querySelectorAll('button').forEach(action => {
                if (action !== button && !action.disabled) { disabledByBusy.add(action); action.disabled = true; }
            });
        });
    }
    for (const link of document.querySelectorAll('[data-dirty-link]')) {
        link.addEventListener('click', event => {
            if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
            if (submitting) { event.preventDefault(); return; }
            if (editor && (updateDirty() || link.dataset.alwaysConfirm === 'true')) {
                event.preventDefault();
                askDiscard(link, link.dataset.discardMessage, () => { leaving = true; window.location.assign(link.href); });
            } else leaving = true;
        });
    }
    window.addEventListener('pageshow', () => {
        leaving = false;
        submitting = false;
        disabledByBusy.forEach(button => { button.disabled = false; });
        disabledByBusy.clear();
        document.querySelectorAll('form[aria-busy]').forEach(form => form.removeAttribute('aria-busy'));
    });
    const classSelect = document.querySelector('#REG-018');
    const year = document.querySelector('#REG-016');
    const grade = document.querySelector('#REG-017');
    const status = document.querySelector('#REG-014');
    const admission = document.querySelector('#REG-013');
    const end = document.querySelector('#REG-015');
    function showOccupancy() {
        const option = classSelect?.selectedOptions[0];
        const display = document.querySelector('#REG-019');
        if (display) display.textContent = option?.value ? `${option.dataset.occupied} ／ ${option.dataset.capacity || '制限なし'}（参考）` : '－ ／ －（参考）';
    }
    function refreshClasses(clearInvalid) {
        if (!classSelect) return;
        const terminal = status.value === '03' || status.value === '04';
        const today = editor.dataset.businessDate;
        classSelect.required = !terminal;
        end.required = terminal;
        // Keep a rejected raw end date visible; an empty nonterminal date cannot be entered.
        end.disabled = canEdit && !terminal && !end.value;
        end.readOnly = !canEdit || !terminal;
        for (const option of classSelect.options) {
            if (!option.value) continue;
            const matches = (!year.value || year.value === option.dataset.year) && (!grade.value || grade.value === option.dataset.grade);
            const available = terminal ? !!admission.value && !!end.value && option.dataset.from <= end.value && admission.value <= option.dataset.to
                : option.dataset.active === 'true' && (!today || option.dataset.from <= today && today <= option.dataset.to);
            option.disabled = !matches || !(option.dataset.existing === 'true' || available);
        }
        if (clearInvalid && classSelect.value && classSelect.selectedOptions[0].disabled) {
            classSelect.value = '';
            if (duplicateToken) duplicateToken.value = '';
            document.querySelector('#class-change-status').textContent = '年度・学年・在籍条件に合わないクラスを解除しました。クラスを選び直してください。';
        }
        showOccupancy();
        updateDirty();
    }
    classSelect?.addEventListener('change', () => {
        const option = classSelect.selectedOptions[0];
        if (option?.dataset.year) { year.value = option.dataset.year; grade.value = option.dataset.grade; }
        refreshClasses(false);
    });
    for (const control of [year, grade, status, admission, end]) control?.addEventListener('change', () => refreshClasses(true));
    refreshClasses(false);
    const search = document.querySelector('[data-search-form]');
    const criteriaStatus = document.querySelector('[data-criteria-status]');
    const currentCriteria = () => ({
        studentNo: search.querySelector('[name="Criteria.StudentNo"]').value,
        name: search.querySelector('[name="Criteria.Name"]').value,
        classId: search.querySelector('[name="Criteria.ClassId"]').value,
        statusCodes: [...search.querySelectorAll('[name="Criteria.StatusCodes"]:checked')].map(control => control.value).sort()
    });
    const appliedInput = search?.dataset.appliedInput ? JSON.parse(search.dataset.appliedInput) : null;
    const appliedCriteria = appliedInput ? { studentNo: appliedInput.StudentNo, name: appliedInput.Name,
        classId: appliedInput.ClassId, statusCodes: appliedInput.StatusCodes } : search ? currentCriteria() : null;
    const criteriaKey = values => JSON.stringify({ studentNo: values.studentNo || '', name: values.name || '',
        classId: values.classId || '', statusCodes: [...(values.statusCodes || [])].sort() });
    const markCriteriaChanged = () => {
        if (!criteriaStatus) return;
        criteriaStatus.textContent = search.dataset.searchOutcome === 'unsearched' ? '条件を指定して検索してください。'
            : criteriaKey(currentCriteria()) === criteriaKey(appliedCriteria) ? '実行した条件を表示しています。'
            : '条件の変更は未反映です。検索を押すと一覧に反映します。';
    };
    search?.addEventListener('input', markCriteriaChanged);
    search?.addEventListener('change', markCriteriaChanged);
    if (search) markCriteriaChanged();
    document.querySelectorAll('[data-error-summary] a[href^="#"]').forEach(link => link.addEventListener('click', event => {
        const target = document.getElementById(link.hash.slice(1));
        if (!target) return;
        event.preventDefault();
        const dialog = target.closest('dialog');
        if (dialog && !dialog.open) openDialog(dialog, link);
        target.focus();
        target.scrollIntoView({ block: 'nearest' });
    }));
    const autoDialog = document.querySelector('dialog[data-auto-open="true"]');
    if (autoDialog) openDialog(autoDialog, document.querySelector(autoDialog === duplicateDialog ? '#REG-027' : '#REG-031'));
    else document.querySelector('[data-error-summary]')?.focus();
})();
