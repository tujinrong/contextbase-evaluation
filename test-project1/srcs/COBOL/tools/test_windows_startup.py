"""Real student-text.exe startup smoke in an owned, hidden native console.

The child has no DSN. Only synthetic F12/F3 are sent to its own CONIN$.
This is not manual IME, glyph, physical keyboard, or SQL Server acceptance.
"""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
from ctypes import wintypes as W
import ctypes as C
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
import evidence
from output_paths import ensure_directory, write_json, write_latest

ROOT = Path(__file__).resolve().parents[1]


def run():
    scratch = ensure_directory(ROOT / ".tmp/windows-console")
    report = ROOT / "build/test-results/windows-startup.json"
    exe = ROOT / "build/app/windows/student-text.exe"
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    runner_before = digest(Path(__file__))
    result = {"runId": os.environ.get('COBOL_RUN_ID', 'local-cobol'), "profileId": "COBOL",
              "scope": "real-Windows-Text-entry-no-DSN-synthetic-input",
              "startedAt": datetime.now(timezone.utc).isoformat(), "checks": [],
              "status": "Failed", "externalDbConnections": 0,
              "databaseMode": "STUDENT_ODBC_DSN empty; no SQLDriverConnectW target",
              "startupStatus": "EXPECTED_DB_UNAVAILABLE",
              "expectedProcessExit": 1,
              "authentication": "user-requested no-auth sample",
              "notExecuted": ["SQL Server integration", "successful DB-connected startup/session exit0", "manual glyph and display-column acceptance",
                              "real IME", "physical keyboard", "deployment or formal acceptance"],
              "formalScore": None}
    write_json(report, {**result, 'status': 'RUNNING'})
    process = None
    attached = False
    handles = []
    hwnd = None
    logs = []

    def check(name, value, **data):
        result["checks"].append({"name": name, "passed": bool(value), **data})
        if not value:
            raise RuntimeError(name)

    try:
        if os.name != "nt":
            raise RuntimeError("Windows required")
        kernel = C.WinDLL("kernel32", use_last_error=True)
        user = C.WinDLL("user32", use_last_error=True)

        class Coord(C.Structure):
            _fields_ = [("x", W.SHORT), ("y", W.SHORT)]

        class Rect(C.Structure):
            _fields_ = [(name, W.SHORT) for name in ["left", "top", "right", "bottom"]]

        class Char(C.Union):
            _fields_ = [("wide", C.c_uint16), ("ascii", C.c_char)]

        class Cell(C.Structure):
            _fields_ = [("char", Char), ("attribute", W.WORD)]

        class Info(C.Structure):
            _fields_ = [("size", Coord), ("cursor", Coord), ("attribute", W.WORD),
                        ("window", Rect), ("maximum", Coord)]

        class Key(C.Structure):
            _fields_ = [("down", W.BOOL), ("repeat", W.WORD), ("vk", W.WORD),
                        ("scan", W.WORD), ("char", Char), ("state", W.DWORD)]

        class Event(C.Union):
            _fields_ = [("key", Key), ("raw", C.c_byte * 16)]

        class Input(C.Structure):
            _fields_ = [("kind", W.WORD), ("event", Event)]

        def api(lib, name, args, restype=W.BOOL):
            function = getattr(lib, name)
            function.argtypes, function.restype = args, restype
            return function

        attach = api(kernel, "AttachConsole", [W.DWORD])
        detach = api(kernel, "FreeConsole", [])
        window = api(kernel, "GetConsoleWindow", [], W.HWND)
        visible = api(user, "IsWindowVisible", [W.HWND])
        exists = api(user, "IsWindow", [W.HWND])
        create = api(kernel, "CreateFileW", [W.LPCWSTR, W.DWORD, W.DWORD, W.LPVOID,
                                             W.DWORD, W.DWORD, W.HANDLE], W.HANDLE)
        close = api(kernel, "CloseHandle", [W.HANDLE])
        info = api(kernel, "GetConsoleScreenBufferInfo", [W.HANDLE, C.POINTER(Info)])
        read = api(kernel, "ReadConsoleOutputW", [W.HANDLE, C.POINTER(Cell), Coord,
                                                  Coord, C.POINTER(Rect)])
        write = api(kernel, "WriteConsoleInputW", [W.HANDLE, C.POINTER(Input), W.DWORD,
                                                   C.POINTER(W.DWORD)])
        check("INPUT_RECORD ABI20", C.sizeof(Input) == 20)
        compiled = json.loads((ROOT / ".tmp/host/build-evidence.json").read_text(encoding="utf-8"))
        before = evidence.compiled_inputs()
        manifest_before = digest(ROOT / "build/input-manifest.json")
        binaries_before = evidence.binary_hashes()
        result["inputManifestSha256"] = manifest_before
        result["binaryHashes"] = binaries_before
        binary_before = digest(exe)
        result["binary"] = {"file": "build/app/windows/student-text.exe", "sha256": binary_before}
        result["compiledInputs"] = before
        check("compiled inputs match current sources", compiled.get("succeeded") and compiled["compiledInputs"] == before)
        check("entry executable matches completed build", compiled["binaries"]["student-text.exe"] == binary_before)
        env = os.environ.copy()
        env["PATH"] = str(ROOT / ".tmp/toolchain/msys2/ucrt64/bin") + os.pathsep + env.get("PATH", "")
        env["COB_CONFIG_DIR"] = ".tmp/toolchain/msys2/ucrt64/share/gnucobol/config"
        env["STUDENT_ODBC_DSN"] = ""
        for name in ["REMOTE_USER", "ST_LOGIN_SESSION_ID", "ST_TRUSTED_ROLE", "STUDENT_STATE_KEY_HEX"]:
            env.pop(name, None)
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        process = subprocess.Popen([str(exe)], cwd=ROOT, env=env,
                                   creationflags=subprocess.CREATE_NEW_CONSOLE, startupinfo=startup,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result["command"] = "build/app/windows/student-text.exe"
        result["creation"] = "CREATE_NEW_CONSOLE + STARTF_USESHOWWINDOW/SW_HIDE"
        # Detach only this test inspector process; never operate another app's console.
        detach()
        until = time.monotonic() + 5
        while time.monotonic() < until and process.poll() is None:
            if attach(process.pid):
                attached = True
                break
            time.sleep(0.02)
        check("attach owned hidden native child", attached)
        hwnd = window()
        check("native console is hidden", hwnd and not visible(hwnd))
        inp = create("CONIN$", 0xC0000000, 3, None, 3, 0, None)
        check("own CONIN opened", inp not in (None, C.c_void_p(-1).value))
        handles.append(inp)

        def capture():
            out = create("CONOUT$", 0xC0000000, 3, None, 3, 0, None)
            if out in (None, C.c_void_p(-1).value):
                raise C.WinError(C.get_last_error())
            try:
                state = Info()
                if not info(out, C.byref(state)):
                    raise C.WinError(C.get_last_error())
                if state.size.x < 132 or state.size.y < 27:
                    return "", state
                cells = (Cell * (132 * 27))()
                rect = Rect(0, 0, 131, 26)
                if not read(out, cells, Coord(132, 27), Coord(0, 0), C.byref(rect)):
                    raise C.WinError(C.get_last_error())
                rows = []
                for row in range(27):
                    data = b"".join(int(cell.char.wide).to_bytes(2, "little")
                                    for cell in cells[row * 132:(row + 1) * 132])
                    rows.append(data.decode("utf-16-le", "replace"))
                return "\n".join(rows), state
            finally:
                close(out)

        def wait_frame(predicate):
            until = time.monotonic() + 8
            last = ""
            while time.monotonic() < until and process.poll() is None:
                last, state = capture()
                if predicate(last.replace(" ", "").replace("\x00", "")):
                    return last, state
                time.sleep(0.02)
            write_latest(scratch / "integration-last-frame.txt", last)
            raise RuntimeError("Expected native frame not observed; see scratch frame")

        def press(vk):
            records = (Input * 2)()
            for index, down in enumerate([1, 0]):
                records[index].kind = 1
                records[index].event.key.down = down
                records[index].event.key.repeat = 1
                records[index].event.key.vk = vk
            count = W.DWORD()
            if not write(inp, records, 2, C.byref(count)) or count.value != 2:
                raise C.WinError(C.get_last_error())

        frame, state = wait_frame(lambda text: "エラー一覧" in text and "E-COM-004" in text)
        check("native frame132x27", state.size.x == 132 and state.size.y == 27)
        normal = frame.replace(" ", "")
        check("fixed no-auth sample header", "sample-userAdministrator" in normal and "認証なしサンプル" in normal)
        check("no-DSN error rendered through actual Text entry", "E-COM-004" in normal and "エラー一覧" in normal)
        write_latest(scratch / "integration-startup-frame.txt", frame)
        press(0x7B)  # F12: close the error panel only.
        frame, _ = wait_frame(lambda text: "エラー一覧" not in text and "未検索" in text)
        check("F12 returns from error to unsearched normal panel", "未検索" in frame.replace(" ", ""))
        press(0x72)  # F3: local MENU exit; no DB configuration.
        stdout, stderr = process.communicate(timeout=8)
        logs.append(stdout.decode("utf-8", "replace") + stderr.decode("utf-8", "replace"))
        check("DB unavailable startup exits safely after F3 MENU with expected code1", process.returncode == 1, exitCode=process.returncode)
        result["actualProcessExit"] = process.returncode
        check("entry and compiled inputs unchanged", digest(exe) == binary_before and evidence.compiled_inputs() == before
              and digest(ROOT / "build/input-manifest.json") == manifest_before
              and evidence.binary_hashes() == binaries_before and digest(Path(__file__)) == runner_before)
        result["status"] = "Passed"
    except Exception as error:
        result["fatal"] = str(error)
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            stdout, stderr = process.communicate()
            logs.append(stdout.decode("utf-8", "replace") + stderr.decode("utf-8", "replace"))
            result["ownedChildTerminatedAfterFailure"] = True
        if os.name == "nt":
            for handle in handles:
                close(handle)
            if attached:
                detach()
            if hwnd:
                for _ in range(100):
                    if not exists(hwnd):
                        break
                    time.sleep(0.01)
                left = bool(exists(hwnd))
                result["nativeConsoleWindowLeft"] = left
                result["checks"].append({"name": "owned console closed", "passed": not left})
                if left:
                    result["status"] = "Failed"
        result["passed"] = sum(item["passed"] for item in result["checks"])
        result["failed"] = sum(not item["passed"] for item in result["checks"])
        result["runnerSha256"] = runner_before
        result["completedAt"] = datetime.now(timezone.utc).isoformat()
        write_json(report, result)
        write_latest(report.with_suffix(".log"), "\n".join(logs))
    print(json.dumps({key: result.get(key) for key in ["status", "passed", "failed", "fatal"]}))
    return 0 if result["status"] == "Passed" else 1


if __name__ == "__main__":
    raise SystemExit(run())
