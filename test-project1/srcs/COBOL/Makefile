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
all: inputs dependencies build/linux/student.cgi build/linux/student-maint
inputs:
	$(PYTHON) tools/input_lock.py
generated:
	$(PYTHON) tools/regenerate.py
dependencies: | build/linux
	$(COBC) -V > build/linux/dependencies.txt
	$(CC) --version >> build/linux/dependencies.txt
	pkg-config --modversion icu-uc openssl odbc >> build/linux/dependencies.txt
build/linux:
	mkdir -p $@
build/linux/student_bridge.o: bridge/student_bridge.c bridge/student_abi.h bridge/fields.h bridge/sql_catalog.h | build/linux
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@
build/linux/student.cgi: cobol/STMAIN.cob $(PROGRAMS) $(COPIES) build/linux/student_bridge.o
	$(COBC) -x $(COBFLAGS) -o $@ cobol/STMAIN.cob $(PROGRAMS) build/linux/student_bridge.o $(LDLIBS)
build/linux/student-maint: cobol/STMAINT.cob $(PROGRAMS) $(COPIES) build/linux/student_bridge.o
	$(COBC) -x $(COBFLAGS) -o $@ cobol/STMAINT.cob $(PROGRAMS) build/linux/student_bridge.o $(LDLIBS)
build/linux/date-probe: tests/date-probe.cob cobol/STDATE.cob $(COPIES) build/linux/student_bridge.o
	$(COBC) -x $(COBFLAGS) -o $@ tests/date-probe.cob cobol/STDATE.cob build/linux/student_bridge.o $(LDLIBS)
build/linux/abi-helper.o: tests/abi-helper.c bridge/student_abi.h | build/linux
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@
build/linux/abi-probe: tests/abi-probe.cob $(COPIES) build/linux/abi-helper.o
	$(COBC) -x $(COBFLAGS) -o $@ tests/abi-probe.cob build/linux/abi-helper.o
build/linux/boundary-probe: tests/boundary-probe.c build/linux/student_bridge.o
	$(CC) $(CPPFLAGS) $(CFLAGS) -o $@ $^ $(LDLIBS)
build/linux/validation-probe: tests/validation-probe.cob $(PROGRAMS) $(COPIES) build/linux/student_bridge.o
	$(COBC) -x $(COBFLAGS) -o $@ tests/validation-probe.cob $(PROGRAMS) build/linux/student_bridge.o $(LDLIBS)
probes: all build/linux/date-probe build/linux/abi-probe build/linux/boundary-probe build/linux/validation-probe
check: probes
	build/linux/abi-probe
	build/linux/date-probe REIWA GAN 05 01 2026-10-10 2019-05-01
clean:
	$(PYTHON) -c "from pathlib import Path; import shutil; p=Path('build/linux').resolve(); r=Path.cwd().resolve(); assert p.parent==r/'build'; shutil.rmtree(p,ignore_errors=True)"
