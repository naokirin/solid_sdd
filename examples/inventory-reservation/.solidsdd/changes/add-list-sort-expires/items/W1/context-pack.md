# Context pack — add-list-sort-expires / W1

- WD: `/home/naoki.guest/repos/github.com/naokirin/solid_sdd/examples/inventory-reservation`
- change_id: `add-list-sort-expires` · item_id: `W1` · working language: en
- Prefer this pack; do not re-Read full OpenAPI/OCL/Brief/tests unless editing that file or pack is stale.

## Paths
- Change Context: `.solidsdd/changes/add-list-sort-expires/change-context.md`
- ChangeBrief: `.solidsdd/changes/add-list-sort-expires/change-brief.json`
- WorkPlan: `.solidsdd/changes/add-list-sort-expires/work-plan.json` (N=1 item W1)
- Feature: `requirements/reservation-list-sort-expires.feature`
- Knowledge: POL-OPAQUE-PRINCIPAL-AUTHZ, POL-SOFT-HOLD-SHARED-READ-VISIBILITY, DEC-SOFT-HOLD-LIST-UNFILTERED-FULL-DUMP

## Intent (W1)
Authorized list full dump sorted by expiresAt ascending; UnauthorizedError unchanged; extend OpenAPI/OCL/tests checkability; no filters/paging/DTO.

## Toolchain (use only these)
```
npm_test: mise exec -- npm test
vitest_run: mise exec -- node ".../node_modules/vitest/vitest.mjs" run
openapi_lint: mise exec -- npx --yes @redocly/cli@latest lint openapi/openapi.yaml --extends=spec
```
(Exact commands in `.solidsdd/host-toolchain.json`.)

## Cost skips active
B1–B5 per docs/run-cost.md; parent records cost_skip:B* in isolation_notes.
