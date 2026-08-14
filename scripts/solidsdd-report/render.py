"""Assemble report.md / report.html directly from collect.py's data.

Moving highlighting/diagramming into scripts (highlight.py, diagram.py)
only pays off if the report-writing agent never has to *transcribe* their
output through its own generation stream. This module is the piece that
makes that true: it writes the files itself. The calling agent supplies a
small "narrative" JSON with only the handful of report sections that
genuinely need LLM synthesis (API contract / DbC / Formal natural-language
summaries, the status-overview paragraph, and — when a Formal spec has an
identifiable mode variable — a simplified state diagram). Everything else
(Brief/NFR/WorkPlan/ArchitecturePlan/ApplicationPlan tables, the coverage
matrix, verbatim Change Context prose, verbatim Gherkin Scenarios, raw
contract embeds) is copied or computed mechanically from what collect.py
already extracted — the report is a *view*, not new authored content, so
most of it never needed an LLM pass in the first place.
"""
from __future__ import annotations

import html
import json
import os
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import collect as collectmod  # noqa: E402
import diagram as diagrammod  # noqa: E402
import highlight as highlightmod  # noqa: E402

HEADINGS = {
    "en": [
        "Status overview",
        "1. Demand and problem",
        "2. Functional requirements",
        "3. Non-functional requirements",
        "4. Technology selection",
        "5. Design",
        "6. Key judgments and trade-offs",
        "7. Open questions",
        "8. Source artifacts",
    ],
    "ja": [
        "ステータス概要",
        "1. 需要と課題",
        "2. 機能要件",
        "3. 非機能要件",
        "4. 技術選定",
        "5. 設計",
        "6. 主要な判断とトレードオフ",
        "7. 未解決の課題",
        "8. 参照アーティファクト",
    ],
}

NOT_PERFORMED_NOTE = {
    "en": "Not performed yet — produced by",
    "ja": "未実施 — 担当スキル:",
}


def _headings(language: str) -> list[str]:
    return HEADINGS.get(language, HEADINGS["en"])


def _esc(text: Any) -> str:
    return html.escape(str(text if text is not None else ""), quote=True)


def _link_root(project_root: Path, change_id: str) -> str:
    """Relative path from the report's own directory back to project_root.

    Every path collect.py returns is project-root-relative (e.g.
    `openapi/openapi.yaml`, `.solidsdd/changes/<id>/work-plan.json`), but
    report.md/report.html live under `.solidsdd/changes/<id>/` — links must
    be resolved from there, not from the project root (see change-report.md
    "Relative links").
    """
    layout = collectmod.load_layout(project_root)
    change_dir = layout.change_dir(change_id)
    return os.path.relpath(str(layout.project_root), start=str(change_dir)).replace(os.sep, "/")


def _href(rel_path: str | None, link_root: str) -> str | None:
    if not rel_path:
        return None
    return f"{link_root}/{rel_path}"


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return ""
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        cells = [str(c).replace("\n", "<br/>").replace("|", "\\|") if c is not None else "" for c in row]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _html_table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return ""
    head = "".join(f"<th>{_esc(h)}</th>" for h in headers)
    body = ""
    for row in rows:
        cells = "".join(f"<td>{_esc(c)}</td>" for c in row)
        body += f"<tr>{cells}</tr>"
    return f'<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


# ---------------------------------------------------------------------------
# Shared row builders (used by both Markdown and HTML renderers)
# ---------------------------------------------------------------------------


def _scope_rows(items: list[dict[str, Any]]) -> list[list[Any]]:
    return [[it.get("id"), it.get("text")] for it in items or [] if isinstance(it, dict)]


def _coverage_rows(matrix: list[dict[str, Any]]) -> list[list[Any]]:
    rows = []
    for row in matrix:
        scenarios = ", ".join(s.get("name") or "" for s in row.get("scenarios") or []) or "—"
        covered_by = ", ".join(row.get("covered_by") or []) or ("**uncovered**" if row["uncovered"] else "—")
        rows.append([row["id"], row.get("text"), covered_by, scenarios])
    return rows


def _nfr_rows(nfr: dict[str, Any] | None) -> list[list[Any]]:
    if not nfr:
        return []
    rows = []
    for item in nfr.get("items") or []:
        rows.append(
            [
                item.get("id"),
                item.get("quality"),
                item.get("status"),
                item.get("requirement"),
                item.get("threshold") or "—",
            ]
        )
    return rows


def _workplan_rows(work_plan: dict[str, Any] | None) -> list[list[Any]]:
    if not work_plan:
        return []
    rows = []
    for it in work_plan.get("items") or []:
        rows.append(
            [
                it.get("id"),
                it.get("intent"),
                ", ".join(it.get("covers") or []),
                it.get("scenario_name") or "—",
                it.get("status"),
                ", ".join(it.get("depends_on") or []) or "—",
            ]
        )
    return rows


def _module_rows(arch: dict[str, Any]) -> list[list[Any]]:
    return [[m.get("id"), m.get("responsibility"), ", ".join(m.get("owns") or []) or "—", ", ".join(m.get("public") or []) or "—"] for m in arch.get("modules") or []]


def _dependency_rows(arch: dict[str, Any]) -> list[list[Any]]:
    return [[d.get("from"), d.get("to"), d.get("reason") or "—", d.get("kind") or "—"] for d in arch.get("dependencies") or []]


def _constraint_rows(arch: dict[str, Any]) -> list[list[Any]]:
    return [[c.get("type"), c.get("from") or "—", c.get("to") or "—", c.get("reason") or "—"] for c in arch.get("constraints") or []]


def _application_rows(application_plans: list[dict[str, Any]]) -> list[list[Any]]:
    rows = []
    for plan in application_plans:
        for t in plan["data"].get("targets") or []:
            rows.append(
                [
                    t.get("kind"),
                    t.get("location"),
                    t.get("density"),
                    t.get("status"),
                    ", ".join(t.get("covers") or []) or "—",
                    t.get("rationale"),
                ]
            )
    return rows


def _diagram_payload_for(kind: str, diagrams: dict[str, Any]) -> dict[str, Any] | None:
    d = diagrams.get(kind)
    if not d or not d.get("eligible"):
        return None
    if kind == "architecture":
        return {"kind": "dependency_graph", "nodes": d["nodes"], "edges": d["edges"], "forbidden_edges": d["forbidden_edges"]}
    if kind == "work_plan":
        return {"kind": "dependency_graph", "nodes": d["nodes"], "edges": d["edges"], "forbidden_edges": []}
    if kind == "application_plan":
        return {"kind": "target_mapping", "left_nodes": d["left_nodes"], "right_nodes": d["right_nodes"], "edges": d["edges"]}
    return None


def _status_overview_rows(data: dict[str, Any], language: str) -> list[list[str]]:
    labels = data["status_labels"]
    sections = data["sections"]
    rows = [
        ["1. Demand and problem", labels[sections["demand"]["state"]], sections["demand"]["owning_skill"]],
        ["2. Functional requirements", labels[sections["functional_requirements"]["state"]], sections["functional_requirements"]["owning_skill"]],
        ["3. Non-functional requirements", labels[sections["non_functional_requirements"]["state"]], sections["non_functional_requirements"]["owning_skill"]],
        ["4. Technology selection", labels[sections["technology_selection"]["state"]], sections["technology_selection"]["owning_skill"]],
    ]
    for key, title in (
        ("work_plan", "5. Design — WorkPlan"),
        ("architecture_plan", "5. Design — ArchitecturePlan"),
        ("application_plan", "5. Design — ApplicationPlan"),
        ("api_contract", "5. Design — API contract"),
        ("dbc", "5. Design — DbC"),
        ("formal", "5. Design — Formal"),
    ):
        d = sections["design"][key]
        rows.append([title, labels[d["state"]], d["owning_skill"]])
    rows.append(["6. Key judgments and trade-offs", labels[sections["key_judgments"]["state"]], sections["key_judgments"]["owning_skill"]])
    rows.append(["7. Open questions", labels[sections["open_questions"]["state"]], "—"])
    return rows


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------


def render_markdown(data: dict[str, Any], narrative: dict[str, Any], project_root: Path) -> str:
    language = narrative.get("language") or data["language_hint"]["value"]
    labels = data["status_labels"]
    h = _headings(language)
    art = data["artifacts"]
    sections = data["sections"]
    diagrams = data["diagrams"]
    link_root = _link_root(project_root, data["change_id"])

    def link(rel_path: str | None) -> str | None:
        return _href(rel_path, link_root)

    out: list[str] = [f"# Change report: {data['change_id']}", ""]

    out += [f"## {h[0]}", ""]
    out.append(_md_table(["Section", "Status", "Owning skill"], _status_overview_rows(data, language)))
    if narrative.get("status_overview"):
        out += ["", narrative["status_overview"]]
    out.append("")

    out += [f"## {h[1]}"]
    if sections["demand"]["state"] == "present":
        text = art["change_context_sections"].get("1", {}).get("text", "")
        drivers = art["change_context_sections"].get("2", {}).get("text", "")
        out += ["", text]
        if drivers:
            out += ["", "**Drivers and constraints**", "", drivers]
    else:
        out += ["", f"{labels['not_performed']} ({sections['demand']['owning_skill']})."]
    out.append("")

    out += [f"## {h[2]}"]
    if sections["functional_requirements"]["state"] == "present":
        brief = art.get("brief")
        if brief:
            for label, key in (("In scope", "in_scope"), ("Out of scope", "out_of_scope"), ("Success criteria", "success_criteria")):
                rows = _scope_rows(brief.get(key) or [])
                if rows:
                    out += ["", f"**{label}**", "", _md_table(["id", "text"], rows)]
        scenarios = art.get("tied_scenarios") or []
        if scenarios:
            out += ["", "**Scenarios**", ""]
            for s in scenarios:
                if s.get("gherkin"):
                    out += ["```gherkin", s["gherkin"], "```", ""]
                if s.get("feature_path"):
                    out += [f"Source: [{s['feature_path']}]({link(s['feature_path'])})", ""]
        cov_rows = _coverage_rows(data["coverage_matrix"])
        if cov_rows:
            out += ["", "**Coverage matrix**", "", _md_table(["id", "text", "covered by", "scenario"], cov_rows)]
    else:
        out += ["", f"{labels['not_performed']} ({sections['functional_requirements']['owning_skill']})."]
    out.append("")

    out += [f"## {h[3]}"]
    if sections["non_functional_requirements"]["state"] == "present":
        nfr_rows = _nfr_rows(art.get("nfr"))
        if nfr_rows:
            out += ["", _md_table(["id", "quality", "status", "requirement", "threshold"], nfr_rows)]
        else:
            out += ["", art["change_context_sections"].get("4", {}).get("text", "")]
    else:
        out += ["", f"{labels['not_performed']} ({sections['non_functional_requirements']['owning_skill']})."]
    out.append("")

    out += [f"## {h[4]}"]
    if sections["technology_selection"]["state"] == "present":
        out += ["", art["change_context_sections"].get("5", {}).get("text", "")]
    else:
        out += ["", f"{labels['not_performed']} ({sections['technology_selection']['owning_skill']})."]
    out.append("")

    out += [f"## {h[5]}"]

    # WorkPlan
    out += ["", "### WorkPlan"]
    if sections["design"]["work_plan"]["state"] == "present":
        wp_diagram = _diagram_payload_for("work_plan", diagrams)
        if wp_diagram:
            rendered = diagrammod.render(wp_diagram)
            out += ["", "```mermaid", rendered["mermaid"], "```"]
        rows = _workplan_rows(art.get("work_plan"))
        out += ["", _md_table(["id", "intent", "covers", "scenario", "status", "depends_on"], rows)]
        if art.get("work_plan_path"):
            out += ["", f"Source: [{art['work_plan_path']}]({link(art['work_plan_path'])})"]
    else:
        out += ["", f"{labels['not_performed']} ({sections['design']['work_plan']['owning_skill']})."]

    # ArchitecturePlan
    out += ["", "### ArchitecturePlan"]
    arch_section = sections["design"]["architecture_plan"]
    if arch_section["state"] == "present":
        arch = art.get("architecture_plan") or {}
        if arch.get("status") == "unchanged":
            out += ["", f"`status: unchanged` — no structural change. {arch.get('summary', '')}"]
        else:
            ad = _diagram_payload_for("architecture", diagrams)
            if ad:
                rendered = diagrammod.render(ad)
                out += ["", "```mermaid", rendered["mermaid"], "```"]
                if diagrams["architecture"].get("no_cycles"):
                    out += ["", "_No dependency cycles required among these modules._"]
            out += ["", "**Modules**", "", _md_table(["id", "responsibility", "owns", "public"], _module_rows(arch))]
            dep_rows = _dependency_rows(arch)
            if dep_rows:
                out += ["", "**Dependencies**", "", _md_table(["from", "to", "reason", "kind"], dep_rows)]
            con_rows = _constraint_rows(arch)
            if con_rows:
                out += ["", "**Constraints**", "", _md_table(["type", "from", "to", "reason"], con_rows)]
        if art.get("architecture_plan_path"):
            out += ["", f"Source: [{art['architecture_plan_path']}]({link(art['architecture_plan_path'])})"]
        if art.get("architecture_reasoning_path"):
            out += ["", f"Why: [{art['architecture_reasoning_path']}]({link(art['architecture_reasoning_path'])})"]
        if art.get("physical_design_path"):
            out += ["", f"Physical design: [{art['physical_design_path']}]({link(art['physical_design_path'])})"]
    else:
        out += ["", f"{labels['not_performed']} ({arch_section['owning_skill']})."]

    # ApplicationPlan
    out += ["", "### ApplicationPlan"]
    if sections["design"]["application_plan"]["state"] == "present":
        ap_diagram = _diagram_payload_for("application_plan", diagrams)
        if ap_diagram:
            rendered = diagrammod.render(ap_diagram)
            out += ["", "```mermaid", rendered["mermaid"], "```"]
        rows = _application_rows(art.get("application_plans") or [])
        out += ["", _md_table(["kind", "location", "density", "status", "covers", "rationale"], rows)]
        for plan in art.get("application_plans") or []:
            out.append(f"\nSource: [{plan['path']}]({link(plan['path'])})")
    else:
        out += ["", f"{labels['not_performed']} ({sections['design']['application_plan']['owning_skill']})."]

    # API contract
    out += ["", "### API contract"]
    if sections["design"]["api_contract"]["state"] == "present":
        out += ["", narrative.get("api_contract_summary") or "_No natural-language summary supplied._"]
        if art.get("openapi_path"):
            out.append(f"\nSource: [{art['openapi_path']}]({link(art['openapi_path'])})")
        if art.get("graphql_path"):
            out.append(f"\nSource: [{art['graphql_path']}]({link(art['graphql_path'])})")
    else:
        out += ["", f"{labels['not_performed']} ({sections['design']['api_contract']['owning_skill']})."]

    # DbC
    out += ["", "### DbC (OCL)"]
    if sections["design"]["dbc"]["state"] == "present":
        out += ["", narrative.get("dbc_summary") or "_No natural-language summary supplied._"]
        for p in art.get("ocl_paths") or []:
            out.append(f"\nSource: [{p}]({link(p)})")
    else:
        out += ["", f"{labels['not_performed']} ({sections['design']['dbc']['owning_skill']})."]

    # Formal
    out += ["", "### Formal"]
    if sections["design"]["formal"]["state"] == "present":
        out += ["", narrative.get("formal_summary") or "_No natural-language summary supplied._"]
        state_data = narrative.get("formal_state_diagram")
        if state_data:
            rendered = diagrammod.render({"kind": "state_diagram", **state_data})
            out += ["", "```mermaid", rendered["mermaid"], "```", "", "_Simplified illustration; see source for full semantics._"]
        for p in art.get("formal_paths") or []:
            out.append(f"\nSource: [{p}]({link(p)})")
    else:
        out += ["", f"{labels['not_performed']} ({sections['design']['formal']['owning_skill']})."]
    out.append("")

    out += [f"## {h[6]}"]
    judgments = art["change_context_sections"].get("6", {}).get("text", "")
    out += ["", judgments] if judgments else ["", f"{labels['not_performed']} ({sections['key_judgments']['owning_skill']})."]
    out.append("")

    out += [f"## {h[7]}"]
    oq = art["change_context_sections"].get("7", {}).get("text", "")
    brief_oq = (art.get("brief") or {}).get("open_questions") or []
    if oq:
        out += ["", oq]
    if brief_oq:
        out += ["", *[f"- {q}" for q in brief_oq]]
    if not oq and not brief_oq:
        out += ["", "None recorded."]
    out.append("")

    out += [f"## {h[8]}", ""]
    out += [f"- [{p}]({link(p)})" for p in data["source_artifacts"]]
    out.append("")

    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

HTML_CSS = """
:root { color-scheme: dark; --bg: #070b14; --panel: #0f1626; --text: #ffffff; --muted: #b7c2d0; --accent: #4dabf7; }
* { box-sizing: border-box; }
body { background: var(--bg); color: var(--text); font-family: system-ui, -apple-system, sans-serif; line-height: 1.55; margin: 0; padding: 2rem clamp(1rem, 4vw, 4rem); }
h1, h2, h3 { border-bottom: 1px solid #1c2536; padding-bottom: 0.3em; }
table { border-collapse: collapse; width: 100%; margin: 0.75em 0; overflow-x: auto; display: block; }
th, td { border: 1px solid #1c2536; padding: 0.4em 0.6em; text-align: left; vertical-align: top; }
th { background: var(--panel); color: var(--text); }
a { color: var(--accent); }
.status-not-performed { color: var(--muted); font-style: italic; }
details.raw { background: var(--panel); border: 1px solid #1c2536; border-radius: 6px; margin: 0.5em 0; padding: 0.5em 0.8em; }
details.raw summary { cursor: pointer; color: var(--accent); }
.raw-note { color: var(--muted); font-size: 0.9em; }
figure.diagram { margin: 0.75em 0; }
"""


def _html_section_or_stub(state_present: bool, owning_skill: str, labels: dict[str, str], body: str) -> str:
    if state_present:
        return body
    return f'<p class="status-not-performed">{_esc(labels["not_performed"])} ({_esc(owning_skill)})</p>'


def _html_raw_panel(path_rel: str, project_root: Path) -> str:
    abs_path = project_root / path_rel
    if not abs_path.is_file():
        return ""
    embedded = highlightmod.embed_file(abs_path, display_path=path_rel)
    note = ""
    if embedded["truncated"]:
        note = f'<p class="raw-note">Truncated ({embedded["original_bytes"]} bytes total) — see source link.</p>'
    return (
        f'<details class="raw"><summary>Raw: {_esc(path_rel)}</summary>'
        f"{note}"
        f'<pre class="raw-code"><code>{embedded["html"]}</code></pre>'
        f"</details>"
    )


def _html_diagram(payload: dict[str, Any] | None) -> str:
    if not payload:
        return ""
    rendered = diagrammod.render(payload)
    svg_part = rendered["svg"] or ""
    return (
        '<figure class="diagram">'
        f"{svg_part}"
        f"<details><summary>Diagram source (Mermaid)</summary><pre>{_esc(rendered['mermaid'])}</pre></details>"
        "</figure>"
    )


def render_html(data: dict[str, Any], narrative: dict[str, Any], project_root: Path) -> str:
    language = narrative.get("language") or data["language_hint"]["value"]
    labels = data["status_labels"]
    h = _headings(language)
    art = data["artifacts"]
    sections = data["sections"]
    diagrams = data["diagrams"]
    link_root = _link_root(project_root, data["change_id"])

    def link(rel_path: str | None) -> str | None:
        return _href(rel_path, link_root)

    body: list[str] = [f"<h1>Change report: {_esc(data['change_id'])}</h1>"]

    body.append(f"<h2>{_esc(h[0])}</h2>")
    body.append(_html_table(["Section", "Status", "Owning skill"], _status_overview_rows(data, language)))
    if narrative.get("status_overview"):
        body.append(f"<p>{_esc(narrative['status_overview'])}</p>")

    body.append(f"<h2>{_esc(h[1])}</h2>")
    demand_body = ""
    if sections["demand"]["state"] == "present":
        text = art["change_context_sections"].get("1", {}).get("text", "")
        drivers = art["change_context_sections"].get("2", {}).get("text", "")
        demand_body = f"<p>{_esc(text)}</p>"
        if drivers:
            demand_body += f"<h3>Drivers and constraints</h3><p>{_esc(drivers)}</p>"
    body.append(_html_section_or_stub(sections["demand"]["state"] == "present", sections["demand"]["owning_skill"], labels, demand_body))

    body.append(f"<h2>{_esc(h[2])}</h2>")
    func_body = ""
    if sections["functional_requirements"]["state"] == "present":
        brief = art.get("brief")
        if brief:
            for label, key in (("In scope", "in_scope"), ("Out of scope", "out_of_scope"), ("Success criteria", "success_criteria")):
                rows = _scope_rows(brief.get(key) or [])
                if rows:
                    func_body += f"<h3>{label}</h3>" + _html_table(["id", "text"], rows)
        scenarios = art.get("tied_scenarios") or []
        if scenarios:
            func_body += "<h3>Scenarios</h3>"
            for s in scenarios:
                if s.get("gherkin"):
                    gh = highlightmod.highlight_gherkin(s["gherkin"])
                    func_body += f'<pre class="raw-code"><code>{gh}</code></pre>'
                if s.get("feature_path"):
                    func_body += f'<p><a href="{_esc(link(s["feature_path"]))}">{_esc(s["feature_path"])}</a></p>'
        cov_rows = _coverage_rows(data["coverage_matrix"])
        if cov_rows:
            func_body += "<h3>Coverage matrix</h3>" + _html_table(["id", "text", "covered by", "scenario"], cov_rows)
    body.append(_html_section_or_stub(sections["functional_requirements"]["state"] == "present", sections["functional_requirements"]["owning_skill"], labels, func_body))

    body.append(f"<h2>{_esc(h[3])}</h2>")
    nfr_body = ""
    if sections["non_functional_requirements"]["state"] == "present":
        nfr_rows = _nfr_rows(art.get("nfr"))
        if nfr_rows:
            nfr_body = _html_table(["id", "quality", "status", "requirement", "threshold"], nfr_rows)
        else:
            nfr_body = f'<p>{_esc(art["change_context_sections"].get("4", {}).get("text", ""))}</p>'
    body.append(_html_section_or_stub(sections["non_functional_requirements"]["state"] == "present", sections["non_functional_requirements"]["owning_skill"], labels, nfr_body))

    body.append(f"<h2>{_esc(h[4])}</h2>")
    tech_body = f'<p>{_esc(art["change_context_sections"].get("5", {}).get("text", ""))}</p>' if sections["technology_selection"]["state"] == "present" else ""
    body.append(_html_section_or_stub(sections["technology_selection"]["state"] == "present", sections["technology_selection"]["owning_skill"], labels, tech_body))

    body.append(f"<h2>{_esc(h[5])}</h2>")

    body.append("<h3>WorkPlan</h3>")
    if sections["design"]["work_plan"]["state"] == "present":
        wp_body = _html_diagram(_diagram_payload_for("work_plan", diagrams))
        wp_body += _html_table(["id", "intent", "covers", "scenario", "status", "depends_on"], _workplan_rows(art.get("work_plan")))
        if art.get("work_plan_path"):
            wp_body += _html_raw_panel(art["work_plan_path"], project_root)
        body.append(wp_body)
    else:
        body.append(_html_section_or_stub(False, sections["design"]["work_plan"]["owning_skill"], labels, ""))

    body.append("<h3>ArchitecturePlan</h3>")
    arch_section = sections["design"]["architecture_plan"]
    if arch_section["state"] == "present":
        arch = art.get("architecture_plan") or {}
        arch_body = ""
        if arch.get("status") == "unchanged":
            arch_body += f'<p><code>status: unchanged</code> — no structural change. {_esc(arch.get("summary", ""))}</p>'
        else:
            arch_body += _html_diagram(_diagram_payload_for("architecture", diagrams))
            if diagrams["architecture"].get("no_cycles"):
                arch_body += "<p><em>No dependency cycles required among these modules.</em></p>"
            arch_body += "<h4>Modules</h4>" + _html_table(["id", "responsibility", "owns", "public"], _module_rows(arch))
            dep_rows = _dependency_rows(arch)
            if dep_rows:
                arch_body += "<h4>Dependencies</h4>" + _html_table(["from", "to", "reason", "kind"], dep_rows)
            con_rows = _constraint_rows(arch)
            if con_rows:
                arch_body += "<h4>Constraints</h4>" + _html_table(["type", "from", "to", "reason"], con_rows)
        if art.get("architecture_plan_path"):
            arch_body += _html_raw_panel(art["architecture_plan_path"], project_root)
        if art.get("architecture_reasoning_path"):
            arch_body += f'<p>Why: <a href="{_esc(link(art["architecture_reasoning_path"]))}">{_esc(art["architecture_reasoning_path"])}</a></p>'
        if art.get("physical_design_path"):
            arch_body += f'<p>Physical design: <a href="{_esc(link(art["physical_design_path"]))}">{_esc(art["physical_design_path"])}</a></p>'
        body.append(arch_body)
    else:
        body.append(_html_section_or_stub(False, arch_section["owning_skill"], labels, ""))

    body.append("<h3>ApplicationPlan</h3>")
    if sections["design"]["application_plan"]["state"] == "present":
        ap_body = _html_diagram(_diagram_payload_for("application_plan", diagrams))
        ap_body += _html_table(["kind", "location", "density", "status", "covers", "rationale"], _application_rows(art.get("application_plans") or []))
        for plan in art.get("application_plans") or []:
            ap_body += _html_raw_panel(plan["path"], project_root)
        body.append(ap_body)
    else:
        body.append(_html_section_or_stub(False, sections["design"]["application_plan"]["owning_skill"], labels, ""))

    body.append("<h3>API contract</h3>")
    if sections["design"]["api_contract"]["state"] == "present":
        api_body = f'<p>{_esc(narrative.get("api_contract_summary") or "No natural-language summary supplied.")}</p>'
        if art.get("openapi_path"):
            api_body += _html_raw_panel(art["openapi_path"], project_root)
        if art.get("graphql_path"):
            api_body += _html_raw_panel(art["graphql_path"], project_root)
        body.append(api_body)
    else:
        body.append(_html_section_or_stub(False, sections["design"]["api_contract"]["owning_skill"], labels, ""))

    body.append("<h3>DbC (OCL)</h3>")
    if sections["design"]["dbc"]["state"] == "present":
        dbc_body = f'<p>{_esc(narrative.get("dbc_summary") or "No natural-language summary supplied.")}</p>'
        for p in art.get("ocl_paths") or []:
            dbc_body += _html_raw_panel(p, project_root)
        body.append(dbc_body)
    else:
        body.append(_html_section_or_stub(False, sections["design"]["dbc"]["owning_skill"], labels, ""))

    body.append("<h3>Formal</h3>")
    if sections["design"]["formal"]["state"] == "present":
        formal_body = f'<p>{_esc(narrative.get("formal_summary") or "No natural-language summary supplied.")}</p>'
        state_data = narrative.get("formal_state_diagram")
        if state_data:
            formal_body += _html_diagram({"kind": "state_diagram", **state_data})
            formal_body += "<p><em>Simplified illustration; see source for full semantics.</em></p>"
        for p in art.get("formal_paths") or []:
            formal_body += _html_raw_panel(p, project_root)
        body.append(formal_body)
    else:
        body.append(_html_section_or_stub(False, sections["design"]["formal"]["owning_skill"], labels, ""))

    body.append(f"<h2>{_esc(h[6])}</h2>")
    judgments = art["change_context_sections"].get("6", {}).get("text", "")
    body.append(f"<p>{_esc(judgments)}</p>" if judgments else _html_section_or_stub(False, sections["key_judgments"]["owning_skill"], labels, ""))

    body.append(f"<h2>{_esc(h[7])}</h2>")
    oq = art["change_context_sections"].get("7", {}).get("text", "")
    brief_oq = (art.get("brief") or {}).get("open_questions") or []
    oq_body = ""
    if oq:
        oq_body += f"<p>{_esc(oq)}</p>"
    if brief_oq:
        oq_body += "<ul>" + "".join(f"<li>{_esc(q)}</li>" for q in brief_oq) + "</ul>"
    body.append(oq_body or "<p>None recorded.</p>")

    body.append(f"<h2>{_esc(h[8])}</h2>")
    body.append("<ul>" + "".join(f'<li><a href="{_esc(link(p))}">{_esc(p)}</a></li>' for p in data["source_artifacts"]) + "</ul>")

    css = HTML_CSS + "\n" + highlightmod.TOKEN_CSS
    title = f"Change report: {html.escape(data['change_id'])}"
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        f"<title>{title}</title><style>{css}</style></head>"
        f"<body>{''.join(body)}</body></html>"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def write_report(
    project_root: Path,
    change_id: str | None,
    narrative: dict[str, Any],
    formats: set[str],
    collected: dict[str, Any] | None = None,
) -> dict[str, str]:
    data = collected or collectmod.collect(project_root, change_id)
    layout = collectmod.load_layout(project_root)
    resolved_root = layout.project_root
    change_dir = layout.change_dir(data["change_id"])
    written: dict[str, str] = {}
    if "markdown" in formats:
        md_path = change_dir / "report.md"
        md_path.write_text(render_markdown(data, narrative, resolved_root), encoding="utf-8")
        written["markdown"] = str(md_path)
    if "html" in formats:
        html_path = change_dir / "report.html"
        html_path.write_text(render_html(data, narrative, resolved_root), encoding="utf-8")
        written["html"] = str(html_path)
    return written


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Render report.md / report.html for solidsdd-report")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--change-id", default=None)
    parser.add_argument("--collected", help="Path to a prior `collect` JSON output (skip re-collecting)")
    parser.add_argument("--narrative", help="Path to narrative JSON (contract/DbC/Formal summaries, status overview)")
    parser.add_argument("--format", default="markdown", choices=["markdown", "html", "both"])
    args = parser.parse_args(argv)

    narrative: dict[str, Any] = {}
    if args.narrative:
        narrative = json.loads(Path(args.narrative).read_text(encoding="utf-8"))
    collected = json.loads(Path(args.collected).read_text(encoding="utf-8")) if args.collected else None
    formats = {"markdown", "html"} if args.format == "both" else {args.format}

    written = write_report(Path(args.project_root), args.change_id, narrative, formats, collected)
    print(json.dumps(written, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
