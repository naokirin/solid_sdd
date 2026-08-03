# solidsdd-context summary (add-lookup-available-stock prep)

- **stack**: TypeScript / Node HTTP API; Vitest; OpenAPI + UML OCL
- **active change (prior)**: `add-reservation-lookup` status=done; pointer will switch on intake
- **contracts**: `openapi/openapi.yaml`, `contracts/Reservation.ocl`, `tests/contracts/reservation.test.ts`
- **features**: `requirements/reservation.feature`, `requirements/reservation-lookup.feature`
- **knowledge**: `.solidsdd/kg/` present (schema/config/links); `knowledge/` empty (no policies yet); no consult/harvest for new change yet
- **verify**: `npm test`, `npm start`; lint via `../../scripts/solidsdd-lint.sh --project-root .`
- **gaps**: empty knowledge (expected until harvest); coverage edges warn-only on prior Briefs
- **next**: `solidsdd-run` for `add-lookup-available-stock` — consult then intake
