"""Lightweight parser for the solid_sdd Structurizr DSL subset.

See reference-src/structurizr-dsl.md for the authoritative grammar. Summary:

  workspace "Name" ["Description"] {
    model {
      [group "Label" { <softwareSystem decl>* }]
      <id> = softwareSystem "Name" ["Description"] {
        [tags "Tag1, Tag2"]
        [properties { "key" "value" ... }]
        <id> = container "Name" ["Description"] ["Technology"] {
          [tags "..."] [properties { ... }]
          <id> = component "Name" ["Description"] ["Technology"] {
            [tags "..."] [properties { ... }]
            <id> -> <id> ["desc"] ["tech"] { [tags "..."] }
          }
          <id> -> <id> ...
        }
        <id> -> <id> ...
      }
      <id> -> <id> ["desc"] ["tech"] { [tags "..."] }
    }
    views {
      (systemContext|container|component) <id> {
        include (* | <id>+)
        autoLayout [direction]
      }
    }
  }

Identifiers must match ``^[a-z][a-z0-9_]*$`` (underscore, not hyphen —
scripts/solidsdd-architecture/project.py converts underscore to hyphen when
projecting element ids into ArchitecturePlan module ids, which require
``^[a-z0-9]+(-[a-z0-9]+)*$``).

This is a real subset of Structurizr DSL syntax (not an invented dialect),
so a file that only uses this subset also parses with the real Structurizr
CLI, should that ever be introduced as an optional toolchain. Unsupported
constructs (person, deploymentNode, dynamic views, styles, themes,
``!include``, scripting, hierarchical identifiers, ...) raise
DslSyntaxError naming the offending line — fail closed rather than
silently ignoring them.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

IDENT_RE = re.compile(r"^[a-z][a-z0-9_]*$")

ELEMENT_KINDS = ("softwareSystem", "container", "component")
VIEW_KINDS = ("systemContext", "container", "component")


class DslSyntaxError(Exception):
    def __init__(self, message: str, line: int):
        super().__init__(f"line {line}: {message}")
        self.message = message
        self.line = line


@dataclass
class Element:
    id: str
    kind: str  # softwareSystem | container | component
    name: str
    description: str = ""
    technology: str = ""
    tags: list[str] = field(default_factory=list)
    properties: dict[str, str] = field(default_factory=dict)
    parent_id: str | None = None
    line: int = 0


@dataclass
class Relationship:
    source: str
    dest: str
    description: str = ""
    technology: str = ""
    tags: list[str] = field(default_factory=list)
    line: int = 0


@dataclass
class View:
    kind: str  # systemContext | container | component
    element_id: str
    include_all: bool = False
    include_ids: list[str] = field(default_factory=list)
    line: int = 0


@dataclass
class Workspace:
    name: str
    description: str = ""
    elements: dict[str, Element] = field(default_factory=dict)
    relationships: list[Relationship] = field(default_factory=list)
    views: list[View] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(
    r"""
      (?P<STRING>"(?:[^"\\]|\\.)*")
    | (?P<ARROW>->)
    | (?P<LBRACE>\{)
    | (?P<RBRACE>\})
    | (?P<EQUALS>=)
    | (?P<STAR>\*)
    | (?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)
    | (?P<NEWLINE>\n)
    | (?P<SKIP>[ \t\r;]+)
    | (?P<LCOMMENT>//[^\n]*)
    """,
    re.VERBOSE,
)


@dataclass
class Token:
    kind: str
    value: str
    line: int


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    line = 1
    pos = 0
    n = len(text)
    while pos < n:
        if text.startswith("/*", pos):
            end = text.find("*/", pos + 2)
            if end == -1:
                raise DslSyntaxError("unterminated block comment", line)
            line += text.count("\n", pos, end)
            pos = end + 2
            continue
        m = _TOKEN_RE.match(text, pos)
        if not m:
            raise DslSyntaxError(f"unexpected character {text[pos]!r}", line)
        kind = m.lastgroup
        value = m.group()
        if kind == "NEWLINE":
            line += 1
        elif kind in ("SKIP", "LCOMMENT"):
            pass
        else:
            tokens.append(Token(kind, value, line))
        pos = m.end()
    tokens.append(Token("EOF", "", line))
    return tokens


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset: int = 0) -> Token:
        idx = min(self.pos + offset, len(self.tokens) - 1)
        return self.tokens[idx]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.kind != "EOF":
            self.pos += 1
        return tok

    def expect(self, kind: str) -> Token:
        tok = self.peek()
        if tok.kind != kind:
            raise DslSyntaxError(
                f"expected {kind}, found {tok.kind} {tok.value!r}", tok.line
            )
        return self.advance()

    def at_ident(self, text: str) -> bool:
        tok = self.peek()
        return tok.kind == "IDENT" and tok.value == text

    def expect_ident(self, text: str) -> Token:
        if not self.at_ident(text):
            tok = self.peek()
            raise DslSyntaxError(f"expected {text!r}", tok.line)
        return self.advance()

    def string_value(self) -> str:
        tok = self.expect("STRING")
        raw = tok.value[1:-1]
        return raw.replace('\\"', '"').replace("\\\\", "\\")

    def collect_strings(self, max_n: int) -> list[str]:
        out: list[str] = []
        while self.peek().kind == "STRING" and len(out) < max_n:
            out.append(self.string_value())
        return out

    def check_ident_pattern(self, tok: Token) -> None:
        if not IDENT_RE.match(tok.value):
            raise DslSyntaxError(
                f"identifier {tok.value!r} must match ^[a-z][a-z0-9_]*$", tok.line
            )

    # -- workspace ---------------------------------------------------------

    def parse_workspace(self) -> Workspace:
        self.expect_ident("workspace")
        strings = self.collect_strings(2)
        name = strings[0] if strings else ""
        description = strings[1] if len(strings) > 1 else ""
        ws = Workspace(name=name, description=description)
        self.expect("LBRACE")
        seen_model = False
        seen_views = False
        while self.peek().kind != "RBRACE":
            if self.at_ident("model"):
                if seen_model:
                    raise DslSyntaxError("duplicate model block", self.peek().line)
                seen_model = True
                self.advance()
                self.expect("LBRACE")
                self.parse_block(ws, None, 0)
                self.expect("RBRACE")
                continue
            if self.at_ident("views"):
                if seen_views:
                    raise DslSyntaxError("duplicate views block", self.peek().line)
                seen_views = True
                self.advance()
                self.expect("LBRACE")
                self.parse_views_body(ws)
                self.expect("RBRACE")
                continue
            tok = self.peek()
            raise DslSyntaxError(
                f"unsupported workspace-level construct {tok.value!r} "
                "(styles/themes/!include/configuration are not supported)",
                tok.line,
            )
        self.expect("RBRACE")
        self.expect("EOF")
        return ws

    # -- model / element bodies ---------------------------------------------

    def parse_block(self, ws: Workspace, parent: Element | None, depth: int) -> None:
        while True:
            tok = self.peek()
            if tok.kind in ("RBRACE", "EOF"):
                return
            if depth == 0 and self.at_ident("group"):
                self.advance()
                self.string_value()  # group label — informational only in v1
                self.expect("LBRACE")
                self.parse_block(ws, parent, depth)
                self.expect("RBRACE")
                continue
            if depth >= 1 and self.at_ident("tags"):
                self.advance()
                raw = self.string_value()
                assert parent is not None
                parent.tags.extend(p.strip() for p in raw.split(",") if p.strip())
                continue
            if depth >= 1 and self.at_ident("properties"):
                self.advance()
                self.expect("LBRACE")
                assert parent is not None
                self.parse_properties(parent.properties)
                self.expect("RBRACE")
                continue
            if tok.kind == "IDENT" and self.peek(1).kind == "EQUALS":
                self.parse_element_decl(ws, parent, depth)
                continue
            if tok.kind == "IDENT" and self.peek(1).kind == "ARROW":
                self.parse_relationship(ws)
                continue
            raise DslSyntaxError(
                f"unsupported construct {tok.value!r} at this position "
                "(unsupported Structurizr feature, or a statement not valid here)",
                tok.line,
            )

    def parse_element_decl(self, ws: Workspace, parent: Element | None, depth: int) -> None:
        if depth > 2:
            tok = self.peek()
            raise DslSyntaxError(
                "elements cannot be nested deeper than component", tok.line
            )
        expected_kind = ELEMENT_KINDS[depth]
        id_tok = self.advance()
        self.check_ident_pattern(id_tok)
        if id_tok.value in ws.elements:
            raise DslSyntaxError(f"duplicate identifier {id_tok.value!r}", id_tok.line)
        self.expect("EQUALS")
        kind_tok = self.peek()
        if kind_tok.kind != "IDENT" or kind_tok.value != expected_kind:
            raise DslSyntaxError(
                f"expected {expected_kind!r} at this nesting level, found "
                f"{kind_tok.value!r} (person/deploymentNode/other kinds are not "
                "supported)",
                kind_tok.line,
            )
        self.advance()
        max_strings = 2 if expected_kind == "softwareSystem" else 3
        strings = self.collect_strings(max_strings)
        if not strings:
            raise DslSyntaxError(f"{expected_kind} requires a name string", kind_tok.line)
        name = strings[0]
        description = strings[1] if len(strings) > 1 else ""
        technology = strings[2] if len(strings) > 2 else ""
        element = Element(
            id=id_tok.value,
            kind=expected_kind,
            name=name,
            description=description,
            technology=technology,
            parent_id=parent.id if parent else None,
            line=id_tok.line,
        )
        ws.elements[id_tok.value] = element
        if self.peek().kind == "LBRACE":
            self.advance()
            self.parse_block(ws, element, depth + 1)
            self.expect("RBRACE")

    def parse_properties(self, target: dict[str, str]) -> None:
        while self.peek().kind == "STRING":
            key = self.string_value()
            if self.peek().kind != "STRING":
                tok = self.peek()
                raise DslSyntaxError(
                    'properties entries must be "key" "value" pairs', tok.line
                )
            target[key] = self.string_value()

    # -- relationships --------------------------------------------------------

    def parse_relationship(self, ws: Workspace) -> None:
        src_tok = self.advance()
        self.check_ident_pattern(src_tok)
        self.expect("ARROW")
        dst_tok = self.expect("IDENT")
        self.check_ident_pattern(dst_tok)
        strings = self.collect_strings(2)
        description = strings[0] if strings else ""
        technology = strings[1] if len(strings) > 1 else ""
        rel = Relationship(
            source=src_tok.value,
            dest=dst_tok.value,
            description=description,
            technology=technology,
            line=src_tok.line,
        )
        if self.peek().kind == "LBRACE":
            self.advance()
            while self.peek().kind not in ("RBRACE", "EOF"):
                if self.at_ident("tags"):
                    self.advance()
                    raw = self.string_value()
                    rel.tags.extend(p.strip() for p in raw.split(",") if p.strip())
                    continue
                tok = self.peek()
                raise DslSyntaxError(
                    f"unsupported relationship attribute {tok.value!r}", tok.line
                )
            self.expect("RBRACE")
        ws.relationships.append(rel)

    # -- views ---------------------------------------------------------------

    def parse_views_body(self, ws: Workspace) -> None:
        while self.peek().kind not in ("RBRACE", "EOF"):
            tok = self.peek()
            if tok.kind == "IDENT" and tok.value in VIEW_KINDS:
                self.advance()
                elem_tok = self.expect("IDENT")
                view = View(kind=tok.value, element_id=elem_tok.value, line=tok.line)
                self.expect("LBRACE")
                self.parse_view_body(view)
                self.expect("RBRACE")
                ws.views.append(view)
                continue
            raise DslSyntaxError(
                f"unsupported view type {tok.value!r} "
                "(dynamic/deployment/filtered views are not supported)",
                tok.line,
            )

    def parse_view_body(self, view: View) -> None:
        while self.peek().kind not in ("RBRACE", "EOF"):
            if self.at_ident("include"):
                self.advance()
                if self.peek().kind == "STAR":
                    self.advance()
                    view.include_all = True
                else:
                    while self.peek().kind == "IDENT":
                        view.include_ids.append(self.advance().value)
                    if not view.include_ids:
                        tok = self.peek()
                        raise DslSyntaxError(
                            "include requires '*' or one or more identifiers", tok.line
                        )
                continue
            if self.at_ident("autoLayout"):
                self.advance()
                if self.peek().kind == "IDENT":
                    self.advance()  # optional direction (tb/lr/bt/rl)
                continue
            tok = self.peek()
            raise DslSyntaxError(f"unsupported view statement {tok.value!r}", tok.line)


def parse(text: str) -> Workspace:
    tokens = tokenize(text)
    return Parser(tokens).parse_workspace()


def parse_file(path: Path) -> Workspace:
    return parse(path.read_text(encoding="utf-8"))
