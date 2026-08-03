---
id: KG-DEC-002-REQ-AUTHORITY
type: decision
title: requirement ノードの正本は ChangeBrief / Gherkin とする
status: active
scope: org.solid_sdd.kg
aliases: []
tags: [kg, phase1]
owner: solid_sdd
confidence: high
verified_at: 2026-08-03
supersedes: []
superseded_by: []
rationale: []
---

# Context

初期の KG 仕様書は `specs/` 文書内アンカーを requirement の記述面としていた。
solid_sdd では ChangeBrief の `in_scope`（R*）と Gherkin Feature が要求の正本であり、別文書で requirement を二重管理すると乖離する。

# Decision

- **要求の正本**: ChangeBrief / Gherkin
- グラフ上の `requirement` / `acceptance_criterion` は Brief / Feature から**インポートされる仮想ノード**
- ID は change スコープ衝突を避けるため `<change_id>/<id>`（例: `initial-reservation/R1`）
- `knowledge/` は更新頻度の低い横断知識（concept / policy / decision / lesson 等）専用
- 知識ノードから要求へのリンクは、上記インポート ID を参照する

# Consequences

- `specs/` に requirement を書く運用は solid_sdd では採用しない
- Phase 1 の dangling 検査は、知識ノード同士に加え Brief 由来 ID への参照も解決できる
