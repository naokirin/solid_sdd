"""Deterministic, dependency-free syntax highlighting for solidsdd-report's
HTML Raw panels (JSON / YAML / Gherkin / OCL / GraphQL).

change-report.md asks for generation-time token highlighting with keys and
string values clearly distinguishable, and Gherkin keywords contrasting with
step prose — historically done by hand-wrapping every token in a `<span>`
during report generation. That is pure mechanical work; this module does it
with regexes instead, so the report-writing agent only calls `embed_file`
and pastes the returned HTML, no external highlighter (Pygments et al.)
required and nothing to do at generation time token-by-token.

Token classes (see TOKEN_CSS): tok-key, tok-str, tok-num, tok-bool, tok-null,
tok-punct, tok-comment, tok-kw, tok-tag. Colors are chosen to stay
distinguishable on the report's dark navy/black background without the loud
yellow/chartreuse the spec explicitly avoids.
"""
from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any

TOKEN_CSS = """
.raw-code { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; white-space: pre; }
.tok-key { color: #7ee2f5; }
.tok-str { color: #f2a679; }
.tok-num { color: #a3e6a3; }
.tok-bool, .tok-null { color: #c9a4f5; }
.tok-punct { color: #8a97a8; }
.tok-comment { color: #6b7785; font-style: italic; }
.tok-kw { color: #e0af68; font-weight: 600; }
.tok-tag { color: #82aaff; }
""".strip()

DEFAULT_MAX_BYTES = 100_000

GHERKIN_KEYWORDS = (
    "Feature",
    "Background",
    "Scenario Outline",
    "Scenario",
    "Given",
    "When",
    "Then",
    "And",
    "But",
    "Examples",
    "Rule",
)
OCL_KEYWORDS = (
    "context",
    "inv",
    "pre",
    "post",
    "def",
    "let",
    "in",
    "if",
    "then",
    "else",
    "endif",
    "package",
    "endpackage",
    "self",
    "body",
    "derive",
    "init",
)
GRAPHQL_KEYWORDS = (
    "type",
    "input",
    "enum",
    "interface",
    "union",
    "scalar",
    "schema",
    "query",
    "mutation",
    "subscription",
    "implements",
    "extend",
    "directive",
    "fragment",
    "on",
)

_JSON_TOKEN_RE = re.compile(
    r'(?P<str>"(?:[^"\\]|\\.)*")'
    r"|(?P<num>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)"
    r"|(?P<bool>\btrue\b|\bfalse\b)"
    r"|(?P<null>\bnull\b)"
    r"|(?P<punct>[{}\[\]:,])"
)


def _esc(text: str) -> str:
    return html.escape(text)


def highlight_json(text: str) -> str:
    out: list[str] = []
    pos = 0
    for m in _JSON_TOKEN_RE.finditer(text):
        out.append(_esc(text[pos : m.start()]))
        kind = m.lastgroup
        value = m.group()
        if kind == "str":
            rest = text[m.end() :].lstrip(" \t")
            css = "tok-key" if rest.startswith(":") else "tok-str"
            out.append(f'<span class="{css}">{_esc(value)}</span>')
        elif kind == "num":
            out.append(f'<span class="tok-num">{_esc(value)}</span>')
        elif kind in ("bool", "null"):
            out.append(f'<span class="tok-{kind}">{_esc(value)}</span>')
        else:
            out.append(f'<span class="tok-punct">{_esc(value)}</span>')
        pos = m.end()
    out.append(_esc(text[pos:]))
    return "".join(out)


_YAML_KEY_RE = re.compile(r'^(\s*(?:-\s+)?)("[^"]*"|\'[^\']*\'|[^:#\n]+?)(\s*:)(\s|$)')
_YAML_COMMENT_RE = re.compile(r"(#.*)$")


def highlight_yaml(text: str) -> str:
    lines = text.split("\n")
    out_lines: list[str] = []
    for line in lines:
        working = line
        comment = ""
        cm = _YAML_COMMENT_RE.search(working)
        if cm and (working.count('"', 0, cm.start()) % 2 == 0):
            comment = cm.group(1)
            working = working[: cm.start()]
        km = _YAML_KEY_RE.match(working)
        if km:
            prefix, key, colon, sep = km.groups()
            rendered = (
                f"{_esc(prefix)}"
                f'<span class="tok-key">{_esc(key)}</span>'
                f'<span class="tok-punct">{_esc(colon)}</span>'
                f"{_esc(sep)}"
            )
            remainder = working[km.end() :]
            rendered += _highlight_yaml_scalar(remainder)
        else:
            rendered = _highlight_yaml_scalar(working)
        if comment:
            rendered += f'<span class="tok-comment">{_esc(comment)}</span>'
        out_lines.append(rendered)
    return "\n".join(out_lines)


_YAML_SCALAR_RE = re.compile(
    r'^(?P<lead>\s*)(?P<val>"[^"]*"|\'[^\']*\'|true|false|null|-?\d+(?:\.\d+)?)(?P<trail>\s*)$'
)


_YAML_STRUCTURAL_RE = re.compile(r"^[|>&*!]")


def _highlight_yaml_scalar(text: str) -> str:
    m = _YAML_SCALAR_RE.match(text)
    if m:
        val = m.group("val")
        if val in ("true", "false"):
            css = "tok-bool"
        elif val == "null":
            css = "tok-null"
        elif val.startswith(("'", '"')):
            css = "tok-str"
        else:
            css = "tok-num"
        return f'{_esc(m.group("lead"))}<span class="{css}">{_esc(val)}</span>{_esc(m.group("trail"))}'
    stripped = text.strip()
    if stripped and not _YAML_STRUCTURAL_RE.match(stripped) and not stripped.startswith("-"):
        lead = text[: len(text) - len(text.lstrip())]
        trail = text[len(text.rstrip()) :]
        return f'{_esc(lead)}<span class="tok-str">{_esc(stripped)}</span>{_esc(trail)}'
    return _esc(text)


_GHERKIN_TAG_RE = re.compile(r"^(\s*)(@\S+(?:\s+@\S+)*)\s*$")
_GHERKIN_KEYWORD_RE = re.compile(
    r"^(\s*)(" + "|".join(re.escape(k) for k in GHERKIN_KEYWORDS) + r")(:|\s|$)"
)


def highlight_gherkin(text: str) -> str:
    out_lines: list[str] = []
    for line in text.split("\n"):
        tm = _GHERKIN_TAG_RE.match(line)
        if tm:
            out_lines.append(f'{_esc(tm.group(1))}<span class="tok-tag">{_esc(tm.group(2))}</span>')
            continue
        km = _GHERKIN_KEYWORD_RE.match(line)
        if km:
            lead, kw, sep = km.groups()
            rest = line[km.end() :]
            out_lines.append(
                f'{_esc(lead)}<span class="tok-kw">{_esc(kw)}</span>{_esc(sep)}{_esc(rest)}'
            )
        else:
            out_lines.append(_esc(line))
    return "\n".join(out_lines)


def _keyword_highlight(text: str, keywords: tuple[str, ...], comment_prefix: str | None) -> str:
    kw_re = re.compile(r"\b(" + "|".join(re.escape(k) for k in keywords) + r")\b")
    str_re = re.compile(r'"(?:[^"\\]|\\.)*"')
    out: list[str] = []
    for line in text.split("\n"):
        working = line
        comment = ""
        if comment_prefix:
            idx = working.find(comment_prefix)
            if idx != -1:
                comment = working[idx:]
                working = working[:idx]
        pos = 0
        rendered = ""
        tokens: list[tuple[int, int, str]] = []
        for m in str_re.finditer(working):
            tokens.append((m.start(), m.end(), "str"))
        for m in kw_re.finditer(working):
            if any(a <= m.start() < b for a, b, _ in tokens):
                continue
            tokens.append((m.start(), m.end(), "kw"))
        tokens.sort()
        for start, end, kind in tokens:
            rendered += _esc(working[pos:start])
            css = "tok-str" if kind == "str" else "tok-kw"
            rendered += f'<span class="{css}">{_esc(working[start:end])}</span>'
            pos = end
        rendered += _esc(working[pos:])
        if comment:
            rendered += f'<span class="tok-comment">{_esc(comment)}</span>'
        out.append(rendered)
    return "\n".join(out)


def highlight_ocl(text: str) -> str:
    return _keyword_highlight(text, OCL_KEYWORDS, "--")


def highlight_graphql(text: str) -> str:
    return _keyword_highlight(text, GRAPHQL_KEYWORDS, "#")


_LANG_BY_SUFFIX = {
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".feature": "gherkin",
    ".ocl": "ocl",
    ".graphql": "graphql",
    ".gql": "graphql",
}

_HIGHLIGHTERS = {
    "json": highlight_json,
    "yaml": highlight_yaml,
    "gherkin": highlight_gherkin,
    "ocl": highlight_ocl,
    "graphql": highlight_graphql,
}


def detect_language(path: Path) -> str:
    return _LANG_BY_SUFFIX.get(path.suffix.lower(), "text")


def highlight(text: str, language: str) -> str:
    fn = _HIGHLIGHTERS.get(language)
    if fn is None:
        return _esc(text)
    return fn(text)


def embed_file(path: Path, *, max_bytes: int = DEFAULT_MAX_BYTES, display_path: str | None = None) -> dict[str, Any]:
    """Read + highlight a raw contract/plan file for HTML embedding.

    Truncates at `max_bytes` (default ~100KB per change-report.md) with a
    clear note; the caller is expected to keep the repo-path link regardless.
    """
    raw = path.read_bytes()
    truncated = len(raw) > max_bytes
    if truncated:
        raw = raw[:max_bytes]
    text = raw.decode("utf-8", errors="replace")
    language = detect_language(path)
    return {
        "path": display_path or str(path),
        "language": language,
        "truncated": truncated,
        "original_bytes": path.stat().st_size,
        "html": highlight(text, language),
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json as jsonmod
    import sys

    parser = argparse.ArgumentParser(description="Highlight a raw contract/plan file for report.html embedding")
    parser.add_argument("path", nargs="?", help="File to highlight (omit with --css-only)")
    parser.add_argument("--display-path", help="Path to record in output (default: the input path)")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--out", help="Write result JSON here instead of stdout")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--css-only", action="store_true", help="Print TOKEN_CSS and exit")
    args = parser.parse_args(argv)

    if args.css_only:
        print(TOKEN_CSS)
        return 0
    if not args.path:
        parser.error("path is required unless --css-only is given")

    result = embed_file(Path(args.path), max_bytes=args.max_bytes, display_path=args.display_path)
    indent = 2 if args.pretty else None
    text = jsonmod.dumps(result, indent=indent, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text + ("\n" if args.pretty else ""), encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
