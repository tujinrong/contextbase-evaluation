#!/bin/sh
set -eu
umask 077
COBOL_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$COBOL_ROOT"
export STUDENT_RENDER_DIR="$COBOL_ROOT/build/runtime"
exec "$COBOL_ROOT/build/linux/student.cgi"
