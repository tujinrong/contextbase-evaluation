"""Language adapters. Python uses AST; brace languages use conservative token patterns."""
from __future__ import annotations

import ast
import re
from typing import Any
from .common import empty_analysis, pairs, snippet, split_top, tokens
from .sql import sql_facts


def symbol(name: str, kind: str, line: int, end: int, signature: str) -> dict[str, Any]:
    return dict(name=name, kind=kind, line=line, end_line=end, signature=snippet(signature, 1200),
                summary="", parameters=[], returns="未明記", annotations=[], routes=[], steps=[], calls=[])


def python_analysis(text: str, path: str) -> dict[str, Any]:
    result = empty_analysis(path, "Python")
    try:
        tree = ast.parse(text, filename=path)
    except (SyntaxError, RecursionError) as exc:
        result.update(status="error", warnings=[f"Python解析失敗: {type(exc).__name__} / L{getattr(exc, 'lineno', '?')}"])
        return result
    render = lambda node: snippet(ast.unparse(node), 700) if node is not None else "未明記"
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    prefixes = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            for keyword in node.value.keywords:
                if keyword.arg == "prefix" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            prefixes[target.id] = keyword.value.value
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            owners, parent = [], parents.get(node)
            while parent:
                if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    owners.insert(0, parent.name)
                parent = parents.get(parent)
            name = ".".join(owners + [node.name])
            is_class = isinstance(node, ast.ClassDef)
            sig = ("class " + node.name + "(" + ", ".join(render(b) for b in node.bases) + ")") if is_class else (
                ("async " if isinstance(node, ast.AsyncFunctionDef) else "") + "def " + node.name + "(" + ast.unparse(node.args) + ") -> " + render(node.returns))
            record = symbol(name, "class" if is_class else "function", node.lineno, node.end_lineno or node.lineno, sig)
            record["summary"] = snippet(ast.get_docstring(node) or "", 1200)
            record["annotations"] = [render(dec) for dec in node.decorator_list]
            if not is_class:
                # ast.unparse preserves /, *, defaults, and annotations without executing them.
                record["parameters"] = [snippet(ast.unparse(node.args), 1600)] if ast.unparse(node.args) else []
                record["returns"] = render(node.returns)
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                        verb = dec.func.attr.lower()
                        if verb in {"get", "post", "put", "patch", "delete", "options", "head", "route"}:
                            route = dec.args[0] if dec.args else next((k.value for k in dec.keywords if k.arg in {"path", "rule"}), None)
                            if isinstance(route, ast.Constant) and isinstance(route.value, str):
                                methods = [verb.upper()] if verb != "route" else ["未明記（framework依存）"]
                                for kw in dec.keywords:
                                    if kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                                        methods = [str(e.value) for e in kw.value.elts if isinstance(e, ast.Constant)]
                                prefix = prefixes.get(ast.unparse(dec.func.value), "")
                                record["routes"].append(dict(method=",".join(methods), path=prefix + route.value, line=dec.lineno))
            def visit(part: ast.AST, depth: int = 0) -> None:
                if isinstance(part, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                    return
                kind, value = "", ""
                if isinstance(part, (ast.If, ast.While)):
                    kind, value = type(part).__name__, render(part.test)
                elif isinstance(part, (ast.For, ast.AsyncFor)):
                    kind, value = "For", render(part.target) + " in " + render(part.iter)
                elif isinstance(part, (ast.Return, ast.Raise, ast.Assert)):
                    kind, value = type(part).__name__, render(part)
                elif isinstance(part, (ast.With, ast.AsyncWith)):
                    kind, value = "With", ", ".join(render(x.context_expr) for x in part.items)
                elif isinstance(part, ast.ExceptHandler):
                    kind, value = "Except", render(part.type)
                elif isinstance(part, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                    kind, value = "代入", render(part)
                elif isinstance(part, ast.Expr) and isinstance(part.value, ast.Call):
                    kind, value = "呼出", render(part.value)
                elif isinstance(part, (ast.Try, ast.TryStar, ast.Match)):
                    kind, value = type(part).__name__, render(part.subject) if isinstance(part, ast.Match) else "例外処理ブロック"
                if kind:
                    record["steps"].append(dict(kind=kind, text=value, line=getattr(part, "lineno", node.lineno), depth=depth))
                if isinstance(part, ast.Call):
                    record["calls"].append(dict(name=render(part.func), line=part.lineno))
                for child in ast.iter_child_nodes(part):
                    visit(child, depth + (1 if kind in {"If", "For", "While", "Try", "TryStar", "With", "Match"} else 0))
            for child in node.body:
                visit(child)
            result["symbols"].append(record)
            if is_class:
                table_name = None
                for child in node.body:
                    if isinstance(child, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__tablename__" for t in child.targets):
                        if isinstance(child.value, ast.Constant) and isinstance(child.value.value, str):
                            table_name = child.value.value
                if table_name:
                    columns = []
                    for child in node.body:
                        if not isinstance(child, (ast.Assign, ast.AnnAssign)) or not isinstance(child.value, ast.Call):
                            continue
                        call = child.value
                        if render(call.func).split(".")[-1] not in {"Column", "mapped_column"}:
                            continue
                        target = child.target if isinstance(child, ast.AnnAssign) else child.targets[0]
                        attr = render(target)
                        args = list(call.args)
                        col_name = args.pop(0).value if args and isinstance(args[0], ast.Constant) and isinstance(args[0].value, str) else attr
                        kw = {k.arg: k.value for k in call.keywords}
                        nullable = kw.get("nullable")
                        nullable_text = ("NULL明記" if nullable.value else "NOT NULL") if isinstance(nullable, ast.Constant) and isinstance(nullable.value, bool) else "未明記（ORM設定要確認）"
                        pk = kw.get("primary_key")
                        columns.append(dict(name=col_name, type=render(args[0]) if args else "未明記", nullable=nullable_text,
                                            primary_key=isinstance(pk, ast.Constant) and pk.value is True,
                                            default=render(kw.get("server_default") or kw.get("default")), definition=render(child), line=child.lineno))
                    result["tables"].append(dict(name=table_name, columns=columns, constraints=[], indexes=[],
                        line=node.lineno, end_line=node.end_lineno, origin="ORM明示宣言（物理DB未照合）"))
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and not isinstance(parents.get(node), ast.Expr):
            if re.search(r"\b(?:SELECT\s|INSERT\s+INTO|UPDATE\s|DELETE\s+FROM|CREATE\s+TABLE)", node.value, re.I):
                tables, crud, warnings = sql_facts(node.value, node.lineno)
                result["tables"].extend(tables)
                result["crud"].extend(crud)
                result["warnings"].extend(warnings)
        if isinstance(node, ast.JoinedStr):
            if any(isinstance(v, ast.Constant) and isinstance(v.value, str) and re.search(r"\b(SELECT|INSERT|UPDATE|DELETE)\b", v.value, re.I) for v in node.values):
                result["warnings"].append(f"L{node.lineno}: 動的SQL(f-string)を検出。参照表・条件の完全解決は未対応です")
    result["symbols"].sort(key=lambda s: (s["line"], s["name"]))
    return result


def brace_analysis(text: str, path: str, language: str) -> dict[str, Any]:
    result = empty_analysis(path, language)
    result["status"] = "partial"
    result["warnings"].append("トークン・括弧に基づく限定解析です。オーバーロード解決、型推論、DI、継承、動的ルート、ORMマッピングは完全解析していません")
    ts, ranges = tokens(text), []
    pm = pairs(ts)
    control = {"if", "for", "foreach", "while", "switch", "catch", "using", "lock", "with", "synchronized"}
    for i, token in enumerate(ts):
        if token["text"] != "(" or token["kind"] != "symbol" or i not in pm:
            continue
        close = pm[i]
        j = close + 1
        # Typed return values and Java throws clauses may occur before the body.
        while j < len(ts) and j < close + 40 and ts[j]["text"] not in {"{", "=>", ";", "=", ")", ","}:
            j += 1
        if j >= len(ts) or ts[j]["text"] not in {"{", "=>"}:
            continue
        before = ts[i - 1]["text"] if i else ""
        arrow = ts[j]["text"] == "=>"
        if before in control or before in {"new", "return", "throw"}:
            continue
        if not arrow and (i == 0 or ts[i - 1]["kind"] != "word" or (i > 1 and ts[i - 2]["text"] in {".", "?.", "new"})):
            continue
        # Do not mistake invocations inside an already recognized method for definitions.
        if any(start < i < end for start, end in ranges):
            continue
        boundary = i - 2
        while boundary >= 0 and ts[boundary]["text"] not in {";", "}", "{"}:
            boundary -= 1
        begin = boundary + 1
        name = before
        if arrow and (name == "async" or not name or not re.fullmatch(r"[\w$]+", name)):
            assigned = [ts[k - 1]["text"] for k in range(begin + 1, i) if ts[k]["text"] == "="]
            name = assigned[-1] if assigned else f"callback_L{token['line']}"
        if not arrow and (any(t["text"] in {"return", "throw", "new"} for t in ts[begin:i - 1]) or any(ts[k]["text"] == "=" and not any(o < k < e and o >= begin and e < i for o, e in pm.items() if o < e) for k in range(begin, i - 1))):
            continue
        body = j + 1 if arrow and j + 1 < len(ts) and ts[j + 1]["text"] == "{" else j
        if ts[body]["text"] == "{" and body in pm:
            end = pm[body]
        elif arrow:
            end = next((k for k in range(j + 1, len(ts)) if ts[k]["text"] in {";", "}"}), len(ts) - 1)
        else:
            continue
        ranges.append((i, end))
        start_offset = ts[begin]["start"] if begin < len(ts) else token["start"]
        signature = text[start_offset:ts[j]["start"]]
        record = symbol(name, "method/function（限定抽出）", ts[begin]["line"], ts[end]["line"], signature)
        record["parameters"] = [snippet(v) for v in split_top(text[token["end"]:ts[close]["start"]])]
        record["returns"] = "シグネチャ参照（型解決なし）"
        # Adjacent documentation comments, not unrelated comments earlier in the file.
        prefix = text[:start_offset]
        doc = re.search(r"(/\*\*[\s\S]*?\*/|(?:///[^\n]*\n)+)\s*$", prefix)
        if doc:
            record["summary"] = snippet(re.sub(r"/\*\*|\*/|(?m:^\s*\*\s?)|///", "", doc.group(1)), 1200)
        record["annotations"] = [snippet(m.group()) for m in re.finditer(r"@[\w.]+(?:\([^\n]*?\))?|\[[A-Za-z][^\]\n]*\]", signature)]
        # Keep route annotations as written; composing class/base paths is intentionally not guessed.
        for ann in record["annotations"]:
            match = re.search(r"(?:Http(Get|Post|Put|Delete|Patch)|(?:Get|Post|Put|Delete|Patch)Mapping|(?:Get|Post|Put|Delete|Patch))\b", ann, re.I)
            route = re.search(r"['\"]([^'\"]*)['\"]", ann)
            if match:
                record["routes"].append(dict(method=match.group(1).upper() if match.group(1) else "注釈参照",
                    path=(route.group(1) if route else "未明記") + "（クラス側prefix等は未合成）", line=record["line"]))
        for k in range(body + 1, end):
            word = ts[k]["text"]
            if ts[k]["kind"] != "word":
                continue
            if word in control | {"return", "throw", "try", "await"}:
                stop = min(end, k + 24)
                for n in range(k + 1, stop):
                    if ts[n]["text"] in {";", "{"}:
                        stop = n
                        break
                record["steps"].append(dict(kind=word, text=snippet(text[ts[k]["start"]:ts[stop]["start"]]), line=ts[k]["line"], depth=0))
            elif k + 1 < end and ts[k + 1]["text"] == "(" and word not in {"nameof", "typeof", "sizeof"}:
                record["calls"].append(dict(name=word, line=ts[k]["line"]))
        result["symbols"].append(record)
    for token in ts:
        if token["kind"] == "string" and re.search(r"\b(?:SELECT\s|INSERT\s+INTO|UPDATE\s|DELETE\s+FROM|CREATE\s+TABLE)", token["text"], re.I):
            value = token["text"]
            if value.startswith(' @"'.strip()):
                value = value[2:-1].replace('""', '"')
            else:
                value = value[1:-1]
            tables, crud, warnings = sql_facts(value, token["line"])
            result["tables"].extend(tables)
            result["crud"].extend(crud)
            result["warnings"].extend(warnings)
            if "${" in value:
                result["warnings"].append(f"L{token['line']}: テンプレートSQLは動的部分を未解決です")
    if not result["symbols"]:
        result["warnings"].append("抽出できた関数/メソッドはありません。宣言専用・未対応構文を含む可能性があり、機能なしとは判定しません")
    return result


def analyze(text: str, path: str, language: str) -> dict[str, Any]:
    if language == "Python":
        return python_analysis(text, path)
    if language == "SQL":
        result = empty_analysis(path, language)
        result["tables"], result["crud"], result["warnings"] = sql_facts(text)
        if result["warnings"]:
            result["status"] = "partial"
        return result
    return brace_analysis(text, path, language)
