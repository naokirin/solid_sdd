# 実行モデル（Orchestrator / Subagent）

スキルを「同一エージェントの連続実行」だけにすると、次が起きる。

- 要件が大きいまま 1 本のループに入り、受け入れ条件と成果物のズレが蓄積する
- 適用判断が、後続の実装・修正コストを見越して契約を薄くする方向に偏る
- 実装担当の文脈のまま契約を弱める／テストを実装に合わせて書き換える
- OCL→テスト生成が実装変更と混ざる
- 検証が自己採点になる
- **各フェーズの成果物の良し悪し評価が、そのフェーズを実行したエージェント任せになる**

そのため **呼び出し元がオーケストレータ（`solidsdd.run` / `solidsdd.loop` または同等の親エージェント）のとき**、下表の「Subagent 必須」スキルは、親自身がスキル本体を実行してはならない。Cursor では Task ツール等で **明示的にサブエージェントを起動**し、スキル名と入出力だけを渡す。

加えて、主要フェーズの直後は **`solidsdd.critique`（敵対的評価）を別 Task で必ず起動**する。これは SpecKit の clarify / analyze と同様、品質ゲートを独立コマンドとして分ける構成である。ただし severity は **チェック可能性が失われたときだけ major/fail** とし、標準密度の磨き込みは minor（loop 継続）に留める。詳細はスキル同梱の `adversarial-critique.md`（編集ソース: `reference-src/adversarial-critique.md`）。

手動でユーザーが単一スキルを指定した場合は、その会話エージェントが実行してよい（ユーザーが親になる）。

## 二層オーケストレーション

```text
User or solidsdd.run (outer parent)
  │
  ├─ solidsdd.context                 … parent 可
  ├─ Task: solidsdd.decompose         ← WorkPlan
  ├─ Task: solidsdd.critique          ← subject: work_plan
  ├─ for each ready WorkPlan item:
  │     solidsdd.loop (slice orchestrator; item.intent)
  │       ├─ Task: judge / critique / apply-* / …
  │       └─ Task: verify / critique
  └─ Task: solidsdd.verify            ← integration（acceptance_of_whole）
       └─ Task: solidsdd.critique     ← verification_report
```

- **`solidsdd.run`**: 要件の分解と slice 順実行・統合 verify。loop 内部フェーズを親で再実装しない。
- **`solidsdd.loop`**: **1 slice**（検証可能な受け入れ条件 1 つ／1 変更意図）専用。WorkPlan を知らなくてよい。
- item が 1 つだけの WorkPlan でも、run は loop を **1 回** 回してから統合 verify する。

## 役割分担（slice = `solidsdd.loop`）

```text
User or solidsdd.loop (parent / orchestrator)
  │
  ├─ solidsdd.context              … parent 可（run 配下では省略可）
  │
  ├─ Task: solidsdd.judge          ← subagent 必須（偏り回避）
  ├─ Task: solidsdd.critique       ← subagent 必須（plan の敵対的評価）
  ├─ Task: solidsdd.apply.api      ← subagent 必須
  ├─ Task: solidsdd.critique       ← subagent 必須（API 契約）
  ├─ Task: solidsdd.apply.dbc      ← subagent 必須
  ├─ Task: solidsdd.critique       ← subagent 必須（OCL）
  ├─ Task: solidsdd.derive.tests   ← subagent 必須
  ├─ Task: solidsdd.critique       ← subagent 必須（導出テスト）
  ├─ Task: solidsdd.implement      ← subagent 必須
  ├─ Task: solidsdd.verify         ← subagent 必須
  ├─ Task: solidsdd.critique       ← subagent 必須（検証レポート）
  ├─ Task: solidsdd.apply.formal   ← subagent 必須（Phase 3・ゲート承認後）
  ├─ Task: solidsdd.critique       ← subagent 必須（形式仕様）
  └─ Task: solidsdd.verify.formal  ← subagent 必須（Phase 3）
       └─ Task: solidsdd.critique  ← subagent 必須（形式検証レポート）
```

## スキル別ポリシー

| スキル | 実行ポリシー | 理由 |
|--------|--------------|------|
| `solidsdd.run` | **orchestrator のみ** | 外側の親。サブエージェントに委任しない |
| `solidsdd.loop` | **orchestrator のみ** | slice の親。サブエージェントに委任しない |
| `solidsdd.context` | orchestrator | 以降の計画用。軽い探索は親でよい |
| `solidsdd.decompose` | **subagent 必須** | 作業分解を契約判断・実装から隔離する |
| `solidsdd.judge` | **subagent 必須** | 適用密度の判断を実装文脈から隔離し、契約を薄くする偏りを避ける |
| `solidsdd.critique` | **subagent 必須** | フェーズ成果物を生産者以外が敵対的に評価する（契約の甘さ指摘を含む） |
| `solidsdd.apply.api` | **subagent 必須** | API 契約だけに閉じる。実装やテストと混ぜない |
| `solidsdd.apply.dbc` | **subagent 必須** | OCL だけに閉じる |
| `solidsdd.derive.tests` | **subagent 必須** | OCL→テストの核。実装改変を禁止する隔離が必要 |
| `solidsdd.implement` | **subagent 必須** | 契約を書き換えず実装側だけ直す |
| `solidsdd.verify` | **subagent 必須** | 実装者と同じ文脈での自己採点を避ける |
| `solidsdd.apply.formal` | **subagent 必須** | 形式仕様だけに閉じる（Phase 3） |
| `solidsdd.verify.formal` | **subagent 必須** | モデル検査の自己採点を避ける（Phase 3） |

親は `solidsdd.decompose` / `solidsdd.judge` が返した計画を受け取り、ループ分岐だけを行う。判断そのものは親で再実行・上書きしない。Critique の判定も親で薄めない。

Phase 2 以降、親は次も扱う（詳細はスキル `references/human-gates.md` / `loop-retry.md`）。

- `human_gate.required` が真なら **apply 前に停止**（critique(plan) 通過後でもゲートは有効）。run では WorkPlan ゲートで slice loop 前に停止しうる
- verify / critique fail 時の `loop_action`（`retry` / `human_gate` / `stop`）に従う（既定の自動リトライ上限 3・**オーケストレータ単位の共有予算**。run と各 loop は別予算）

Phase 3: `formal` の `apply` は人間ゲート承認後にのみ `solidsdd.apply.formal` / critique(formal) / `solidsdd.verify.formal` を起動する。`defer` の formal は API/DbC 経路を止めない。

## 敵対的隔離とフィードバック

1. Subagent 必須スキルを親がインライン実行した場合 → `solidsdd.critique`（`subject: isolation`）相当として記録し、**当該スキルを Task で再実行**する（親が成果物を「直して」済ませない）
2. Critique / verify の `retry` → 示唆スキルを **新しい Task** で起動し、該当 subject の critique（および必要なら verify）を再度かける
3. 自動リトライは **最大 3**（verify 失敗・critique 失敗・isolation 再実行を合算）。同一スキル連続で進捗なし、または予算尽きたら `human_gate`
4. 無限ループ禁止: 予算超過後に自動再試行しない

## 親エージェントの義務（`solidsdd.loop`）

1. Subagent 必須スキルを、親のツール実行で「スキル手順を自分でやる」形に落とさない
2. 各 Task に渡すプロンプトへ、対象スキルの `SKILL.md` パス・成果物パス・直前成果（context 要約、ApplicationPlan、critique subject 等）を含める
3. サブエージェントの成果（差分・レポート・ApplicationPlan・CritiqueReport）だけを受け取り、次フェーズへ渡す
4. `ApplicationPlan` / CritiqueReport を親が改変して契約や指摘を薄くしない（誤りなら該当スキルを再度 Subagent で起動）
5. `human_gate.required` なら承認まで apply しない（formal の early rollout を含む）
6. 生産者ステップの直後に対応する `solidsdd.critique` を **省略しない**
7. `solidsdd.verify` / `solidsdd.verify.formal` / `solidsdd.critique` が fail なら、`loop_action` と示唆スキルに従い **再度サブエージェントとして** 起動する（またはゲート／停止）
8. 最大自動リトライを超えたら人間ゲートとして停止する
9. 最終サマリに、各 subagent 必須ステップと critique subject を Task 起動したことの一覧（隔離チェックリスト）を残す

## 親エージェントの義務（`solidsdd.run`）

1. `solidsdd.decompose` / `critique(work_plan)` / 統合 `verify` をインラインでやらない
2. 各 item は **`solidsdd.loop` スキルに従う**（judge/apply/implement を run 親が直接実行しない）
3. `WorkPlan` / CritiqueReport を親が薄めない
4. WorkPlan の human_gate を slice 起動前に尊重する
5. 全 item 完了後に統合 `solidsdd.verify`（+ critique）を省略しない
6. run レベルの retry 予算を守り、最終サマリに隔離チェックリストと blocked items を残す

## サブエージェントへの渡し方（テンプレート）

```text
You are executing the solid_sdd skill: <skill-name>
Read and follow: skills/<skill-dir>/SKILL.md
Working directory: <consuming project root>
Inputs:
  - ...
Constraints:
  - Do only what that skill allows
  - Return: summary, changed files, artifacts (plan/report JSON if any)
```

Critique の場合は必ず `subject` と評価対象パス／抜粋を含める。

## 手動実行時

ユーザーが `solidsdd-derive-tests` だけを呼ぶ場合、現行エージェントが実行してよい。  
ただし **別スキルを続けて同一応答でやる場合**（例: judge のあとすぐ implement）は、混線を避けるため subagent 必須スキルを Task で切ることを推奨する。連続チェインでは生産者の直後に `solidsdd-critique` を Task で挟むことを推奨する。

既に 1 つの検証可能な受け入れ条件だけが分かっている場合は `solidsdd-loop` 単体でよい。要件が複数条件・曖昧な場合は `solidsdd-run` を使う。
