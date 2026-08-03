---
id: POL-KG-PERSISTENCE
type: policy
title: 知識層には更新が稀な普遍的知見のみを載せる
status: active
scope: org.solid_sdd
aliases:
  - knowledge permanence
  - ナレッジ永続化方針
tags: [kg]
owner: solid_sdd
confidence: high
verified_at: "2026-08-03"
supersedes: []
superseded_by: []
rationale:
  - KG-DEC-002-REQ-AUTHORITY
---

solid_sdd は change 単位の要求・契約を living documentation として保守しない。
一方、用語定義・横断ポリシー・ADR・教訓など、**機能廃止後も残すべき普遍性の高い知見**は `knowledge/` に独立ノードとして保持する。

## 適用範囲

- concept / policy / invariant / pattern / decision / lesson

## 載せないもの

- 個別 change の in/out of scope や一時的な受入シナリオ全文
- 契約（OpenAPI / OCL）の本文（既存 SoT に任せる）
