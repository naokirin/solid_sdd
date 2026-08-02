# Change Context — initial-reservation

## 1. Demand

Build an inventory **soft-hold** reservation API so authorized callers can reserve/release stock with TTL expiry, without payments or multi-warehouse routing.

## 2. Actors & prior art

- Caller principal (opaque id)
- Inventory service
- No prior Features in this sample; greenfield for cross-change checks later

## 3. Functional outline

Reserve → hold reduces availability; release/expire restore; fail closed on authz and stock.

## 4. NFR (projection of `nfr.json`)

See `.solidsdd/changes/initial-reservation/nfr.json` (SoT): reliability (no oversell), security (authz), operability/compatibility/maintainability in scope; performance out of scope.

## 5. Tech selection

Deferred to judge; expect OpenAPI + OCL + derived tests in a follow-on implement change. Framing sample only.

## 6. Key judgments

- Soft holds with TTL (not payment authorization)
- Opaque principal authz stub, not full IAM
- Working language: en (from sample)

## 7. Open questions

None blocking after sample gate approval.

## 8. Links

- Brief: `.solidsdd/changes/initial-reservation/change-brief.json`
- WorkPlan: `.solidsdd/changes/initial-reservation/work-plan.json`
- Features: `requirements/reservation.feature`
- NFR: `.solidsdd/changes/initial-reservation/nfr.json`
- Gate approval: `.solidsdd/changes/initial-reservation/gate-approval.json`
