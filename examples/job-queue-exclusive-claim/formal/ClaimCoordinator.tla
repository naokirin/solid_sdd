---- MODULE ClaimCoordinator ----
(***************************************************************************)
(* Phase 3 formal spec for change establish-job-queue.                     *)
(*                                                                         *)
(* Scope (per application-plan.json's formal target and NFR1 in nfr.json): *)
(* model ONLY the concurrency-safety property of ClaimCoordinator::claimJob*)
(* under interleaved calls from multiple workers -- "even under concurrent *)
(* claim attempts, the successful claim on a given job is always exactly  *)
(* one" (NFR1 / R2 / SC1 / SC2). Job submission (W1) and result recording  *)
(* (W3) are out of scope for this formal spec (application-plan.json:      *)
(* "Do not model job submission or result recording"); their single-call   *)
(* pre/post shape is covered by contracts/JobQueue.ocl instead. OCL also   *)
(* covers claimJob's own single-call pre/post shape (unclaimed -> claimed, *)
(* or a named AlreadyClaimed failure); this spec exists only to cover what *)
(* OCL structurally cannot express: safety across interleaved calls.       *)
(*                                                                         *)
(* Realization modeled (physical-design.md "Physical Boundaries"): the     *)
(* project chose exclusivity via an atomic conditional update (CAS) on the *)
(* shared job storage's claim field -- NOT a dedicated resident coordinator*)
(* process/lock service. Claim(w, j) below is therefore modeled as a       *)
(* single atomic TLA+ action whose guard (job not yet claimed by anyone)   *)
(* and write (record the successful claim) occur in one indivisible step,  *)
(* matching a compare-and-swap primitive -- there is deliberately no       *)
(* separate "owner"/lock variable representing a serialized critical       *)
(* section, since that would model a different (rejected) realization.    *)
(***************************************************************************)
EXTENDS Integers, FiniteSets

CONSTANTS Workers, Jobs
VARIABLES claims

ASSUME Workers \in Nat /\ Workers >= 1
ASSUME Jobs \in Nat /\ Jobs >= 1

\* claims is an append-only log of successful claim events: <<worker, job>>
\* pairs that the atomic CAS has ever accepted. It only grows; a job that
\* already appears (for any worker) can never be claimed again.
TypeOK ==
  claims \subseteq ((1..Workers) \times (1..Jobs))

Init ==
  claims = {}

\* Atomic compare-and-swap: succeeds only if no worker has claimed job j yet,
\* and in the same step records w as the (sole) successful claimant of j.
Claim(w, j) ==
  /\ ~ \E w2 \in 1..Workers : <<w2, j>> \in claims
  /\ claims' = claims \cup {<<w, j>>}

Done == \A j \in 1..Jobs : \E w \in 1..Workers : <<w, j>> \in claims

\* Allow intentional stuttering once every job has a claimant.
Terminating ==
  /\ Done
  /\ UNCHANGED claims

Next ==
  \/ \E w \in 1..Workers, j \in 1..Jobs : Claim(w, j)
  \/ Terminating

\* Weak fairness on the claim step: some worker's attempt on some still-
\* unclaimed job is not perpetually skipped, which is what makes the
\* liveness property (EventuallyAllJobsClaimed) checkable below.
Spec ==
  /\ Init
  /\ [][Next]_claims
  /\ WF_claims(\E w \in 1..Workers, j \in 1..Jobs : Claim(w, j))

\* --- Safety invariant (NFR1) ------------------------------------------
\* "At most one worker successfully claims a given job": for every job,
\* the set of workers whose claim was ever accepted for it has size <= 1.
\* Because claims is a log of every accepted CAS (not just current state),
\* this also rules out a job being claimed, "unclaimed", and claimed again
\* by someone else -- the log can only grow, so this is a true safety
\* property over the whole run, not just a snapshot.
AtMostOneClaimant ==
  \A j \in 1..Jobs : Cardinality({w \in 1..Workers : <<w, j>> \in claims}) <= 1

Inv == TypeOK /\ AtMostOneClaimant

\* Once the run is Done (every job has a claimant), each job must have
\* EXACTLY one claimant (not zero, not more than one) -- a stronger,
\* end-state sanity check that mutual exclusion actually resolved every
\* contested job rather than leaving it permanently unclaimed.
FinalOK ==
  Done => \A j \in 1..Jobs : Cardinality({w \in 1..Workers : <<w, j>> \in claims}) = 1

\* --- Liveness property ---------------------------------------------------
\* Progress / no-starvation: every job is eventually claimed by exactly one
\* worker. This is not itself required by NFR1 (NFR1 is a safety property),
\* but it confirms the model does not admit an infinite run where a job
\* stays perpetually unclaimed under fair scheduling of claim attempts.
EventuallyAllJobsClaimed == <>Done

====
