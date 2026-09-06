# DEV HTTPS delay: positive wildcard DNS caching — 2026-09-06

## Finding

Fresh normal-auth run J isolated an extra public HTTPS delay to a cached positive
wildcard parking answer. Concurrent probes used the same application hostname,
SNI and normal certificate verification. A probe pinned to the verified DEV
worker reached HTTPS 200 at 207.103 seconds after deployment start; ordinary DNS
reached HTTPS 200 at 298.092 seconds. The first-success samples differ by
90.989 seconds. This is a single paired experiment, not a general speed guarantee.

The ordinary-DNS probe continued connecting to Cloudflare addresses
`188.114.96.9` / `188.114.97.9` with curl TLS exit 35 after the worker-pinned
probe was serving verified HTTPS. It first succeeded when its resolved address
changed to `13.140.128.15`, approximately 300 seconds after its first lookup.
Together with the authoritative record configuration, this identifies positive
wildcard-answer caching as the extra routing delay. This is **not** an NXDOMAIN
or negative-caching finding, nor evidence that application initialization is fast.

## DNS configuration observed before the fix

Read-only authoritative configuration inspection found:

| Record | Existing configuration |
| --- | --- |
| `*.enclava.work` | CNAME to `pixie.porkbun.com`, proxied; automatic TTL, returned DNS TTL 300 seconds |
| `*.dev.enclava.work` | Absent |
| CAP-created exact app hostname | Direct, unproxied A record to `13.140.128.15`, TTL 300 seconds |

A lookup before CAP creates the exact app record can therefore obtain a valid
parking wildcard answer. Creating the exact record does not invalidate that
already cached positive answer. J's observed address switch near its lifetime
boundary explains why ordinary DNS lagged a verified connection to the correct
worker. The evidence does not locate every cache layer or attribute a particular
TLS error to the application itself.

## Paired experiment and sample bounds

The observer's first normal-DNS request began at **14:23:41.479062 UTC**.
Normal-auth deployment began at **14:23:42.827816 UTC**; these are different
origins. The last column below uses deployment start. Times are completed probe
samples, not exact server-side transitions; each request also has a start time.

| Observation | Completed sample, UTC | Since deployment start |
| --- | --- | ---: |
| Last pinned TLS-failure sample before verified HTTP | 14:26:26.515235 | 163.687 s |
| First pinned verified TLS / HTTP 404 | 14:26:28.581480 | 165.754 s |
| Last pinned HTTP 404 before 200 | 14:27:07.863304 | 205.035 s |
| First pinned verified HTTPS 200 | 14:27:09.931126 | 207.103 s |
| Last ordinary-DNS Cloudflare / TLS exit 35 | 14:28:38.750167 | 295.922 s |
| First ordinary-DNS worker / verified HTTPS 200 | 14:28:40.919954 | 298.092 s |

The successful pinned request ran from 14:27:09.863750 to 14:27:09.931126;
its previous 404 request ran from 14:27:07.797318 to 14:27:07.863304.
The ordinary-DNS successful request ran from 14:28:40.783193 to
14:28:40.919954; its preceding failure ran from 14:28:38.715831 to
14:28:38.750167. These brackets constrain observation precision; do not report
the sample spacing as an exact service transition or TTL expiry instant.

The first normal-DNS success completed **299.440892 seconds after the observer's
first lookup began**, versus 298.092138 seconds after deployment began.
Before application success, pinned verified TLS already returned HTTP 404;
DNS is therefore not the only startup stage. Application readiness and the
remaining init/managed-delivery bottlenecks still require separate measurement.

Strict SSH host-key verification after initial TOFU passed. The deployment
observer finished with exit code zero at 14:28:42.036086 UTC. Normal destroy
exited zero. At 14:30 UTC, the exact disposable namespace, PVs
`7f9e2c96-421c-4a91-96bf-f8bb6342124e` and
`cd5542ad-6cfd-4443-bced-70d8d7b5a891`, and their matching Longhorn volumes
were verified absent.

## Measurement safety

The DEV-only paired observer was reviewed using actual Pi CLI with GLM-5.3;
its local self-test passed. It runs two concurrent probes: ordinary DNS and
`--resolve` to the independently verified worker address. Both keep the original
hostname, SNI and certificate checks. There is no insecure TLS mode, redirect
following, authentication, custom header, response-body publication or customer
log collection.

The command uses absolute `/usr/bin/curl`, `-q` and `--noproxy '*'`; its subprocess
environment contains only fixed PATH and locale. It cannot inherit curl config,
proxy settings, TLS key logging or CA trust overrides. Each curl request has a
two-second limit, with a five-second subprocess limit and a bounded overall
observer window. Output is restricted to timestamps, fixed mode, validated
status/IP fields and finite nonnegative timing metadata. Raw stderr and response
bodies are not published. No private evidence files, credentials or keys are
included in this report. Preprod was not accessed or changed.

## Mitigation and outstanding validation

An infrastructure PR is being prepared to manage a DEV-specific wildcard DNS
record pointing directly at the verified DEV worker, with narrowly scoped DNS
record ownership. It has **not** been applied at this checkpoint. Keep CAP's
exact app records and certificate verification intact; do not alter the global
parking wildcard or preprod as a shortcut.

After reviewed application, allow old positive answers to expire and run a fresh
normal-auth K experiment with concurrent ordinary-DNS and pinned probes. Compare
actual HTTPS usability, not just pod readiness or CLI completion, then verify
SSH, normal deletion, exact disposable storage removal and the preserved canary.
Run K has **not** been performed. No post-fix improvement is claimed yet.
