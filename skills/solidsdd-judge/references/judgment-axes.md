# Judgment axes (MVP)

| Signal | Prefer |
|--------|--------|
| HTTP boundary / compatibility | `api` + `openapi`, status `apply` |
| Domain pre/post/invariants | `dbc` + `ocl`, status `apply` |
| Concurrency / deep safety proofs | `formal`, status `defer` (MVP) |
| Exploratory / unstable UX-only | `natural_only` or thin density |

Judge from risk and boundary axes, not from how hard implementation would be.
Never silently drop formal needs—use `defer` with rationale.
