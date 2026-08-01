---- MODULE ExclusiveMemory ----
(***************************************************************************)
(* Minimal Phase 3 formal sample for solid_sdd.                            *)
(* Shared calculator-style memory register with exclusive add:             *)
(* each client acquires ownership, increments mem by 1, then releases.     *)
(* Motivates concurrency_safety beyond OCL single-thread posts.            *)
(***************************************************************************)
EXTENDS Integers

CONSTANTS Clients, MaxAdds
VARIABLES mem, owner, remaining

None == 0

ASSUME Clients \in Nat /\ Clients >= 1
ASSUME MaxAdds \in Nat /\ MaxAdds >= 1

TypeOK ==
  /\ mem \in Int
  /\ mem >= 0
  /\ mem <= Clients * MaxAdds
  /\ owner \in {None} \cup (1..Clients)
  /\ remaining \in [1..Clients -> 0..MaxAdds]

Init ==
  /\ mem = 0
  /\ owner = None
  /\ remaining = [c \in 1..Clients |-> MaxAdds]

Acquire(c) ==
  /\ remaining[c] > 0
  /\ owner = None
  /\ owner' = c
  /\ UNCHANGED <<mem, remaining>>

Add(c) ==
  /\ owner = c
  /\ remaining[c] > 0
  /\ mem' = mem + 1
  /\ remaining' = [remaining EXCEPT ![c] = @ - 1]
  /\ owner' = None

Done == \A c \in 1..Clients : remaining[c] = 0

Terminating ==
  /\ Done
  /\ UNCHANGED <<mem, owner, remaining>>

Next ==
  \/ \E c \in 1..Clients : Acquire(c) \/ Add(c)
  \/ Terminating

Spec == Init /\ [][Next]_<<mem, owner, remaining>>

Inv == TypeOK

\* When all clients finish their adds, memory equals the total planned adds.
FinalOK == Done => (mem = Clients * MaxAdds)

====
