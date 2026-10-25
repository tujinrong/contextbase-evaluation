# Linux x86_64 deployment. Host .exe evidence is a separate build profile.
COBC ?= cobc
CC ?= gcc
PYTHON ?= python3
COBFLAGS = -free -fstatic-call -Wall -I copy
CPPFLAGS += -I bridge $(shell pkg-config --cflags icu-uc openssl odbc)
CFLAGS += -std=c11 -O2 -fPIC -Wall -Wextra -Werror
LDLIBS = $(shell pkg-config --libs icu-uc openssl odbc)
PROGRAMS := $(filter-out cobol/STMAIN.cob cobol/STMAINT.cob,$(wildcard cobol/*.cob))
COPIES := $(wildcard copy/*.cpy)
.PHONY: all inputs generated dependencies probes check clean
all: inputs dependencies build/app/linux/student.cgi build/app/linux/student-maint
inputs:
	$(PYTHON) tools/input_lock.py
generated:
	$(PYTHON) tools/regenerate.py
dependencies: | .tmp/linux build/app/linux build/test-results/linux
	$(COBC) -V > build/test-results/linux/dependencies.txt
	$(CC) --version >> build/test-results/linux/dependencies.txt
	pkg-config --modversion icu-uc openssl odbc >> build/test-results/linux/dependencies.txt
.tmp/linux build/app/linux build/test-results/linux:
	mkdir -p $@
.tmp/linux/student_bridge.o: bridge/student_bridge.c bridge/student_abi.h bridge/fields.h bridge/sql_catalog.h | .tmp/linux
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@
build/app/linux/student.cgi: cobol/STMAIN.cob $(PROGRAMS) $(COPIES) .tmp/linux/student_bridge.o | build/app/linux
	$(COBC) -x $(COBFLAGS) -o $@ cobol/STMAIN.cob $(PROGRAMS) .tmp/linux/student_bridge.o $(LDLIBS)
build/app/linux/student-maint: cobol/STMAINT.cob $(PROGRAMS) $(COPIES) .tmp/linux/student_bridge.o | build/app/linux
	$(COBC) -x $(COBFLAGS) -o $@ cobol/STMAINT.cob $(PROGRAMS) .tmp/linux/student_bridge.o $(LDLIBS)
.tmp/linux/date-probe: tests/date-probe.cob cobol/STDATE.cob $(COPIES) .tmp/linux/student_bridge.o | build/app/linux
	$(COBC) -x $(COBFLAGS) -o $@ tests/date-probe.cob cobol/STDATE.cob .tmp/linux/student_bridge.o $(LDLIBS)
.tmp/linux/abi-helper.o: tests/abi-helper.c bridge/student_abi.h | .tmp/linux
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@
.tmp/linux/abi-probe: tests/abi-probe.cob $(COPIES) .tmp/linux/abi-helper.o
	$(COBC) -x $(COBFLAGS) -o $@ tests/abi-probe.cob .tmp/linux/abi-helper.o
.tmp/linux/boundary-probe: tests/boundary-probe.c .tmp/linux/student_bridge.o
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ $^ $(LDLIBS)
.tmp/linux/validation-probe: tests/validation-probe.cob $(PROGRAMS) $(COPIES) .tmp/linux/student_bridge.o | build/app/linux
	$(COBC) -x $(COBFLAGS) -o $@ tests/validation-probe.cob $(PROGRAMS) .tmp/linux/student_bridge.o $(LDLIBS)
probes: all .tmp/linux/date-probe .tmp/linux/abi-probe .tmp/linux/boundary-probe .tmp/linux/validation-probe
check: probes
	.tmp/linux/abi-probe
	.tmp/linux/date-probe REIWA GAN 05 01 2026-10-10 2019-05-01
clean:
	$(PYTHON) -c "from pathlib import Path; import shutil; p=Path('.tmp/linux').resolve(); r=Path.cwd().resolve(); assert p.parent==r/'.tmp'; shutil.rmtree(p,ignore_errors=True)"
