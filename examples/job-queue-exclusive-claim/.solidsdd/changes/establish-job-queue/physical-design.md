# Physical Design

## Logical Elements

- JobQueue
- ClaimCoordinator
- WorkerPool
- ResultStore

## Physical Realization

| Logical Element | Physical Realization |
|---|---|
| JobQueue | `src/job-queue/` (excluding `claim-coordinator.ts`) |
| ClaimCoordinator | `src/job-queue/claim-coordinator.ts` |
| WorkerPool | `src/worker-pool/` |
| ResultStore | `src/result-store/` |

## Physical Boundaries

- `ClaimCoordinator`はファイルとしては`JobQueue`と同じディレクトリ(`src/job-queue/`)配下に
  あるが、独立したモジュール境界(`claim-coordinator.ts`が唯一の入口)として扱う。`JobQueue`の
  他コードは`ClaimState`へ直接アクセスしない。
- プロセス/サービス境界: ChangeBriefの前提により、ワーカーは別々のOSプロセス、あるいは別々の
  マシンで動作しうる。したがって`ClaimCoordinator`の直列化を、単一の常駐コーディネータ
  プロセス(すべてのクレーム要求を一箇所で処理するプロセス)で強制する案と、共有ストアへの
  アトミックな条件付き更新(compare-and-swap 相当)で強制する案の両方が構造的に成立する。
  本changeでは後者(共有ストアのアトミック操作)を選ぶ: 専用の常駐コーディネータサービスを
  新たに導入せずに済み、ワーカー数のスケールに対してコーディネータ自体がボトルネック/単一
  障害点にならない。この決定はNFR1の形式検証(`formal/ClaimCoordinator.tla`、本changeでは
  未作成)が検証すべき遷移プロパティの前提になる。
- データベース境界: `JobQueue`と`ClaimCoordinator`は同一のジョブストレージ(同じレコード/行)
  を共有する。`ClaimCoordinator`のアトミック操作は、`JobQueue`が保持するジョブレコードの
  クレームフィールドに対する条件付き更新として実現され、別ストアを新設しない。`ResultStore`
  は`JobQueue`/`ClaimCoordinator`とは別のストレージを持つ — 結果はジョブIDをキーとする別個の
  エンティティであり、クレーム排他性のような整合性要件がR3には明記されていないため。

## Physical Dependencies

- `src/worker-pool/` -> `src/job-queue/claim-coordinator.ts`
- `src/worker-pool/` -> `src/result-store/`
