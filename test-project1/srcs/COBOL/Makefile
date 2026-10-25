# Windows x64 native Console sample. build.py replaces its checked scratch.
# Example: make BUILD_ARGS="--sdk C:/sdk/ucrt64 --cc C:/sdk/zig/zig.exe"
PYTHON ?= python
BUILD_ARGS ?=
.DEFAULT_GOAL := all
.PHONY: all
all:
	$(PYTHON) -X utf8 build.py $(BUILD_ARGS)
