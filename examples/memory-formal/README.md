# memory-formal（Phase 3 評価サンプル）

共有メモリレジスタへの **排他的加算** を TLA+ でモデル化し、TLC で検査する最小サンプル。  
arithmetic-api の Memory（OCL）が単一スレッド前提なのに対し、ここは `concurrency_safety` 向け。

## チェッカー

**TLA+ / TLC**（リポジトリ既定。選定理由は [../../tools/tla/README.md](../../tools/tla/README.md)）。

## 成果物

| 種類 | パス |
|------|------|
| TLA+ | `formal/ExclusiveMemory.tla` |
| TLC config | `formal/ExclusiveMemory.cfg` |

## セットアップ

```bash
# リポジトリルートから
tools/tla/fetch-tla2tools.sh   # JDK 17+ が必要
./verify.sh
```

## 性質

- `Inv` / `TypeOK`: メモリ範囲と owner / remaining の型
- `FinalOK`: 全クライアント完了後 `mem = Clients * MaxAdds`

## solid_sdd

- Judge: `kind=formal`, `adapter_hint=tla`, `status=apply` + **human_gate**（早期 Phase 3）
- Apply: `solidsdd-apply-formal`
- Verify: `solidsdd-verify-formal` → 本ディレクトリの `./verify.sh` 相当
