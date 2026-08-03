---
id: KG-DEC-001-IMPL-LANG
type: decision
title: solidsdd-kg は Go + SQLite で実装する
status: active
scope: org.solid_sdd.kg
aliases: []
tags: [kg, phase1]
owner: solid_sdd
confidence: high
verified_at: "2026-08-03"
supersedes: []
superseded_by: []
rationale: []
---

# Context

solid_sdd に「普遍性の高い知識」を要求から独立したグラフとして載せるモジュール（solidsdd-kg）を追加する。
実装言語と派生物ストアを決める必要があった。

# Decision

- 実装言語: **Go**（単一バイナリ配布・CI 実行が容易）
- 派生インデックス: **SQLite**（pure Go ドライバ、削除して再生成可能）
- 設定・スキーマ配置: **`.solidsdd/kg/`**（既存 `.solidsdd` と同居し、`.sdd` との混同を避ける）
- キャッシュ: **`.solidsdd-cache/`**（gitignore）

# Consequences

- リポジトリの他成果物（skills / Python lint）とは別バイナリになる
- Phase 1 では増分ビルドや DuckDB は採用しない
