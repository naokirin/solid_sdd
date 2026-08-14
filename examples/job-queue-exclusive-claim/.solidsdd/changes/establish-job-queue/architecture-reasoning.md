# Architecture Reasoning

## Change

establish-job-queue

## Design Problem

これはプロジェクト最初のArchitecture Modelである。複数のプロデューサーがジョブを投入し、
複数の並行ワーカー(別々のOSプロセス、あるいは別々のマシンで動作しうる)がそれらをクレーム・
処理する。核心の構造的問題は、同一ジョブに対する並行クレーム試行があっても成功するクレームが
常にちょうど1件になることを、どのモジュールがどう保証するかである(R2/NFR1/SC1/SC2)。

## Decision Drivers

- クレーム状態(あるジョブが誰にクレームされているか)には単一の所有者が必要で、他のモジュール
  がそれを直接変更してはならない。
- 並行クレーム試行は、呼び出し元のワーカーがいくつのプロセス/マシンに分散していても、1つの
  権威の中で直列化されなければならない。
- WorkerPoolはJob/クレーム状態を直接変更してはならず、ClaimCoordinatorが提供する排他的な
  クレーム操作を通じてのみクレームを要求できる。
- ジョブ投入(R1)と結果記録(R3)には二重クレームのような排他性要件が明示されておらず、
  クレーム排他性(R2)と同じ整合性境界を共有する必要はない。

## Logical Decomposition

### Responsibility

- `JobQueue`: ジョブ投入を受け付け、ペイロードと存在(未クレームジョブ)を保持する。
- `ClaimCoordinator`(`JobQueue`内のcontainer): 同一ジョブへの並行クレーム試行を直列化し、
  ちょうど1件だけを成功させる排他的クレームプロトコルを所有する。
- `WorkerPool`: 並行して稼働する複数ワーカーを表し、クレームを試み、処理結果を記録する。
- `ResultStore`: 完了したジョブの結果を記録し、ジョブIDで取得可能にする。

### State Ownership

`JobQueue`は`Job`(ID・ペイロード・存在)を所有する。`ClaimCoordinator`は`ClaimState`
(あるジョブが誰にクレームされているか)を所有する。両者を分離するのは、クレーム排他性の
安全性要件(R2/NFR1)がクレーム遷移そのものにのみ適用され、投入(R1)やペイロード保持には
適用されないためである。`ResultStore`は`JobResult`をジョブIDをキーとして所有し、クレーム前の
`Job`状態とは別のエンティティとして扱う(R3に二重クレーム相当のリスクは明記されていない)。

### Knowledge Ownership

「あるジョブについて成功するクレームはちょうど1件」というルールは`ClaimCoordinator`にのみ
保持される。ワーカー自身がクレームの成否をローカルに判定することはなく、常に
`ClaimCoordinator`へ問い合わせ、権威ある回答(成功、または「既にクレーム済み」)を受け取る
(W2の受け入れ条件と一致)。

### Change Locality

将来のスケジューリング/優先度ポリシー変更(X1、対象外)は`JobQueue`/`ClaimCoordinator`
内に留まり、`WorkerPool`/`ResultStore`へは波及しない。将来のリトライ/デッドレター処理
(X2、対象外)は`WorkerPool`/`ResultStore`側の関心であり、投入(R1)ロジックへは波及しない。
この境界により、投入(R1)・クレーム(R2)・結果記録(R3)それぞれの変更理由が他へ漏れ出さない。

### Consistency Boundary

「あるジョブが今どのワーカーにクレームされているか」という状態は、並行呼び出し元をまたいで
一貫している必要がある。これが`ClaimCoordinator`を`JobQueue`のペイロード保持から分離した
境界として独立させる理由であり、ペイロード自体はクレーム判定と同じ厳密な整合性を必要としない。

### Concurrency Boundary

`ClaimCoordinator`が並行クレーム試行を直列化する場所である。これは構造的な決定(誰がクレーム
可否を判定する権威を持つか、どのサーフェス経由か)であり、遷移の正確な意味論(TLA+が検証する
安全性プロパティそのもの)ではない。ChangeBriefの前提「ワーカーは別々のOSプロセス、あるいは
別々のマシンで動作する可能性がある」により、`ClaimCoordinator`の直列化を実際に何が強制するか
(単一の常駐プロセスか、共有ストアのアトミック操作か、分散ロックサービスか)はLogicalモデルだけ
では決まらない — [Physical Design](physical-design.md)で扱う。

## Boundary Decisions

4つの要素: `job_queue`(`claim_coordinator`をcontainerとして内包)、`worker_pool`、
`result_store`。WorkPlanの`touches`が示す3つの変更局所性クラスタ(`src/job-queue/**`、
`src/worker-pool/**`、`src/result-store/**`)にR1/R2/R3が対応する。`claim_coordinator`は
`job_queue`ディレクトリ配下に物理的に置かれる(`src/job-queue/claim-coordinator.ts`)ものの、
その排他性責務はNFR1の独立した形式検証対象(`formal/ClaimCoordinator.tla`)であり、
`JobQueue`の「SubmitJob」とは別の公開サーフェス「ClaimJob」を持つため、独立したLogical要素
として名前を与える。

## Dependency Decisions

- `worker_pool -> claim_coordinator`: ワーカーは排他的クレームを要求する。この方向でのみ
  `ClaimCoordinator`がクレーム判定の唯一の権威であり続けられる。逆方向(`ClaimCoordinator`が
  `WorkerPool`に依存)ではワーカー側にクレーム判定の主導権が移り、排他性を中央で保証できない。
- `worker_pool -> result_store`: ワーカーはクレーム成功後の処理完了時に結果を記録する。
  `ResultStore`が`WorkerPool`に依存する逆方向にすると、結果保存が「誰が結果を作ったか」に
  結合してしまい、ジョブIDによる単純な記録・取得の責務から外れる。
- `invariants.yaml`に`forbid_dependency(worker_pool -> job_queue)`を追加した: `WorkerPool`が
  `JobQueue`の投入サーフェスを直接呼び出す正当な理由はなく、クレームは常に
  `ClaimCoordinator`経由でなければならないという排他性の決定を、機械的に検査可能な制約として
  固定する。

## Alternatives Considered

- `ClaimCoordinator`を独立させず`JobQueue`に統合する案: 却下。投入(R1、排他性要件なし)と
  クレーム排他性(R2/NFR1、形式検証対象)という異なる関心を混在させてしまい、Physical Design
  で扱う「直列化を実際に何が強制するか」という判断も曖昧になる。
- `WorkerPool`がクレーム状態を直接所有・判定する案: 却下。単一の権威が存在しなくなり、
  R2/SC2が求める構造的な排他性の保証が成立しない。

## Trade-offs

`ClaimCoordinator`を`JobQueue`内の独立したcontainerとして切り出すことで、「投入」と地続きの
概念に1段階の内部境界が増える。その代わりに、TLA+検証の対象範囲を投入ロジックから切り離せる、
明確な形式検証単位を得られる。

## Architecture Invariants

- ClaimCoordinatorのみがJobを未クレームからクレーム済みへ遷移させる権限を持つ(単一の権威)。
- 任意の時点で、あるジョブに対して成功したクレームはちょうど1件である(排他制御、NFR1)。
- JobQueueが所有するJob(ペイロード/存在)とClaimCoordinatorが所有するClaimStateは別個の
  関心事であり、投入(R1)の変更はクレーム排他性(R2)のロジックへ波及しない。

## Where each layer picks up from here

- **Architecture**(このファイル + `workspace.dsl`): *どのモジュール*が`ClaimState`を所有し、
  クレームは常に`ClaimCoordinator`の排他的サーフェスを経由しなければならないこと。
- **BDD**([`requirements/job-queue.feature`](../../../requirements/job-queue.feature)):
  Given/When/Then形式での振る舞い — 2人のワーカーが同時にクレームを試み、1人だけが成功する。
- **TLA+**(`formal/ClaimCoordinator.tla`、本changeでは未作成 — NFR1の測定方法として予定):
  「並行クレーム試行に対して二重成功が0件である」という厳密な状態/遷移プロパティを形式検証する。

Architectureは*どのモジュールが状態を所有し、境界がどこにあるか*を述べ、TLA+は*正確な遷移
意味論*を述べる。どちらも他方の代わりにはならない([architecture-axes.md](../../../../../../skills/solidsdd-architecture/references/architecture-axes.md)のRole separationを参照)。
