"""Build and run the real terminal C module in an owned hidden console.

No business fixture, database, machine setting, or system clock is changed.
The C unit TU substitutes session CHECK/TOUCH only; integration is separate.
"""
from pathlib import Path
import ctypes
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

root = Path(__file__).resolve().parent.parent
scratch = root / ".tmp/windows-console"
report = root / "build/test-results"
scratch.mkdir(parents=True, exist_ok=True)
report.mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
for key, name in [("ZIG_GLOBAL_CACHE_DIR", "zig-global-cache"),
                  ("ZIG_LOCAL_CACHE_DIR", "zig-local-cache"),
                  ("TMP", "temp"), ("TEMP", "temp")]:
    path = scratch / name
    path.mkdir(exist_ok=True)
    env[key] = str(path)
compiler = root / ".tmp/toolchain/zig-x86_64-windows-0.14.1/zig.exe"
common = [str(compiler), "cc", "-std=c11", "-target", "x86_64-windows-gnu",
          "-Wall", "-Wextra", "-Werror"]
commands = [common + ["-c", str(root / "bridge/windows_terminal.c"), "-o",
                      str(scratch / "windows-terminal.o")],
            common + [str(root / "tests/windows-terminal-test.c"), "-o",
                      str(scratch / "windows-terminal-test.exe"), "-luser32"]]
result = {"runId": "20261025-regenerate", "profileId": "COBOL",
          "scope": "native-unit-with-synthetic-console-input",
          "sessionScope": "test-only CHECK/TOUCH stubs; real Cbridge integration is separate",
          "startedAt": datetime.now(timezone.utc).isoformat(),
          "commands": [], "checks": [], "status": "Failed", "externalDbConnections": 0,
          "notExecuted": ["real IME", "actual glyph/display-column acceptance",
                          "physical keyboard", "real Cbridge session integration",
                          "COBOL application or SQL Server integration"], "formalScore": None}
logs = []
try:
    if os.name != "nt":
        raise RuntimeError("Windows native console required")
    for command in commands:
        run = subprocess.run(command, env=env, capture_output=True, timeout=120)
        result["commands"].append({"command": subprocess.list2cmdline(command),
                                   "exitCode": run.returncode})
        logs.append(run.stdout.decode("utf-8", "replace") + run.stderr.decode("utf-8", "replace"))
        if run.returncode:
            raise RuntimeError("Native compile failed")
    output = scratch / "native-unit-result.json"
    if output.exists():
        output.unlink()  # Single known disposable file inside resolved scratch.
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 0
    command = [str(scratch / "windows-terminal-test.exe"), str(output)]
    process = subprocess.Popen(command, env=env, creationflags=subprocess.CREATE_NEW_CONSOLE,
                               startupinfo=startup, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = process.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        logs.append(stdout.decode("utf-8", "replace") + stderr.decode("utf-8", "replace"))
        raise RuntimeError("Owned native unit exceeded30seconds; terminated")
    logs.append(stdout.decode("utf-8", "replace") + stderr.decode("utf-8", "replace"))
    result["commands"].append({"command": subprocess.list2cmdline(command),
                               "exitCode": process.returncode,
                               "creation": "CREATE_NEW_CONSOLE + STARTF_USESHOWWINDOW/SW_HIDE"})
    native = json.loads(output.read_text(encoding="utf-8"))
    result["checks"] = native["checks"]
    result["passed"] = native["passed"]
    result["failed"] = native["failed"]
    result["status"] = "Passed" if process.returncode == 0 and native["status"] == "Passed" else "Failed"
    result["childExited"] = process.poll() is not None
except Exception as error:
    result["fatal"] = str(error)
finally:
    result["sourceHashes"] = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in ["bridge/windows_terminal.c", "bridge/windows_terminal.h",
                     "tests/windows-terminal-test.c", "tests/run-windows-terminal-unit.py"]}
    result["completedAt"] = datetime.now(timezone.utc).isoformat()
    (report / "windows-terminal-unit.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (report / "windows-terminal-unit.log").write_text("\n".join(logs), encoding="utf-8")
print(json.dumps({k: result.get(k) for k in ["status", "passed", "failed", "fatal"]}))
sys.exit(0 if result["status"] == "Passed" else 1)
