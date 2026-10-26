"""Read-only syntax indexes; successful parsing does not establish semantic truth.

The two adapters share records, not a required inheritance hierarchy.  No input
code is imported, compiled, executed, or linked to a guessed call target.
"""

from __future__ import annotations

import hashlib
import importlib
from bisect import bisect_right
import json
import math
import os
from pathlib import PurePosixPath
import re
import subprocess
import sys
from typing import Protocol


MAX_SOURCE_BYTES = 4 * 1024 * 1024
MAX_NODES = 200_000


class LanguageAdapter(Protocol):
    def index(self, path: str, text: str, *, source_sha256: str) -> dict: ...


def _load_parser(module_name: str):
    from tree_sitter import Language, Parser

    grammar = importlib.import_module(module_name)
    return Parser(Language(grammar.language()))


def _result(path: str, language: str | None, module: str | None) -> dict:
    return {
        "path": path,
        "language": language,
        "status": "unsupported",
        "symbols": [],
        "imports": [],
        "calls": [],
        "diagnostics": [],
        "capabilities": {
            "syntax": False,
            "symbols": False,
            "imports": False,
            "callSites": False,
            "semanticBinding": False,
            "dataFlow": False,
            "frameworkRules": False,
        },
        "backend": {"name": "tree-sitter", "grammar": module, "available": False},
    }


def _diagnostic(code: str, message: str, evidence: list | None = None) -> dict:
    return {"code": code, "message": message, "evidence": evidence or []}


def _syntax_index(path: str, text: str, source_sha256: str, *, language: str,
                  module: str, declarations: dict[str, str]) -> dict:
    result = _result(path, language, module)
    result["capabilities"]["symbolKinds"] = sorted(set(declarations.values()))
    result["capabilities"]["callKinds"] = ["invocation", "construction"]
    if not re.fullmatch(r"[0-9a-fA-F]{64}", source_sha256):
        result["status"] = "failed"
        result["diagnostics"].append(_diagnostic("invalid-source-hash", "Expected a SHA-256 hex digest."))
        return result
    try:
        data = text.encode("utf-8")
    except UnicodeEncodeError:
        result["status"] = "failed"
        result["diagnostics"].append(_diagnostic("invalid-text", "Source text contains an unpaired surrogate."))
        return result
    if len(data) > MAX_SOURCE_BYTES:
        result["status"] = "limit-exceeded"
        result["diagnostics"].append(_diagnostic("source-size-limit", f"Source exceeds {MAX_SOURCE_BYTES} UTF-8 bytes; no truncation was parsed."))
        return result
    try:
        parser = _load_parser(module)
    except (ImportError, AttributeError, TypeError, ValueError, OSError) as exc:
        result["diagnostics"].append(_diagnostic("parser-unavailable", f"{type(exc).__name__}: {exc}"))
        return result
    result["backend"]["available"] = True
    try:
        tree = parser.parse(data)
        if tree is None:
            raise RuntimeError("Parser returned no syntax tree.")
        root = tree.root_node
        # py-tree-sitter 0.26.0 Point.row/column have a borrowed-reference bug
        # (upstream #472/#500). Byte offsets avoid that API and are exact for
        # decoded UTF-8, including CRLF and multibyte characters.
        line_starts = [0] + [i + 1 for i, byte in enumerate(data) if byte == 10]

        def content(node) -> str:
            return data[node.start_byte:node.end_byte].decode("utf-8") if node is not None else ""

        def evidence(node) -> list[dict]:
            start_line = bisect_right(line_starts, node.start_byte)
            end_line = bisect_right(line_starts, max(node.start_byte, node.end_byte - 1))
            return [{"path": path, "startLine": start_line,
                     "endLine": end_line,
                     "sha256": source_sha256}]

        # Java packages and C# file-scoped namespaces apply to following siblings.
        initial_scope: tuple[str, ...] = ()
        for child in root.named_children:
            if child.type in {"package_declaration", "file_scoped_namespace_declaration"}:
                name = child.child_by_field_name("name")
                if name is None:
                    name = next((n for n in child.named_children
                                 if n.type in {"identifier", "scoped_identifier", "qualified_name"}), None)
                if name is not None:
                    initial_scope = (content(name),)
        stack = [(root, initial_scope, initial_scope)]
        visited = 0
        while stack:
            node, names, identities = stack.pop()
            visited += 1
            if visited > MAX_NODES:
                # No incomplete prefix is exposed as a complete index.
                result.update(status="limit-exceeded", symbols=[], imports=[], calls=[])
                result["diagnostics"].append(_diagnostic("node-limit", f"Syntax tree exceeds {MAX_NODES} nodes; index was discarded."))
                return result
            if node.type == "ERROR" or node.is_missing:
                result["diagnostics"].append(_diagnostic(
                    "syntax-error" if node.type == "ERROR" else "missing-syntax",
                    f"{node.type}: {content(node)[:160]}", evidence(node)))
            child_names, child_identities = names, identities
            if node.type in declarations:
                name_node = node.child_by_field_name("name")
                name = content(name_node)
                if name:
                    kind = declarations[node.type]
                    parameters = node.child_by_field_name("parameters")
                    type_parameters = node.child_by_field_name("type_parameters")
                    explicit_interface = next((child for child in node.named_children
                                               if child.type == "explicit_interface_specifier"), None)
                    # Preserve declared overload syntax without claiming type resolution.
                    signature = content(explicit_interface) + name + content(type_parameters) + content(parameters)
                    signature = " ".join(signature.split())
                    qualified_name = ".".join((*names, name))
                    identity_scope = "::".join(identities)
                    identity = "\0".join((path.replace("\\", "/"), identity_scope, kind, signature))
                    result["symbols"].append({
                        "id": "symbol:" + hashlib.sha256(identity.encode("utf-8")).hexdigest(),
                        "kind": kind, "name": name, "qualifiedName": qualified_name,
                        "scope": identity_scope, "signature": signature,
                        "startLine": evidence(node)[0]["startLine"],
                        "endLine": evidence(node)[0]["endLine"], "evidence": evidence(node),
                    })
                    child_names = (*names, name)
                    child_identities = (*identities, signature)
            elif node.type in {"using_directive", "import_declaration"}:
                result["imports"].append({"text": content(node), "scope": "::".join(identities),
                                          "evidence": evidence(node)})
            elif node.type in {"invocation_expression", "method_invocation", "object_creation_expression"}:
                receiver = None
                call_kind = "invocation"
                if node.type == "method_invocation":
                    target = node.child_by_field_name("name")
                    receiver_node = node.child_by_field_name("object")
                elif node.type == "object_creation_expression":
                    target = node.child_by_field_name("type")
                    receiver_node = None
                    call_kind = "construction"
                else:
                    function = node.child_by_field_name("function")
                    target = function
                    receiver_node = None
                    if function is not None and function.type in {"member_access_expression", "member_binding_expression"}:
                        target = function.child_by_field_name("name")
                        receiver_node = function.child_by_field_name("expression")
                if receiver_node is not None:
                    receiver = content(receiver_node)
                result["calls"].append({
                    "name": content(target), "receiver": receiver, "text": content(node),
                    "kind": call_kind, "scope": "::".join(identities),
                    "resolution": "unresolved", "evidence": evidence(node),
                })
            for child in reversed(node.children):
                stack.append((child, child_names, child_identities))
        result["status"] = "partial" if root.has_error else "complete"
        if root.has_error and not result["diagnostics"]:
            result["diagnostics"].append(_diagnostic("syntax-error", "Tree reports a syntax error.", evidence(root)))
        result["capabilities"].update(syntax=True, symbols=True, imports=True, callSites=True)
    except Exception as exc:
        result.update(status="failed", symbols=[], imports=[], calls=[])
        result["diagnostics"].append(_diagnostic("parser-failure", f"{type(exc).__name__}: {exc}"))
    return result


class CSharpAdapter:
    def index(self, path: str, text: str, *, source_sha256: str) -> dict:
        return _syntax_index(path, text, source_sha256, language="csharp", module="tree_sitter_c_sharp",
                             declarations={"namespace_declaration": "namespace", "class_declaration": "class",
                                           "struct_declaration": "struct", "interface_declaration": "interface",
                                           "record_declaration": "record", "enum_declaration": "enum",
                                           "method_declaration": "method", "constructor_declaration": "constructor",
                                           "local_function_statement": "local-function", "property_declaration": "property"})


class JavaAdapter:
    def index(self, path: str, text: str, *, source_sha256: str) -> dict:
        return _syntax_index(path, text, source_sha256, language="java", module="tree_sitter_java",
                             declarations={"class_declaration": "class", "interface_declaration": "interface",
                                           "record_declaration": "record", "enum_declaration": "enum",
                                           "annotation_type_declaration": "annotation", "method_declaration": "method",
                                           "constructor_declaration": "constructor", "compact_constructor_declaration": "constructor"})


def index_source(path: str, text: str, *, source_sha256: str) -> dict:
    """Index a decoded source file; source_sha256 identifies original source bytes.

    ``complete`` describes the supported syntax pass only, never type binding,
    business coverage, or a verified ContextBase.  No filesystem is accessed.
    """
    normalized_path = path.replace("\\", "/")
    suffix = PurePosixPath(normalized_path).suffix.lower()
    adapter = {".cs": CSharpAdapter, ".java": JavaAdapter}.get(suffix)
    if adapter is None:
        result = _result(normalized_path, None, None)
        result["diagnostics"].append(_diagnostic("unsupported-language", f"Unsupported suffix: {suffix or '(none)'}."))
        return result
    return adapter().index(normalized_path, text, source_sha256=source_sha256)


def index_source_isolated(path: str, text: str, *, source_sha256: str,
                          timeout_seconds: float = 30) -> dict:
    """Run this tool's parser in a worker, containing native parser crashes.

    The timeout protects one parse operation, not an investigation's total
    budget.  The input source is JSON data on stdin, never an executable.
    """
    normalized_path = path.replace("\\", "/")
    suffix = PurePosixPath(normalized_path).suffix.lower()
    grammar = {".cs": ("csharp", "tree_sitter_c_sharp"), ".java": ("java", "tree_sitter_java")}.get(suffix)
    if grammar is None:
        return index_source(normalized_path, text, source_sha256=source_sha256)
    result = _result(normalized_path, *grammar)

    def failure(code: str, message: str) -> dict:
        result["status"] = "failed"
        result["diagnostics"].append(_diagnostic(code, message))
        return result

    if (isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(timeout_seconds) or timeout_seconds <= 0):
        return failure("invalid-operation-timeout", "Operation timeout must be a finite positive number.")
    try:
        if len(text.encode("utf-8")) > MAX_SOURCE_BYTES:
            result["status"] = "limit-exceeded"
            result["diagnostics"].append(_diagnostic("source-size-limit", f"Source exceeds {MAX_SOURCE_BYTES} UTF-8 bytes; worker was not started."))
            return result
        request = json.dumps({"path": normalized_path, "text": text, "source_sha256": source_sha256}, ensure_ascii=False)
        completed = subprocess.run(
            [sys.executable, "-m", "contextbase.analysis.adapters", "--worker"],
            input=request, text=True, encoding="utf-8", capture_output=True,
            timeout=timeout_seconds, shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except subprocess.TimeoutExpired:
        return failure("parser-operation-timeout", f"Parser worker exceeded {timeout_seconds} seconds; no index was accepted.")
    except (OSError, UnicodeError) as exc:
        return failure("parser-worker-unavailable", f"{type(exc).__name__}: {exc}")
    if completed.returncode != 0:
        # stderr may contain source text, so retain the exit code without
        # copying arbitrary raw process output into a user-facing diagnostic.
        return failure("parser-worker-exit", f"Parser worker exited with code {completed.returncode}; possible native crash. No index was accepted.")
    try:
        payload = json.loads(completed.stdout)
    except (ValueError, TypeError):
        return failure("parser-worker-protocol", "Parser worker did not return a JSON index.")
    required = {"path", "language", "status", "symbols", "imports", "calls", "diagnostics", "capabilities", "backend"}
    if (not isinstance(payload, dict) or not required.issubset(payload)
            or payload["path"] != normalized_path or payload["language"] != grammar[0]
            or payload["status"] not in {"complete", "partial", "unsupported", "failed", "limit-exceeded"}
            or any(not isinstance(payload[key], list) for key in ("symbols", "imports", "calls", "diagnostics"))
            or any(not isinstance(payload[key], dict) for key in ("capabilities", "backend"))):
        return failure("parser-worker-protocol", "Parser worker returned an incompatible index.")
    return payload


def _worker_main() -> int:
    if sys.argv[1:] != ["--worker"]:
        return 2
    try:
        request = json.load(sys.stdin)
        if not isinstance(request, dict) or any(not isinstance(request.get(key), str)
                                               for key in ("path", "text", "source_sha256")):
            return 2
        result = index_source(request["path"], request["text"], source_sha256=request["source_sha256"])
        sys.stdout.write(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception:
        return 2


if __name__ == "__main__":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(_worker_main())
