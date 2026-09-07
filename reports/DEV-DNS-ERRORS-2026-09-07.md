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
were stopped/timed out. They are not counted as approval. Exact-head CI and
live DEV results remain pending.
