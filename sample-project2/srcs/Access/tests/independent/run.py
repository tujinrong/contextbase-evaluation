"""Independent tests on an owned copy; no user/final ACCDB or secrets are published."""
from pathlib import Path
import datetime as dt
import gc
import hashlib
import json
import secrets
import shutil
import sys
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import build
import win32api
import win32event
import win32process

CASES = ['IR-A01-seed-and-schema', 'IR-A02-failure4-success-reset', 'IR-A03-search-native-seven-columns',
         'IR-A04-version-before-nochange', 'IR-A05-missing-loaded-child-rejected', 'IR-A06-correctable-saved-value',
         'IR-A07-raw-preserved-on-invalid-kana', 'IR-A08-longtext-supplementary-roundtrip',
         'IR-A09-login-required-input-focus', 'IR-A10-save-field-error-focus', 'IR-A11-empty-new-reservation-required',
         'IR-A12-unknown-save-guard', 'IR-A13-idle-exact-expiry', 'IR-A15-unsearched-raw-survives-new-cancel',
         'IR-A16-busy-export-key-cancel-and-restore', 'IR-A17-busy-validation-restores-disabled-controls',
         'IR-A18-busy-search-restores-unselected-controls']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    source = ROOT / '.tmp/build/CareerManagement.accdb'
    work = ROOT / '.tmp/independent-review'
    work.mkdir(parents=True, exist_ok=True)
    if work.resolve() != work.absolute():
        raise RuntimeError('Redirected review scratch refused')
    target = work / 'CareerManagement-independent.accdb'
    before = sha(source)
    if target.exists():
        if target.is_symlink() or target.parent.resolve() != work.resolve():
            raise RuntimeError('Unsafe independent test copy')
        target.unlink()
    shutil.copy2(source, target)
    if sha(source) != before or sha(target) != before:
        raise RuntimeError('Staging changed while copying; wait for an unchanged candidate')
    passwords = json.loads(build.win32crypt.CryptUnprotectData((ROOT / '.tmp/test-secrets.dpapi').read_bytes(), None, None, None, 0)[1])
    app = None
    process = None
    process_id = None
    process_exited = False
    compiled = False
    stage = 'open-owned-copy'
    rows = []
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    build.pythoncom.CoInitialize()
    try:
        app = build.win32com.client.gencache.EnsureDispatch(build.win32com.client.DispatchEx('Access.Application'))
        app.Visible = False
        process_id = win32process.GetWindowThreadProcessId(app.hWndAccessApp())[1]
        process = win32api.OpenProcess(0x100000, False, process_id)
        app.OpenCurrentDatabase(str(target))
        component = app.VBE.ActiveVBProject.VBComponents.Add(1)
        component.Name = 'IndependentReview'
        module = component.CodeModule
        if module.CountOfLines:
            module.DeleteLines(1, module.CountOfLines)
        module.AddFromString((ROOT / 'tests/independent/ReviewSuite.bas').read_text('utf-8').replace('\n', '\r\n'))
        module = None
        component = None
        # Test-copy-only observation of the existing private export phase; no production flag/behavior change.
        component = app.VBE.ActiveVBProject.VBComponents('modCareerExport')
        module = component.CodeModule
        module.AddFromString('Public Function IndependentExportRunningProbe() As Boolean\r\nIndependentExportRunningProbe = exportRunning\r\nEnd Function\r\n')
        module = None
        component = None
        stage = 'compile-owned-copy'
        app.DoCmd.RunCommand(126)
        compiled = bool(app.IsCompiled)
        if not compiled:
            raise RuntimeError('Access VBA project is not in a compiled state')
        for case in CASES:
            stage = case
            result = app.Run('RunReviewCase', case, passwords[1], passwords[0])
            if isinstance(result, tuple):
                result = result[0]
            parts = str(result).split('|', 1)
            rows.append({'id': case, 'status': parts[0], **({'detail': parts[1]} if len(parts) > 1 else {})})
        # Compare the real CNG result with an independent Python PBKDF2 calculation.
        stage = 'IR-A14-cng-independent-pbkdf2-vector'
        password = secrets.token_urlsafe(24) + '🐱e\u0301  '
        verifier = app.Run('NewVerifier', password)
        if isinstance(verifier, tuple):
            verifier = verifier[0]
        pieces = verifier.split('$')
        expected = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(pieces[3][2:]), 600000, 32).hex()
        valid = app.Run('VerifyPassword', password, verifier)
        invalid = app.Run('VerifyPassword', password.rstrip(), verifier)
        if isinstance(valid, tuple):
            valid = valid[0]
        if isinstance(invalid, tuple):
            invalid = invalid[0]
        ok = pieces[:3] == ['PBKDF2-SHA256', 'v=1', 'i=600000'] and secrets.compare_digest(expected, pieces[4][3:]) and bool(valid) and not bool(invalid)
        rows.append({'id': 'IR-A14-cng-independent-pbkdf2-vector', 'status': 'PASS' if ok else 'FAIL'})
        password = ''
        verifier = ''
        app.CloseCurrentDatabase()
        app.Quit(2)
        app = None
    except Exception as error:
        rows.append({'id': 'IR-HARNESS', 'status': 'FAIL', 'stage': stage,
                     'exceptionType': type(error).__name__, 'hresult': getattr(error, 'hresult', None)})
    finally:
        passwords.clear()
        if app is not None:
            try:
                app.CloseCurrentDatabase()
            except Exception:
                pass
            try:
                app.Quit(2)
            except Exception:
                pass
        app = None
        gc.collect()
        build.release()
        build.pythoncom.CoUninitialize()
        if process is not None:
            process_exited = win32event.WaitForSingleObject(process, 5000) == 0
            process.Close()
    candidate_unchanged = sha(source) == before
    result = {'status': 'PASS' if rows and all(x['status'] == 'PASS' for x in rows) and process_exited and compiled and candidate_unchanged else 'FAIL', 'reviewer': '/root/req_desktop',
              'startedAtUtc': started, 'finishedAtUtc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'candidateArtifactSha256': before, 'candidateUnchanged': candidate_unchanged,
              'compileGate': {'command': 'acCmdCompileAndSaveAllModules(126)', 'isCompiled': compiled},
              'testCopyProbes': ['IndependentReview module', 'modCareerExport readonly exportRunning getter; canonical source unchanged'],
              'requestedChecks': len(CASES) + 1, 'completedProductCases': sum(x['id'] in CASES for x in rows),
              'ownedAccessPid': process_id, 'ownedProcessExited': process_exited,
              'testSources': {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in Path(__file__).parent.glob('*') if p.is_file()},
              'checks': rows, 'scope': 'Actual Access64 COM/VBA/CNG/ACE on a disposable candidate copy. Busy export uses an owned-form Timer at product DoEvents checkpoints to inspect locks and invoke key/Esc handlers; success/cancel/validation restoration is checked. Handler API and field Value/focus checks are not native keyboard/IME evidence. No source/final/user database modified.',
              'notPerformed': ['Real keyboard/IME/DPI/printing', 'Cross-process gate/concurrent saves', 'Access commit acknowledgement fault injection', 'User acceptance/formal scoring'], 'formalScore': None}
    output = ROOT / 'build/test-results/independent-review/access.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf-8')
    print(json.dumps({'status': result['status'], 'checks': len(rows), 'failed': [x for x in rows if x['status'] != 'PASS'], 'candidateUnchanged': result['candidateUnchanged']}, ensure_ascii=False))
    return 0 if result['status'] == 'PASS' and result['candidateUnchanged'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
