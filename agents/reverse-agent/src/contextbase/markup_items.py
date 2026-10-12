"""Conservative HTML/Razor item extraction. Never execute input or its scripts.

This is structural extraction, not a full Razor/C# interpreter. Dynamic markup,
partial views, model graphs and database lineage require a reviewed adapter.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from .itemlist import NA, UNKNOWN, TYPES

VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())
CONTROLS = frozenset(("input", "select", "textarea", "button", "output"))


@dataclass(eq=False)
class Node:
    tag: str
    attrs: dict[str, str | None]
    line: int
    parent: "Node | None" = None
    children: list[Any] = field(default_factory=list)

    def text(self) -> str:
        parts = [x.text() if isinstance(x, Node) else x for x in self.children]
        return re.sub(r"\s+", " ", " ".join(parts)).strip()

    def ancestors(self):
        parent = self.parent
        while parent is not None:
            yield parent
            parent = parent.parent


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root", {}, 1)
        self.current = self.root
        self.nodes: list[Node] = []

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs), self.getpos()[0], self.current)
        self.current.children.append(node)
        self.nodes.append(node)
        if tag not in VOID:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        node = self.current
        while node.parent is not None:
            if node.tag == tag:
                self.current = node.parent
                return
            node = node.parent

    def handle_data(self, data):
        self.current.children.append(data)


def mask_csharp_comments(text: str) -> str:
    """Keep string literals but mask comments; preserve line/character offsets."""
    token = re.compile(r'@"(?:""|[^"])*"|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/')
    return token.sub(lambda m: re.sub(r"[^\n]", " ", m[0]) if m[0].startswith(("//", "/*")) else m[0], text)


def property_facts(source: str, path: str) -> dict[str, dict]:
    clean = mask_csharp_comments(source)
    # Restrict to simple annotated auto-properties; don't invent nested model facts.
    pattern = re.compile(r'(?P<attributes>(?:\s*\[[^\]\n]+\]\s*)*)public\s+(?P<type>[\w?.<>\[\]]+)\s+(?P<name>\w+)\s*\{\s*get\s*;\s*(?:set|init)\s*;\s*\}', re.M)
    facts = {}
    for match in pattern.finditer(clean):
        attrs = match["attributes"]
        info = {"type": match["type"], "required": bool(re.search(r"\[\s*(?:\w+\.)*Required(?:Attribute)?\s*(?:\(|\])", attrs)),
                "bound": bool(re.search(r"\[\s*(?:\w+\.)*BindProperty(?:Attribute)?\s*(?:\(|\])", attrs)),
                "line": clean.count("\n", 0, match.start()) + 1, "path": path}
        ran = re.search(r"\bRange\(\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)", attrs)
        if ran:
            info["range"] = ran.groups()
        length = re.search(r"\b(?:StringLength|MaxLength)\(\s*(\d+)", attrs)
        if length:
            info["length"] = length[1]
        # Assignments provide evidence that a bound input is also populated.
        executable = re.sub(r'@"(?:""|[^"])*"|"(?:\\.|[^"\\])*"', lambda m: " " * len(m[0]), clean)
        info["assigned"] = bool(re.search(r"(?<![\w.])" + re.escape(match["name"]) + r"\s*=(?!=)", executable))
        facts[match["name"]] = info
    return facts


def property_graph(source: str, path: str, model_sources: dict[str, tuple[str, str]] | None = None) -> dict[str, dict]:
    """Resolve a bounded graph of uniquely named model files; never execute C#.

    Ambiguous class names must be omitted by the caller. Collections, inheritance
    and custom Tag Helpers remain outside this limited static adapter.
    """
    models = model_sources or {}
    result = property_facts(source, path)
    def descend(prefix, info, seen, depth):
        typ = info.get("type", "").removesuffix("?")
        if depth >= 4 or typ in seen or typ not in models:
            return
        child_text, child_path = models[typ]
        for name, child in property_facts(child_text, child_path).items():
            child = dict(child, bound=info.get("bound", False),
                         assigned=info.get("assigned", False) or child.get("assigned", False))
            key = prefix + "." + name
            result[key] = child
            descend(key, child, seen | {typ}, depth + 1)
    for name, info in list(result.items()):
        descend(name, info, set(), 0)
    return result


def boolean_attribute(attrs, name, *, razor=False):
    """Return true/false/conditional. HTML's literal 'false' is still present."""
    if name not in attrs:
        return "false"
    value = str(attrs[name] or "")
    if razor and value.startswith("@"):
        if value in {"@false", "@(false)", "@null", "@(null)"}:
            return "false"
        if value in {"@true", "@(true)"}:
            return "true"
        return "conditional"
    return "true"


def extract_markup(text: str, path: str, model_text: str = "", model_path: str = "",
                   model_sources: dict[str, tuple[str, str]] | None = None) -> dict:
    # Razor comments may contain fake controls. Mask them without changing lines.
    clean = re.sub(r"@\*[\s\S]*?\*@", lambda m: re.sub(r"[^\n]", " ", m[0]), text)
    if Path(path).suffix.lower()==".jsp":
        # Visible literals in a JSP title are alternatives, not executed branches.
        variables={}
        for match in re.finditer(r'String\s+(\w+)\s*=([^;]+);',clean):
            alternatives=[v for v in re.findall(r'"([^"\n]*)"',match[2]) if re.search(r'[ぁ-ゖァ-ヺ一-鿿]',v)]
            if alternatives:variables[match[1]]='／'.join(dict.fromkeys(alternatives))
        clean=re.sub(r'<%=\s*(\w+)\s*%>',lambda m:variables.get(m[1],m[0]),clean)
        clean=re.sub(r"<%[\s\S]*?%>",lambda m:re.sub(r"[^\n]"," ",m[0]),clean)
        clean=re.sub(r"\$\{[^}]*\}","",clean)
    parser = Tree()
    parser.feed(clean)
    properties = property_graph(model_text, model_path, model_sources) if model_text else {}
    razor = Path(path).suffix.lower() == ".cshtml"
    labels = {}
    for node in parser.nodes:
        if node.tag == "label":
            key = node.attrs.get("for") or node.attrs.get("asp-for")
            if key and node.text():
                labels[str(key)] = node.text()
    items, events, warnings = [], [], []
    warning_codes = set()

    def warn(code, message):
        if code not in warning_codes:
            warning_codes.add(code)
            warnings.append(code + ": " + message)

    for node in parser.nodes:
        if any(parent.tag in {"script", "style", "template"} for parent in node.ancestors()):
            continue
        attrs, tag = node.attrs, node.tag
        operation_link = tag == "a" and bool(attrs.get("href") or attrs.get("asp-page"))
        heading = tag in {"h1", "h2", "h3", "h4", "legend", "th"}
        if tag not in CONTROLS and not operation_link and not heading:
            continue
        typ = str(attrs.get("type") or ("submit" if tag == "button" else "text" if tag == "input" else tag)).lower()
        if typ == "hidden":
            warn("UI-HIDDEN", "非表示値は公開項目一覧に含めず、内部状態として別途確認する。")
            continue
        binding = attrs.get("asp-for") or attrs.get("v-model") or attrs.get("name")
        key = str(binding or attrs.get("id") or "")
        if key.startswith("@Model."):
            key = key[7:]
        elif key.startswith("Model."):
            key = key[6:]
        caption = attrs.get("aria-label") or labels.get(str(attrs.get("id") or "")) or labels.get(key)
        parent_label = next((x for x in node.ancestors() if x.tag == "label"), None)
        if not caption and parent_label:
            caption = parent_label.text()
        operation = operation_link or tag == "button" or (tag == "input" and typ in {"button", "submit", "reset", "image"})
        if not caption and (operation or heading or tag == "output"):
            caption = node.text() or attrs.get("value")
        if not caption and heading and not node.text():
            # Empty table-header cells are spacing/operation columns, not named fields.
            if tag == "th":continue
        if not caption and operation and any("pagination" in str(parent.attrs.get("class", "")) for parent in node.ancestors()):
            caption="ページ番号選択"
        if not caption:
            caption = key or f"表示名未確認（{tag}、{node.line}行）"
            warn("UI-LABEL", "一部の日本語項目名は原本のラベルから確定できない。")
        info = properties.get(key, {})
        if razor and tag == "input" and attrs.get("asp-for") and not attrs.get("type"):
            model_type = info.get("type", "").removesuffix("?").lower()
            native = {"bool": "checkbox", "boolean": "checkbox", "string": "text",
                      "int": "number", "int32": "number", "long": "number", "short": "number",
                      "byte": "number", "float": "number", "double": "number", "decimal": "number",
                      "datetime": "datetime-local"}
            if model_type in native:
                typ = native[model_type]
            elif model_type:
                warn("UI-TYPE", "カスタム型のInput Tag Helperによる部品種別は未確認。")
        readonly = boolean_attribute(attrs, "readonly", razor=razor)
        disabled = boolean_attribute(attrs, "disabled", razor=razor)
        role = "operation" if operation else "static" if heading else "display" if tag == "output" or "true" in {readonly, disabled} else "input"
        if role == "input" and ("v-model" in attrs or (info.get("bound") and info.get("assigned")) or str(attrs.get("value", "")).startswith("@Model.")):
            role = "input_output"
        required_attr = boolean_attribute(attrs, "required", razor=razor)
        required: Any = True if required_attr == "true" or info.get("required") else "条件付き（条件は要確認）" if required_attr == "conditional" else UNKNOWN
        if info.get("required"):
            warn("UI-VALIDATION", "必須のモデル属性は宣言根拠。各保存経路で検証結果を判定するかは別途確認する。")
        if role in {"input", "input_output"} and required == UNKNOWN:
            warn("UI-REQUIRED", "画面だけで必須を確定できない項目がある。業務検証・モデル定義の追加確認が必要。")
        length = attrs.get("maxlength") or info.get("length")
        formats = [f"最大{length}文字"] if length else []
        if typ == "number":
            formats.append("数値")
        elif typ in {"checkbox", "radio"}:
            formats.append("選択／未選択")
        if attrs.get("min") is not None or attrs.get("max") is not None:
            formats.append(f"範囲 {attrs.get('min', '下限未確認')} ～ {attrs.get('max', '上限未確認')}")
        if info.get("range"):
            formats.append(f"数値 {info['range'][0]} ～ {info['range'][1]}")
        choices = NA
        if tag == "select":
            values = [child.text() for child in parser.nodes if child.tag == "option" and node in list(child.ancestors())]
            if values and not any("@" in value for value in values):
                choices = "固定候補：" + "／".join(values)
            else:
                choices = UNKNOWN
                warn("UI-CHOICES", "動的な候補取得元は画面名や項目名からDBへ推測接続しない。")
        description = (f"「{caption}」の操作を受け付ける。業務結果はイベント仕様で確認する。" if operation else
                       f"{caption}を表示する。" if role in {"static", "display"} else
                       f"{caption}を入力・選択する。")
        if attrs.get("pattern"):
            description += " 画面の入力パターン：" + str(attrs["pattern"]) + "。"
        if "formnovalidate" in attrs:
            description += " この操作ではブラウザーのフォーム検証を省略する。サーバー側検証とは別扱い。"
        if readonly == "true":
            description += " 画面からは編集できない。"
        elif readonly == "conditional":
            description += " 条件により編集不可になる。常に出力専用とは扱わない。"
        if disabled == "true":
            description += " 無効化された項目。画面から操作できない。"
        elif disabled == "conditional":
            description += " 条件により操作不可になる。適用条件は要確認。"
        if any("@" in str(v) for v in attrs.values() if v):
            warn("UI-DYNAMIC", "Razor等の動的属性・表示条件は実行せず、静的構造として抽出している。")
        evidence = [{"path": path, "line": node.line}]
        if info:
            evidence.append({"path": info.get("path", model_path), "line": info["line"]})
        items.append({"name": caption, "type": "Button" if operation else "Label" if heading else TYPES.get(typ, TYPES.get(tag, tag)),
                      "role": role, "required": required,
                      "length": "／".join(formats) or UNKNOWN, "choices": choices,
                      "description": description, "line": node.line,
                      "binding": key, "native_type": tag if typ == tag else f"{tag}[type={typ}]",
                      "evidence": evidence})
        if operation:
            handler = str(attrs.get("asp-page-handler") or attrs.get("asp-page") or attrs.get("href") or ("既定フォーム送信" if typ == "submit" else "未確認"))
            events.append({"trigger": str(caption), "handler": handler, "line": node.line})
    if re.search(r"<partial\b|@(?:await\s+)?Html\.Partial|@Render", clean):
        warn("UI-PARTIAL", "共有レイアウト・部分画面の合成は未実施。主画面の項目数へ混在計上しない。")
    warn("UI-SCOPE", "静的抽出。反復行は定義として一度数え、条件分岐・動的HTML・DB対応の完全性は未検証。")
    result = {"items": items, "events": events, "warnings": warnings}
    title_match = re.search(r'ViewData\["Title"\]\s*=\s*"([^"\\\n]+)"\s*;', clean)
    if razor and title_match:
        result["title"] = title_match[1]
    return result
