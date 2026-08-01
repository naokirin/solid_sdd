# 実行モデル（Orchestrator / Subagent）

スキルを「同一エージェントの連続実行」だけにすると、次が起きる。

- 適用判断が、後続の実装・修正コストを見越して契約を薄くする方向に偏る
- 実装担当の文脈のまま契約を弱める／テストを実装に合わせて書き換える
- OCL→テスト生成が実装変更と混ざる
- 検証が自己採点になる

そのため **呼び出し元がオーケストレータ（`solidsdd.loop` または同等の親エージェント）のとき**、下表の「Subagent 必須」スキルは、親自身がスキル本体を実行してはならない。Cursor では Task ツール等で **明示的にサブエージェントを起動**し、スキル名と入出力だけを渡す。

手動でユーザーが単一スキルを指定した場合は、その会話エージェントが実行してよい（ユーザーが親になる）。

## 役割分担

```text
User or solidsdd.loop (parent / orchestrator)
  │
  ├─ solidsdd.context              … parent 可
  │
  ├─ Task: solidsdd.judge          ← subagent 必須（偏り回避）
  ├─ Task: solidsdd.apply.api      ← subagent 必須
  ├─ Task: solidsdd.apply.dbc      ← subagent 必須
  ├─ Task: solidsdd.derive.tests   ← subagent 必須
  ├─ Task: solidsdd.implement      ← subagent 必須
  └─ Task: solidsdd.verify         ← subagent 必須
```

## スキル別ポリシー

| スキル | 実行ポリシー | 理由 |
|--------|--------------|------|
| `solidsdd.loop` | **orchestrator のみ** | 親。サブエージェントに委任しない |
| `solidsdd.context` | orchestrator | 以降の計画用。軽い探索は親でよい |
| `solidsdd.judge` | **subagent 必須** | 適用密度の判断を実装文脈から隔離し、契約を薄くする偏りを避ける |
| `solidsdd.apply.api` | **subagent 必須** | OpenAPI だけに閉じる。実装やテストと混ぜない |
| `solidsdd.apply.dbc` | **subagent 必須** | OCL だけに閉じる |
| `solidsdd.derive.tests` | **subagent 必須** | OCL→テストの核。実装改変を禁止する隔離が必要 |
| `solidsdd.implement` | **subagent 必須** | 契約を書き換えず実装側だけ直す |
| `solidsdd.verify` | **subagent 必須** | 実装者と同じ文脈での自己採点を避ける |

親は `solidsdd.judge` が返した `ApplicationPlan` を受け取り、ループ分岐（どの apply を起動するか等）だけを行う。判断そのものは親で再実行・上書きしない。

## 親エージェントの義務（`solidsdd.loop`）

1. Subagent 必須スキルを、親のツール実行で「スキル手順を自分でやる」形に落とさない
2. 各 Task に渡すプロンプトへ、対象スキルの `SKILL.md` パス・成果物パス・直前成果（context 要約、ApplicationPlan 等）を含める
3. サブエージェントの成果（差分・レポート・ApplicationPlan）だけを受け取り、次フェーズへ渡す
4. `ApplicationPlan` を親が改変して契約を薄くしない（誤りなら `solidsdd.judge` を再度 Subagent で起動）
5. `solidsdd.verify` が fail なら、示唆されたスキルを **再度サブエージェントとして** 起動する
6. 最大ループ回数を超えたら人間ゲートとして停止する

## サブエージェントへの渡し方（テンプレート）

```text
You are executing the solid_sdd skill: <skill-name>
Read and follow: skills/<skill-dir>/SKILL.md
Working directory: <project root or examples/arithmetic-api>
Inputs:
  - ...
Constraints:
  - Do only what that skill allows
  - Return: summary, changed files, artifacts (plan/report JSON if any)
```

## 手動実行時

ユーザーが `solidsdd-derive-tests` だけを呼ぶ場合、現行エージェントが実行してよい。  
ただし **別スキルを続けて同一応答でやる場合**（例: judge のあとすぐ implement）は、混線を避けるため subagent 必須スキルを Task で切ることを推奨する。
