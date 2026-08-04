---- MODULE ConcurrentReserve ----
(***************************************************************************)
(* Bounded concurrency model: soft-hold reserve against one SKU.           *)
(* Concurrent authorized clients each attempt at most one unit; a lock     *)
(* serializes the critical section so last-unit races cannot oversell.     *)
(* Properties: available stock never negative; holds never exceed Stock;  *)
(* stock conservation (holds + available = Stock).                         *)
(***************************************************************************)
EXTENDS Integers, FiniteSets

CONSTANTS Clients, Stock
VARIABLES available, holds, owner, remaining

None == 0

ASSUME Clients \in Nat /\ Clients >= 1
ASSUME Stock \in Nat /\ Stock >= 1

TypeOK ==
  /\ available \in 0..Stock
  /\ holds \subseteq (1..Clients)
  /\ Cardinality(holds) <= Stock
  /\ owner \in {None} \cup (1..Clients)
  /\ remaining \in [1..Clients -> {0, 1}]

Init ==
  /\ available = Stock
  /\ holds = {}
  /\ owner = None
  /\ remaining = [c \in 1..Clients |-> 1]

\* Enter exclusive critical section to attempt a soft-hold.
BeginReserve(c) ==
  /\ remaining[c] = 1
  /\ owner = None
  /\ owner' = c
  /\ UNCHANGED <<available, holds, remaining>>

\* Soft-hold succeeds when stock remains; decrement available.
CommitHold(c) ==
  /\ owner = c
  /\ available > 0
  /\ available' = available - 1
  /\ holds' = holds \cup {c}
  /\ remaining' = [remaining EXCEPT ![c] = 0]
  /\ owner' = None

\* Race loser / insufficient stock: no hold, stock unchanged.
FailInsufficient(c) ==
  /\ owner = c
  /\ available = 0
  /\ remaining' = [remaining EXCEPT ![c] = 0]
  /\ owner' = None
  /\ UNCHANGED <<available, holds>>

Done == \A c \in 1..Clients : remaining[c] = 0

Terminating ==
  /\ Done
  /\ UNCHANGED <<available, holds, owner, remaining>>

Next ==
  \/ \E c \in 1..Clients :
       BeginReserve(c) \/ CommitHold(c) \/ FailInsufficient(c)
  \/ Terminating

vars == <<available, holds, owner, remaining>>

Spec == Init /\ [][Next]_vars

Inv ==
  /\ TypeOK
  /\ available >= 0
  /\ Cardinality(holds) <= Stock
  /\ Cardinality(holds) + available = Stock

\* When every client has finished, holds equal min(Clients, Stock).
FinalOK ==
  Done => (Cardinality(holds) = IF Clients <= Stock THEN Clients ELSE Stock)

====
