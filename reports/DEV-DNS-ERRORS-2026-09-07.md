# DEV DNS error attribution — 2026-09-07

## Scope and hypothesis

Follow-up to [the previous broker measurements](DEV-BROKER-DNS-2026-09-06.md).
DEV only; never access or change PREPROD. Preserve the original canary UID
`90f0d6c1-fab7-44ef-9cec-942ea1058efd`, confidential workload boundaries,
exact TXT matching and ACME validation.

Q took199.814s through normal-auth CLI. Its system lookups failed in31/18/37ms,
each followed by a2s external timeout and5s propagation sleep; system lookup4
succeeded in121ms. DNS visibility21.217s, broker total25.910s. Those timings
do not prove whether the initial errors were negative DNS answers or transport
failures. No end-to-end DNS speedup was established.

Pinned Hickory represents NXDOMAIN/NODATA as typed errors, currently handled
like transport failures. Diagnostic-only changes will classify those errors
before stringification; lookup results/order, fallback, retry budgets and
certificate validation remain unchanged.

## Diagnostic contract

Optional `error_category` on existing `workload_tls_timing` records, only for
`dns_system_lookup` / `dns_external_lookup` with outcome `error`:

- `nxdomain`: typed NoRecordsFound with NXDomain response.
- `nodata`: typed NoRecordsFound with NoError response.
- `timeout`: native timeout, timed-out I/O, or configured outer lookup timeout.
- `transport`: other I/O failure or no connections.
- `other`: all remaining errors, including other DNS response codes.

No names, TXT answers, raw error text, evidence or inherited span fields.
Existing target opt-in, process-local sequence and non-additive timing semantics
remain. Missing category stays valid for historical records. The collector
rejects unknown, malformed, empty, duplicated or wrong-context categories.

## Verification plan

1. Typed-error, cancellation, redaction and collector tests; exact-head PR review
   and CI before merge. Use actual Devin SWE-1.7 and Pi GLM-5.3 for bounded review;
   a denied or timed-out invocation is not review approval.
2. Signed main release, DEV-only digest/immutable-Job promotion, runtime imageID,
   migration/readiness and original-canary checks.
3. Fresh normal-auth deployment S with unchanged CLI binary; stream only platform
   timing logs through the strict collector, collect metadata and verified HTTPS.
4. Verify actual SSH before normal destruction, then exact namespace/PV/Longhorn
   absence and original-canary preservation.
5. Decide on behavior changes only from observed categories. Negative answers
   must never count as TXT propagation success; transport fallback and mandatory
   ACME validation cannot be bypassed. Resolver caching tradeoffs remain relevant.

## Source verification

[CAP #105](https://github.com/enclava-labs/cap/pull/105), head `8122700`, adds
typed classification beside unchanged error messages and optional fixed-label
timing emission. All454 API tests passed on a fresh isolated local database
(414 library,10 main,2 contract,28 integration); all-target API clippy and
formatting passed. Negative answers still trigger fallback in both resolver
orders. Configured timeout/cancellation behavior is unchanged. Actual Devin
SWE-1.7 review completed; exact-head automated review found no issues.

[PaaS #95](https://github.com/enclava-labs/enclava-paas/pull/95), head `f41244c`,
updates only the collector and its docs. Filter/analyzer self-tests and bounded
process-level malformed-input tests passed. Local Devin review found no defect
in the first diff, but root and both PR reviewers identified quoted categories
with trailing bytes being accepted as a valid prefix. The final commit scans
the complete whitespace-delimited token and adds a regression. Both comments
were answered; Devin marked the finding resolved. No raw data is exported.

Actual Pi GLM-5.3 attempts produced no review result within bounded waiting and
were stopped/timed out. They are not counted as approval. Exact-head CI passed:
CAP workspace `34083407420` and image `34083407416`, PaaS `34083471142`.
All reviews/inline/issue comments were reread before separate exact-head merge
calls. CAP merged as `adc672408791376487c26a358916dac92c830e3d`, PaaS as
`8c90947125c2a37db937c2f6472966401c1fb230`.

Signed API release dispatch `34083992338`, tag
`manual-20260907-dev-dns-error-timing`, targets that exact CAP main source.
The release completed successfully. Downloaded API digest
`sha256:c94150ab99731ed160a46ab7543976608dc914c077cb8dac3033ce6e069dce3c`
and migration46 passed the official image-reference verifier. Exact
main-workflow keyless signature verification passed; optional annotations are
empty, so source/profile binding uses the successful dispatch record/artifact.

[Ops #156](https://github.com/enclava-labs/enclava-ops-manifests/pull/156),
head `f734916`, changes only DEV API/Job references, immutable Job name and
README. Server dry-run, environment contracts, complete DEV render and
contained authority/mTLS regressions passed. All runtime settings, checksums,
tenant/PaaS/appraiser pins and DNS policies/configuration remain unchanged.
Exact-head automated review found no issues. CI `34085256438` passed; all
comments were read before exact-head merge as `8ec57d2`. Flux applied without
manual reconciliation. API pod `cap-api-99458b658-lp82z`, UID
`dcb5efbc-554e-4619-89a4-065a77a3d7a4`, is Ready with zero restarts on the exact
digest. Migration Job succeeded on the same image. PaaS readiness reports ten
checks; original canary UID/four ready containers/zero restarts are unchanged.
S started through normal authentication at05:06:52 UTC with the unchanged CLI
SHA256 `73bee0f1a3d9bf671b25c7a147393b1c3760f8610af143fe45bb264f5b4e7d7a`.
Live timing and functional results are recorded below.

## Read-only resolver topology check

DEV live CoreDNS and its checked-in `clusters/enclava-work/coredns.yaml` both
use `cache 30`, forwarding through node DNS endpoints on port1053. Those
endpoints also use `cache 30`, matching `node-dns-upstream.yaml`. No DNS config
was changed. [CoreDNS cache documentation](https://coredns.io/plugins/cache/)
defines this as a TTL cap, not a mandatory delay; denial responses can be cached.
The two caps must not be added into a claimed60s delay. Actual negative answers,
cache residence and upstream publication timing remain unproven for Q.

## Offline bootstrap comparison while the release builds

P/R/Q sanitized metadata consistently brackets46/46/47s from scheduling to
sandbox-ready, then23/24/23s until `enclava-init` starts. Volume attach events
occur at scheduling+10s, last mount events at+14–15s, first Pulled event at+26s.
The remaining gap is not yet attributable to VM boot versus image/container
preparation: these events omit component association and operation start times.
CLI bootstrap retry sleeps overlap infrastructure startup, so they are not
additive delay or evidence that deleting sleeps saves a minute.

DEV kubelet exposes numeric cumulative duration/count metrics for
`run_podsandbox`, `pull_image`, `create_container`, and `start_container`.
Only those fixed labels and numeric values were projected from the metadata
endpoint; no raw stream was retained. Before/after snapshots around S can
provide aggregate operation duration deltas. They are node-wide, not per-pod;
concurrent operations, failed attempts and counter resets must be considered.

## S: negative-answer fallback confirmed live

Normal-auth CLI completed in **172.541s**, with API running and verified HTTPS
observed by **179.007s**. Bootstrap89.078s, ownership0.928s, managed wait55.677s.
First real SSH passed using normal TOFU and the existing user key; a second
connection passed with strict saved-host-key verification. Neither command
required a policy or confidentiality bypass. TOFU is not attestation-bound
host-key verification.

Exactly one broker request (API pod `cap-api-99458b658-lp82z`, sequence1):

| Nested phase | Duration / result |
| --- | --- |
| System lookup1 | 70ms, **nxdomain** |
| External fallback1 | 2.001s, **timeout** |
| System lookup2 | 35ms, **nxdomain** |
| External fallback2 | 2.001s, **timeout** |
| System lookup3 | 65ms, success |
| DNS visibility, including retries | **14.175s**, success |
| Broker total | **18.534s**, success |

This directly establishes that negative system-DNS answers trigger fallback
to an external resolver that times out in DEV. Roughly4s went into those two
fallbacks and10s into existing propagation sleeps; neither is added again to
the enclosing totals. It does **not** identify the cache layer or prove when
the authoritative TXT became available. Q's older error-only events cannot
retroactively be relabeled as proven NXDOMAIN.

S was27.274s faster than Q overall, but this release changes diagnostics only:
no causal speedup is claimed. Ownership alone changed18.423→0.928s and DNS
visibility21.217→14.175s. Managed worker window50.490s included eight423 write
responses and twoKDS429s; those remain separate observations.

### Next mitigation decision

The smallest source candidate is to distinguish valid negative TXT answers
from resolver transport failure in the shared TXT adapter: only typed
NoRecordsFound with NXDomain/NoError could become an empty answer, retaining
exact-token checking and propagation retry while preserving fallback for
timeouts, I/O, SERVFAIL, REFUSED and unknown errors. This is **not implemented**
in the diagnostic PR: an alternate reachable resolver can sometimes escape a
stale negative cache, so both resolver orders and a real before/after DEV test
are required before claiming an improvement. Do not globally disable caches,
widen DNS egress or equate an empty answer with successful ACME validation.

### Kubelet counter experiment and limits

Snapshots at05:06:33 and05:11:38 UTC projected only four fixed operation names
and numeric counters; no raw metric stream was retained. Counters did not reset.
The window covers four sandbox operations totaling12.199s, eleven container
creates totaling0.593s, eleven container starts totaling40.650s, and two image
pulls totaling0.878s. These are node-wide totals, **not S-specific timings**;
the four sandbox operations prevent attributing12.199s to S alone. Do not add
potentially overlapping operation totals to application wall-clock time.

S metadata has one pod UID and zero container restarts. Creation→scheduled was
10s (a FailedScheduling event preceded success), scheduled→sandbox-ready46s,
sandbox-ready→main containers12s, main→enclava-init11s, init→Ready54s. No
sandbox failure/change event appeared, but absence of events does not exclude
unreported attempts. Tools started one second before the sandbox-ready condition
timestamp, underscoring that conditions are approximate lifecycle observations.
The repeatable46–47s interval still needs per-operation attribution.

### Cleanup

Only after both SSH checks passed, normal destruction exited zero. At05:14:05
UTC authenticated lookup returned404; the exact namespace, PVs
`pvc-3644389e-4137-4ef4-aab6-5d510c270065` and
`pvc-8989a307-a033-492c-bdb1-284f037b7086`, and matching Longhorn volumes were
absent. Exact metadata/DB observers stopped; paired HTTPS observer completed.
The original canary retained its UID, four ready containers and zero restarts.
PREPROD was not accessed or changed. No deployment speed or full production
ceremony completion is claimed from this diagnostic release.
