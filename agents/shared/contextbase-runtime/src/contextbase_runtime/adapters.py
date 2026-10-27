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
        "entries": [],
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


def _csharp_entries(root, content, evidence, syntax_id, symbol_ids):
    """Observe registrations and action syntax, without resolving a framework."""
    entries = []
    http_attributes = {'Http' + verb.title(): verb for verb in
                       ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS')}
    map_methods = {'Map' + verb.title(): verb for verb in
                   ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS')}

    def descendants(node):
        stack = [node]
        while stack:
            current = stack.pop()
            yield current
            stack.extend(reversed(current.named_children))

    def literal(node):
        if node is None:
            return None
        # Attribute/call argument wrappers have no semantic interpretation here.
        if node.type in {'argument', 'attribute_argument'}:
            children = node.named_children
            if len(children) != 1:
                return None
            return literal(children[0])
        raw = content(node)
        if node.type == 'verbatim_string_literal' and raw.startswith('@"') and raw.endswith('"'):
            return raw[2:-1].replace('""', '"')
        if node.type != 'string_literal' or not raw.startswith('"') or raw.startswith('"""'):
            return None
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            return None

    def attributes(node):
        values = []
        for group in node.named_children:
            if group.type != 'attribute_list':
                continue
            for attribute in group.named_children:
                if attribute.type != 'attribute':
                    continue
                name_node = attribute.child_by_field_name('name')
                if name_node is None:
                    name_node = attribute.named_children[0] if attribute.named_children else None
                name = content(name_node).split('.')[-1].removesuffix('Attribute')
                arguments = next((n for n in attribute.named_children if n.type == 'attribute_argument_list'), None)
                positional = next((n for n in arguments.named_children if n.type == 'attribute_argument'), None) \
                    if arguments is not None else None
                values.append((name, positional is not None, literal(positional)))
        return values

    def shape(node):
        if node is None:
            return 'unspecified'
        if node.type in {'argument', 'arrow_expression_clause'} and len(node.named_children) == 1:
            return shape(node.named_children[0])
        if node.type in {'lambda_expression', 'anonymous_method_expression'}:
            return shape(node.named_children[-1]) if node.named_children else 'lambda'
        if node.type == 'block':
            return 'block'
        if node.type == 'invocation_expression':
            function = node.child_by_field_name('function')
            target = function.child_by_field_name('name') if function is not None else None
            if content(target or function) == 'NotFound':
                return 'expression-not-found'
        if node.type in {'identifier', 'member_access_expression'}:
            return 'method-group'
        return 'expression'

    def add(node, kind, name, *, symbol=None, verb=None, route=None,
            template_status='not-applicable', handler_shape='unspecified', discriminator='',
            evidence_nodes=None):
        sources = [node] if evidence_nodes is None else evidence_nodes
        locations = [item for source in sources for item in evidence(source)]
        entries.append({'id': syntax_id('entry', node, json.dumps(
                            [kind, verb, route, discriminator], separators=(',', ':'))),
                        'kind': kind, 'name': name, 'symbolId': symbol,
                        'verb': verb, 'route': route, 'templateStatus': template_status,
                        'handlerShape': handler_shape, 'evidence': locations,
                        'resolution': 'unresolved', 'startByte': node.start_byte, 'endByte': node.end_byte})

    def route_value(class_template, action_template):
        class_present, class_value = class_template
        action_present, action_value = action_template
        if action_value is not None and action_value.startswith(('~/', '/')):
            return (action_value[1:] if action_value.startswith('~/') else action_value), 'literal'
        if ((class_present and class_value is None) or (action_present and action_value is None)):
            return None, 'unresolved'
        parts = [value for value in (class_value, action_value) if value is not None]
        if not parts:
            return None, 'unspecified'
        route = parts[0]
        for part in parts[1:]:
            route = route.rstrip('/') + '/' + part.lstrip('/')
        return route, 'literal'

    globals_ = [node for node in root.named_children if node.type == 'global_statement']
    if globals_:
        add(root, 'top-level-program', '<top-level>', handler_shape='top-level', evidence_nodes=globals_)
    for node in descendants(root):
        if node.type == 'method_declaration':
            name = content(node.child_by_field_name('name'))
            modifiers = {content(n) for n in node.named_children if n.type == 'modifier'}
            symbol = symbol_ids.get((node.start_byte, node.end_byte))
            body = node.child_by_field_name('body')
            if body is None:
                body = next((n for n in node.named_children if n.type == 'arrow_expression_clause'), None)
            if name == 'Main' and 'static' in modifiers:
                add(node, 'program-main', name, symbol=symbol, handler_shape=shape(body))
            owner = node.parent
            while owner is not None and owner.type not in {'class_declaration', 'struct_declaration'}:
                owner = owner.parent
            if owner is None or owner.type != 'class_declaration' or 'public' not in modifiers:
                continue
            owner_name = content(owner.child_by_field_name('name'))
            base = next((n for n in owner.named_children if n.type == 'base_list'), None)
            is_controller = owner_name.endswith('Controller') or bool(re.search(
                r'\bController(?:Base)?\b', content(base)))
            if not is_controller:
                continue
            action_attrs = attributes(node)
            class_routes = [(present, value) for attr, present, value in attributes(owner) if attr == 'Route'] \
                or [(False, None)]
            action_routes = [(present, value) for attr, present, value in action_attrs if attr == 'Route']
            for index, (attribute, present, value) in enumerate(action_attrs):
                if attribute not in http_attributes:
                    continue
                templates = [(present, value)] if present else (action_routes or [(False, None)])
                for class_index, class_template in enumerate(class_routes):
                    for action_index, action_template in enumerate(templates):
                        route, status = route_value(class_template, action_template)
                        add(node, 'mvc-action', name, symbol=symbol, verb=http_attributes[attribute],
                            route=route, template_status=status, handler_shape=shape(body),
                            discriminator=f'{index}:{class_index}:{action_index}',
                            evidence_nodes=[n for n in owner.named_children if n.type == 'attribute_list'] + [node])
        elif node.type == 'invocation_expression':
            function = node.child_by_field_name('function')
            if function is None or function.type != 'member_access_expression':
                continue
            name = content(function.child_by_field_name('name'))
            if name not in map_methods and name != 'MapMethods':
                continue
            arguments_node = node.child_by_field_name('arguments')
            if arguments_node is None:
                continue
            arguments = list(arguments_node.named_children)
            if len(arguments) < (3 if name == 'MapMethods' else 2):
                continue
            route = literal(arguments[0])
            verbs = [map_methods[name]] if name in map_methods else []
            if name == 'MapMethods':
                expression = arguments[1].named_children
                if len(expression) == 1 and expression[0].type in {
                        'array_creation_expression', 'implicit_array_creation_expression', 'collection_expression'}:
                    initializer = next((n for n in expression[0].named_children
                                        if n.type == 'initializer_expression'), expression[0])
                    strings = [literal(n) for n in initializer.named_children]
                    if strings and all(value is not None for value in strings):
                        verbs = list(dict.fromkeys(strings))
            for verb in verbs or [None]:
                add(node, 'minimal-route', name, verb=verb, route=route,
                    template_status='literal' if route is not None else 'unresolved',
                    handler_shape=shape(arguments[-1]))
    return entries


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

        def syntax_id(prefix, node, kind):
            value = json.dumps([path.replace('\\', '/'), source_sha256, node.start_byte,
                                node.end_byte, kind], separators=(',', ':'))
            return prefix + ':' + hashlib.sha256(value.encode('utf-8')).hexdigest()

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
        stack = [(root, initial_scope, initial_scope, None, 'top-level')]
        symbol_ids = {}
        visited = 0
        while stack:
            node, names, identities, caller_id, caller_context = stack.pop()
            visited += 1
            if visited > MAX_NODES:
                # No incomplete prefix is exposed as a complete index.
                result.update(status="limit-exceeded", symbols=[], imports=[], calls=[], entries=[])
                result["diagnostics"].append(_diagnostic("node-limit", f"Syntax tree exceeds {MAX_NODES} nodes; index was discarded."))
                return result
            if node.type == "ERROR" or node.is_missing:
                result["diagnostics"].append(_diagnostic(
                    "syntax-error" if node.type == "ERROR" else "missing-syntax",
                    f"{node.type}: {content(node)[:160]}", evidence(node)))
            child_names, child_identities = names, identities
            child_caller, child_context = caller_id, caller_context
            if node.type in {'lambda_expression', 'anonymous_method_expression'}:
                child_context = 'lambda'
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
                    symbol_id = "symbol:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()
                    symbol_ids[(node.start_byte, node.end_byte)] = symbol_id
                    result["symbols"].append({
                        "id": symbol_id,
                        "kind": kind, "name": name, "qualifiedName": qualified_name,
                        "scope": identity_scope, "signature": signature,
                        "startLine": evidence(node)[0]["startLine"],
                        "endLine": evidence(node)[0]["endLine"], "evidence": evidence(node),
                        "startByte": node.start_byte, "endByte": node.end_byte,
                    })
                    child_names = (*names, name)
                    child_identities = (*identities, signature)
                    if kind in {'method', 'constructor', 'local-function', 'property'}:
                        child_caller, child_context = symbol_id, kind
                    elif kind in {'class', 'struct', 'interface', 'record', 'enum', 'annotation'}:
                        # A nested type's initializer is not owned by an enclosing method.
                        child_caller, child_context = None, 'top-level'
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
                    "id": syntax_id('call', node, call_kind),
                    "name": content(target), "receiver": receiver, "text": content(node),
                    "kind": call_kind, "scope": "::".join(identities),
                    "resolution": "unresolved", "evidence": evidence(node),
                    "callerId": caller_id, "callerContext": caller_context,
                    "startByte": node.start_byte, "endByte": node.end_byte,
                    "arity": len(node.child_by_field_name('arguments').named_children)
                        if node.child_by_field_name('arguments') is not None else None,
                })
            for child in reversed(node.children):
                stack.append((child, child_names, child_identities, child_caller, child_context))
        if language == 'csharp':
            result['entries'] = _csharp_entries(root, content, evidence, syntax_id, symbol_ids)
        result["status"] = "partial" if root.has_error else "complete"
        if root.has_error and not result["diagnostics"]:
            result["diagnostics"].append(_diagnostic("syntax-error", "Tree reports a syntax error.", evidence(root)))
        result["capabilities"].update(syntax=True, symbols=True, imports=True, callSites=True)
    except Exception as exc:
        result.update(status="failed", symbols=[], imports=[], calls=[], entries=[])
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
            [sys.executable, "-m", "contextbase_runtime.adapters", "--worker"],
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
            or ('entries' in payload and not isinstance(payload['entries'], list))
            or any(not isinstance(payload[key], dict) for key in ("capabilities", "backend"))):
        return failure("parser-worker-protocol", "Parser worker returned an incompatible index.")
    payload.setdefault('entries', [])
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
