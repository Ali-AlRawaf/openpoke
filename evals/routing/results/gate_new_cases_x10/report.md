# Routing eval report: 20261019T085049Z

- **Model:** anthropic/claude-haiku-5.5
- **Commit:** fb1c361 (dirty)
- **Sizes:** 25, 50, 100, 200, 400, 800, 1600
- **Cases:** 2
- **Fixtures:** evals/routing/fixtures
- **Total cost:** $0.2231
- **Started:** 2026-10-19T08:50:49+00:00  **Finished:** 2026-10-19T08:53:32+00:00

## Per size

| size | accuracy | correct | wrong_reuse | false_create | false_reuse | missed | error | extra | calls | mean prompt tok | mean cached tok | mean completion tok | mean reasoning tok | cost $ | mean latency s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 25 | 100% (30/30) | 30 | 0 | 0 | 0 | 0 | 0 | 0 | 42 | 20,749.6 | 17,558.3 | 467.2 | 112.8 | 0.0339 | 6.0 |
| 50 | 100% (30/30) | 30 | 0 | 0 | 0 | 0 | 0 | 0 | 48 | 21,145.6 | 18,659.5 | 418.0 | 95.8 | 0.0339 | 6.1 |
| 100 | 100% (30/30) | 30 | 0 | 0 | 0 | 0 | 0 | 0 | 42 | 20,617.4 | 17,849.5 | 458.1 | 105.8 | 0.0316 | 5.8 |
| 200 | 100% (30/30) | 30 | 0 | 0 | 0 | 0 | 0 | 0 | 42 | 20,406.4 | 17,840.8 | 466.5 | 111.9 | 0.0308 | 6.0 |
| 400 | 100% (30/30) | 30 | 0 | 0 | 0 | 0 | 0 | 0 | 44 | 20,691.9 | 18,200.2 | 451.0 | 99.6 | 0.0316 | 6.1 |
| 800 | 100% (30/30) | 30 | 0 | 0 | 0 | 0 | 0 | 0 | 44 | 20,718.1 | 18,098.8 | 451.0 | 100.3 | 0.0323 | 6.1 |
| 1600 | 100% (30/30) | 30 | 0 | 0 | 0 | 0 | 0 | 0 | 43 | 19,967.6 | 17,833.8 | 457.7 | 104.4 | 0.0290 | 5.9 |

Accuracy pools every repeat. Token columns are means per LLM call; latency is per case run.

## Agent search

| size | runs that searched | searches per run | gold in search results | creates without a search | creates blocked by the search gate | rejected sends | search fallbacks |
|---|---|---|---|---|---|---|---|
| 25 | 100% | 1.2 | 100% | 0 | 0 | 0 | 0 |
| 50 | 100% | 1.2 | 100% | 0 | 0 | 1 | 0 |
| 100 | 100% | 1.3 | 100% | 0 | 0 | 0 | 0 |
| 200 | 100% | 1.2 | 100% | 0 | 0 | 0 | 0 |
| 400 | 100% | 1.3 | 100% | 0 | 0 | 0 | 0 |
| 800 | 100% | 1.4 | 100% | 0 | 0 | 0 | 0 |
| 1600 | 100% | 1.1 | 100% | 0 | 0 | 1 | 0 |

*Gold in search results*: of the existing-agent golds in runs where the query ranked agents (rosters above the search cutoff), how many the search returned. A false create with the gold returned is the IA's choice; without it, retrieval's.

## Before / after (baseline run `20261018T165232Z`)

| | 25 | 50 | 100 | 200 | 400 | 800 | 1600 |
|---|---|---|---|---|---|---|---|
| **accuracy** | 95% → **100%** | 98% → **100%** | 91% → **100%** | 89% → **100%** | 83% → **100%** | 86% → **100%** | 78% → **100%** |
| overload target (dormant, inference) | 98% → **-** | 98% → **-** | 93% → **-** | 87% → **-** | 77% → **-** | 67% → **-** | 62% → **-** |
| dormant control (name match) | 100% → **-** | 100% → **-** | 100% → **-** | 100% → **-** | 92% → **-** | 100% → **-** | 88% → **-** |
| easy recent | 97% → **100%** | 100% → **100%** | 100% → **100%** | 100% → **100%** | 98% → **100%** | 100% → **100%** | 98% → **100%** |
| policy-ambiguous | 60% → **-** | 80% → **-** | 30% → **-** | 40% → **-** | 40% → **-** | 60% → **-** | 60% → **-** |
| multi-task | 100% → **100%** | 100% → **100%** | 100% → **100%** | 60% → **100%** | 50% → **100%** | 90% → **100%** | 20% → **100%** |

## Case groups (pass rate)

| group | 25 | 50 | 100 | 200 | 400 | 800 | 1600 |
|---|---|---|---|---|---|---|---|
| overload target (dormant, inference) | - | - | - | - | - | - | - |
| dormant control (name match) | - | - | - | - | - | - | - |
| easy recent | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| policy-ambiguous | - | - | - | - | - | - | - |
| multi-task | 100% | 100% | 100% | 100% | 100% | 100% | 100% |

## Case x size

| case | category | 25 | 50 | 100 | 200 | 400 | 800 | 1600 | pattern |
|---|---|---|---|---|---|---|---|---|---|
| c09_new_counterpart_overlapping_name | new_counterpart_overlapping_name | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c10_parallel_known_and_new | parallel_known_and_new | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |

## Misses

None.
