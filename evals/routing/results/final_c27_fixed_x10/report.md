# Routing eval report: 20261019T100723Z

- **Model:** anthropic/claude-haiku-5.5
- **Commit:** 5a72891 (dirty)
- **Sizes:** 25, 50, 100, 200, 400, 800, 1600
- **Cases:** 1
- **Fixtures:** evals/routing/fixtures
- **Total cost:** $0.1073
- **Started:** 2026-10-19T10:07:23+00:00  **Finished:** 2026-10-19T10:09:41+00:00

## Per size

| size | accuracy | correct | wrong_reuse | false_create | false_reuse | missed | error | extra | calls | mean prompt tok | mean cached tok | mean completion tok | mean reasoning tok | cost $ | mean latency s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 25 | 100% (10/10) | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 21 | 19,949.9 | 17,678.1 | 523.3 | 163.3 | 0.0152 | 7.1 |
| 50 | 100% (10/10) | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 22 | 20,028.3 | 17,864.8 | 450.0 | 123.3 | 0.0148 | 6.4 |
| 100 | 100% (10/10) | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 21 | 20,011.7 | 17,681.6 | 513.0 | 156.7 | 0.0152 | 7.1 |
| 200 | 100% (10/10) | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 21 | 20,005.4 | 17,678.3 | 500 | 144.8 | 0.0151 | 6.5 |
| 400 | 100% (10/10) | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 21 | 19903 | 17,669.9 | 510.0 | 149.8 | 0.0149 | 6.9 |
| 800 | 100% (10/10) | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 26 | 20,438.7 | 18,563.7 | 459.5 | 132.8 | 0.0169 | 7.6 |
| 1600 | 100% (10/10) | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 22 | 19,842.7 | 17,831.3 | 521.2 | 174.2 | 0.0152 | 7.3 |

Accuracy pools every repeat. Token columns are means per LLM call; latency is per case run.

## Agent search

| size | runs that searched | searches per run | gold in search results | creates without a search | rejected sends | search fallbacks |
|---|---|---|---|---|---|---|
| 25 | 100% | 1.0 | - | 0 | 0 | 0 |
| 50 | 100% | 1.0 | - | 0 | 0 | 0 |
| 100 | 100% | 1.0 | - | 0 | 0 | 0 |
| 200 | 100% | 1.0 | - | 0 | 0 | 0 |
| 400 | 100% | 1.0 | - | 0 | 0 | 0 |
| 800 | 100% | 1.0 | - | 0 | 1 | 0 |
| 1600 | 100% | 1.0 | - | 0 | 0 | 0 |

*Gold in search results*: of the existing-agent golds in runs where the query ranked agents (rosters above the search cutoff), how many the search returned. A false create with the gold returned is the IA's choice; without it, retrieval's.

## Before / after (baseline run `20261018T165232Z`)

| | 25 | 50 | 100 | 200 | 400 | 800 | 1600 |
|---|---|---|---|---|---|---|---|
| **accuracy** | 95% → **100%** | 98% → **100%** | 91% → **100%** | 89% → **100%** | 83% → **100%** | 86% → **100%** | 78% → **100%** |
| overload target (dormant, inference) | 98% → **-** | 98% → **-** | 93% → **-** | 87% → **-** | 77% → **-** | 67% → **-** | 62% → **-** |
| dormant control (name match) | 100% → **-** | 100% → **-** | 100% → **-** | 100% → **-** | 92% → **-** | 100% → **-** | 88% → **-** |
| easy recent | 97% → **-** | 100% → **-** | 100% → **-** | 100% → **-** | 98% → **-** | 100% → **-** | 98% → **-** |
| policy-ambiguous | 60% → **-** | 80% → **-** | 30% → **-** | 40% → **-** | 40% → **-** | 60% → **-** | 60% → **-** |
| multi-task | 100% → **-** | 100% → **-** | 100% → **-** | 60% → **-** | 50% → **-** | 90% → **-** | 20% → **-** |
| stress: paraphrase (dormant, no name) | - → **-** | - → **-** | - → **-** | - → **-** | - → **-** | - → **-** | - → **-** |
| stress: new counterpart, familiar topic | - → **100%** | - → **100%** | - → **100%** | - → **100%** | - → **100%** | - → **100%** | - → **100%** |
| stress: typo (dormant name) | - → **-** | - → **-** | - → **-** | - → **-** | - → **-** | - → **-** | - → **-** |

## Case groups (pass rate)

| group | 25 | 50 | 100 | 200 | 400 | 800 | 1600 |
|---|---|---|---|---|---|---|---|
| overload target (dormant, inference) | - | - | - | - | - | - | - |
| dormant control (name match) | - | - | - | - | - | - | - |
| easy recent | - | - | - | - | - | - | - |
| policy-ambiguous | - | - | - | - | - | - | - |
| multi-task | - | - | - | - | - | - | - |
| stress: paraphrase (dormant, no name) | - | - | - | - | - | - | - |
| stress: new counterpart, familiar topic | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| stress: typo (dormant name) | - | - | - | - | - | - | - |

## Case x size

| case | category | 25 | 50 | 100 | 200 | 400 | 800 | 1600 | pattern |
|---|---|---|---|---|---|---|---|---|---|
| c27_new_familiar_topic_restaurant | new_counterpart_familiar_topic | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |

## Misses

None.
