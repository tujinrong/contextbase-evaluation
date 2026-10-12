"""Generate numbered human procedures from the control tree, not diagram order.

Graph layout is built backwards from exits. Sorting those graph nodes by source
line is not program order: an if, its call and its return can share one line.
Keep branch hierarchy explicit, and do not claim both alternatives always run.
"""
from __future__ import annotations
from typing import Any
import re



def field_condition(narrator: Any, expression: str) -> str | None:
    """Translate only explicit null/empty getter comparisons; do not infer rules."""
    match = re.fullmatch(r"\w+\.(?:get|is)([A-Z]\w*)\(\)\s*(==|!=)\s*null", expression.strip())
    if match:
        label = narrator.field(match[1])
        return "「" + label + "」" + ("が未設定" if match[2] == "==" else "が設定されている")
    match = re.fullmatch(r"\w+\.(?:get|is)([A-Z]\w*)\(\)\.length\(\)\s*(==|!=)\s*0", expression.strip())
    if match:
        return "「" + narrator.field(match[1]) + "」" + ("が空" if match[2] == "==" else "が空ではない")
    return None


def procedure_steps(narrator: Any, event: dict[str, Any]) -> list[dict[str, Any]]:
    """Return display steps with stable hierarchical numbers and source anchors.

    This function only projects the already parsed control tree. It does not
    infer new SQL, bindings, branch conditions, or exception propagation.
    """
    methods = event.get("methods", [])
    if not methods:
        return [{"number": "1", "description": "定義された操作を受け付ける。詳細な実行経路は原本対応を参照する", "line": None, "kind": "unresolved"}]
    method = methods[0]
    result: list[dict[str, Any]] = []

    def add(number: str, description: str, node: dict, branch: str = "") -> None:
        result.append({"number": number, "description": description.rstrip("。"),
                       "line": node.get("line"), "kind": node.get("kind", "unknown"),
                       "branch": branch, "guards": list(node.get("guards", []))})

    def walk(nodes: list[dict], prefix: str = "", branch: str = "",
             cleanup: bool = False, depth: int = 0) -> None:
        if depth > 24:
            add(prefix + "1", "深い入れ子の処理は詳細仕様の原本対応を参照する", {"kind": "unresolved"}, branch)
            return
        serial = 0
        index = 0
        while index < len(nodes):
            node = nodes[index]
            index += 1
            kind = node.get("kind", "unknown")
            phrase = narrator.statement(node) if kind not in {
                "if", "for", "foreach", "while", "try", "catch", "finally",
                "using", "lock", "synchronized", "switch"} else ""
            if not phrase and kind not in {
                "if", "for", "foreach", "while", "try", "catch", "finally",
                "using", "lock", "synchronized", "switch"}:
                continue
            serial += 1
            number = prefix + str(serial)
            lead = (branch + "：") if branch else ""
            if kind == "if":
                condition = narrator.condition(node.get("condition", ""))
                tail = "成立時と不成立時の手順を分けて行う" if node.get("else") else "該当する場合に限り、次の分岐内手順を行う。該当しない場合は分岐の後へ進む"
                add(number, lead + "「" + condition + "」に該当するか確認する。" + tail, node, branch)
                walk(node.get("body", []), number + ".", "条件成立時", cleanup, depth + 1)
                alternate = node.get("else", [])
                if alternate:
                    walk(alternate, number + "-別.", "条件不成立時", cleanup, depth + 1)
                # No else means continuation, not an invented action.
            elif kind in {"for", "foreach", "while"}:
                condition = narrator.condition(node.get("condition", ""))
                add(number, lead + "繰返し条件「" + condition + "」に従い、次の手順を繰り返す。条件を満たさなくなった場合は繰返しの後へ進む", node, branch)
                walk(node.get("body", []), number + ".", "繰返しの各回", cleanup, depth + 1)
            elif kind == "try":
                catches = list(node.get("catches", []))
                after = list(node.get("cleanup", []))
                while index < len(nodes) and nodes[index].get("kind") == "catch":
                    catches.append(nodes[index]); index += 1
                if index < len(nodes) and nodes[index].get("kind") == "finally":
                    after = list(nodes[index].get("body", [])); index += 1
                add(number, lead + "通常処理と例外時の処理を区別して実行する。例外処理は対応する例外が発生した場合に限る", node, branch)
                walk(node.get("body", []), number + ".", "通常処理", bool(after) or cleanup, depth + 1)
                for catch_no, handler in enumerate(catches, 1):
                    hnum = number + "-例外" + str(catch_no)
                    detail = handler.get("condition", "")
                    add(hnum, "例外条件「" + detail + "」に該当した場合に次の手順を行う。型名は原本の表記", handler, "例外発生時")
                    walk(handler.get("body", []), hnum + ".", "例外発生時", bool(after) or cleanup, depth + 1)
                if after:
                    hnum = number + "-後処理"
                    add(hnum, "通常終了・例外・途中のreturnのいずれでも、この範囲を抜ける前に次の共通後処理を行う", {"kind": "finally", "line": node.get("line")})
                    walk(after, hnum + ".", "終了時の共通後処理", cleanup, depth + 1)
            elif kind in {"using", "lock", "synchronized", "finally"}:
                title = {"using": "資源の有効範囲内", "lock": "排他制御の範囲内",
                         "synchronized": "排他制御の範囲内", "finally": "終了時の共通後処理"}[kind]
                add(number, lead + title + "で次の手順を実行する", node, branch)
                walk(node.get("body", []), number + ".", title, cleanup, depth + 1)
            elif kind in {"catch", "switch"}:
                description = "値に応じた分岐の詳細は原本対応を参照する" if kind == "switch" else "この例外に該当した場合の処理を行う。接続する例外経路は原本対応を参照する"
                add(number, lead + description, node, branch)
            else:
                if kind in {"return", "throw"}:
                    phrase = ("終了時の共通後処理を行ってから、" if cleanup else "") + phrase + "。この経路の後続手順は実行しない"
                add(number, lead + phrase, node, branch)

    tree = method.get("flow")
    if tree:
        walk(tree)
    else:
        # Flat extraction cannot prove nesting. Keep the guards on every action
        # and explicitly mark the limited ordering evidence.
        for node in method.get("steps", []):
            if node.get("kind") == "if":
                phrase = "分岐条件「" + narrator.condition(node.get("condition", "")) + "」を確認する"
            else:
                phrase = narrator.statement(node)
            if not phrase:
                continue
            guards = [narrator.condition(g) for g in node.get("guards", []) if g not in {"try", "finally"}]
            if guards:
                phrase = "条件「" + "、かつ".join(guards) + "」のもとで、" + phrase
            add(str(len(result) + 1), phrase, node, "平坦抽出・詳細な接続は原本対応を参照")
    return result or [{"number": "1", "description": "関連する処理へ制御を渡す。詳細な実行経路は原本対応を参照する", "line": None, "kind": "unresolved"}]
