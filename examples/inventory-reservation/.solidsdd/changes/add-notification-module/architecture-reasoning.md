# Architecture Reasoning

## Change

add-notification-module

## Design Problem

Hold-expiry notification (which channel, how it's formatted, retry policy)
has nothing to do with hold lifecycle rules (reserve/release/expire/TTL/
authZ), but there is no module today whose responsibility is delivery. If
notification logic gets added inside `reservation`, future delivery-channel
changes (e.g. swapping email for push) would force changes inside the
module that owns hold correctness.

## Logical Decomposition

### Responsibility

Notification is responsible for hold-expiry delivery: channel selection,
formatting, and retry. Reservation stays responsible only for hold
lifecycle correctness.

### State Ownership

Notification owns `NotificationLog` (delivery attempts/outcomes).
Reservation continues to own `Hold`. Notification does not decide when a
hold expires — it reacts to that fact.

### Knowledge Ownership

Delivery-channel formatting/retry rules live in Notification. Reservation
does not know how (or whether) a notification is delivered.

### Change Locality

A future change to delivery channel/format/retry only touches Notification.
A future change to hold TTL/authZ rules only touches Reservation. Today
this example keeps the two reasons for change separate from the start,
rather than waiting for them to tangle inside one file.

## Boundary Decisions

New module `notification`, with `NotificationService` as its public
facade — the only supported way another module observes/consumes
notification state.

## Dependency Decisions

`notification -> reservation`: Notification needs hold-expiry events to
know when to notify, so this dependency is necessary. The direction is
notification depending on reservation, not the reverse — reservation must
stay usable (and testable) with no notification channel configured at all,
so the reverse edge is explicitly forbidden in `invariants.yaml`.

## Alternatives Considered

Adding notification logic directly inside `reservation` was considered and
rejected: it would mean every change to delivery formatting/retry requires
touching the module responsible for hold correctness, which is exactly the
coupling this change is meant to avoid.

## Trade-offs

One more module/facade for what is currently a small sample. Accepted
because the whole point of this example is to show a module boundary
introduced proactively along a change-reason line (delivery vs. lifecycle
correctness), not one added reactively after the two concerns are already
tangled.

## Architecture Invariants

- Notification owns hold-expiry delivery (channel/formatting/retry); it
  does not decide hold lifecycle.
- Reservation must not depend on Notification (`forbid_dependency` in
  `invariants.yaml`).

## Known limitations

Design-only, same as `structure-inventory-reservation-split`: the sample's
implementation intentionally remains a single `reservation.ts` file (see
README "Out of scope").
