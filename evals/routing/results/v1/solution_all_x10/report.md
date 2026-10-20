# Routing eval report: 20261019T074728Z

- **Model:** anthropic/claude-haiku-5.5
- **Commit:** fb1c361 (dirty)
- **Sizes:** 25, 50, 100, 200, 400, 800, 1600
- **Cases:** 20
- **Fixtures:** evals/routing/fixtures
- **Total cost:** $1.4600
- **Started:** 2026-10-19T07:47:28+00:00  **Finished:** 2026-10-19T08:00:06+00:00

## Per size

| size | accuracy | correct | wrong_reuse | false_create | false_reuse | missed | error | extra | calls | mean prompt tok | mean cached tok | mean completion tok | mean reasoning tok | cost $ | mean latency s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 25 | 100% (210/210) | 210 | 0 | 0 | 0 | 0 | 0 | 0 | 364 | 19,594.0 | 17,470.3 | 324.3 | 97.5 | 0.2192 | 4.1 |
| 50 | 100% (210/210) | 210 | 0 | 0 | 0 | 0 | 0 | 0 | 361 | 19,568.7 | 17,525.1 | 324.0 | 97.5 | 0.2139 | 4.0 |
| 100 | 100% (210/210) | 210 | 0 | 0 | 0 | 0 | 0 | 0 | 354 | 19,393.1 | 17,464.7 | 333.7 | 103.2 | 0.2062 | 4.0 |
| 200 | 100% (210/210) | 210 | 0 | 0 | 0 | 0 | 0 | 0 | 362 | 19,415.6 | 17,483.9 | 320.8 | 95.8 | 0.2087 | 4.1 |
| 400 | 100% (209/210) | 209 | 0 | 0 | 0 | 1 | 0 | 0 | 366 | 19,386.2 | 17,555.1 | 323.8 | 98.3 | 0.2072 | 4.1 |
| 800 | 100% (210/210) | 210 | 0 | 0 | 0 | 0 | 0 | 0 | 357 | 19,292.3 | 17,478.8 | 335.4 | 104.6 | 0.2032 | 4.1 |
| 1600 | 100% (210/210) | 210 | 0 | 0 | 0 | 0 | 0 | 0 | 351 | 19,231.5 | 17,389.1 | 339.7 | 103.9 | 0.2015 | 4.2 |

Accuracy pools every repeat. Token columns are means per LLM call; latency is per case run.

## Agent search

| size | runs that searched | searches per run | gold in search results | creates without a search | rejected sends | search fallbacks |
|---|---|---|---|---|---|---|
| 25 | 80% | 0.810 | 100% | 0 | 2 | 0 |
| 50 | 79% | 0.810 | 100% | 1 | 0 | 0 |
| 100 | 76% | 0.770 | 100% | 1 | 0 | 0 |
| 200 | 80% | 0.800 | 100% | 0 | 0 | 0 |
| 400 | 79% | 0.810 | 100% | 0 | 1 | 0 |
| 800 | 77% | 0.780 | 100% | 1 | 1 | 0 |
| 1600 | 76% | 0.780 | 100% | 1 | 0 | 0 |

*Gold in search results*: of the existing-agent golds in runs where the query ranked agents (rosters above the search cutoff), how many the search returned. A false create with the gold returned is the IA's choice; without it, retrieval's.

## Before / after (baseline run `20261018T165232Z`)

| | 25 | 50 | 100 | 200 | 400 | 800 | 1600 |
|---|---|---|---|---|---|---|---|
| **accuracy** | 95% → **100%** | 98% → **100%** | 91% → **100%** | 89% → **100%** | 83% → **100%** | 86% → **100%** | 78% → **100%** |
| overload target (dormant, inference) | 98% → **100%** | 98% → **100%** | 93% → **100%** | 87% → **100%** | 77% → **100%** | 67% → **100%** | 62% → **100%** |
| dormant control (name match) | 100% → **100%** | 100% → **100%** | 100% → **100%** | 100% → **100%** | 92% → **100%** | 100% → **100%** | 88% → **100%** |
| easy recent | 97% → **100%** | 100% → **100%** | 100% → **100%** | 100% → **100%** | 98% → **100%** | 100% → **100%** | 98% → **100%** |
| policy-ambiguous | 60% → **100%** | 80% → **100%** | 30% → **100%** | 40% → **100%** | 40% → **100%** | 60% → **100%** | 60% → **100%** |
| multi-task | 100% → **100%** | 100% → **100%** | 100% → **100%** | 60% → **100%** | 50% → **90%** | 90% → **100%** | 20% → **100%** |

## Case groups (pass rate)

| group | 25 | 50 | 100 | 200 | 400 | 800 | 1600 |
|---|---|---|---|---|---|---|---|
| overload target (dormant, inference) | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| dormant control (name match) | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| easy recent | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| policy-ambiguous | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| multi-task | 100% | 100% | 100% | 100% | 90% | 100% | 100% |

## Case x size

| case | category | 25 | 50 | 100 | 200 | 400 | 800 | 1600 | pattern |
|---|---|---|---|---|---|---|---|---|---|
| c01_followup_named_counterpart | followup_counterpart_in_name | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c02_new_task_known_counterpart | new_task_known_counterpart | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c03_counterpart_not_in_owner_name | new_task_owner_name_unrelated | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c04_reply_to_email_found_by_unrelated_agent | reply_to_found_email | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c05_confirm_pending_draft | confirm_pending_draft | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c06_modify_existing_trigger | modify_reminder | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c07_revive_dormant_counterpart | dormant_counterpart_summary_only | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c08_same_first_name_other_person | same_first_name_other_person | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c09_new_counterpart_overlapping_name | new_counterpart_overlapping_name | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c10_parallel_known_and_new | parallel_known_and_new | 10/10 | 10/10 | 10/10 | 10/10 | 9/10 (missed×1) | 10/10 | 10/10 | pass at every size |
| c11_dormant_name_match_noor | dormant_name_match | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c12_dormant_inference_noor | dormant_inference | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c13_dormant_name_match_tidewater | dormant_name_match | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c14_dormant_inference_tidewater | dormant_inference | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c15_dormant_name_match_ironwood | dormant_name_match | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c16_dormant_inference_ironwood | dormant_inference | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c17_dormant_name_match_harold | dormant_name_match | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c18_dormant_inference_harold | dormant_inference | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c19_dormant_name_match_marcus | dormant_name_match | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |
| c20_dormant_inference_marcus | dormant_inference | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | pass at every size |

## Misses

### c10_parallel_known_and_new @ 400 #9: `missed`

- **Task:** ask Halcyon Chimney about a chimney sweep before mid-November
- **Gold:** `NEW`
- **Chosen:** (none)
- **All delegations:** `Email to Gabe Offsite Agenda`
- **Every task in this case:**
  - tell Gabe Theo will be ~20 min late to Wednesday's offsite kickoff: gold `Email to Gabe Offsite Agenda`, chosen `Email to Gabe Offsite Agenda` → `correct`
  - ask Halcyon Chimney about a chimney sweep before mid-November: gold `NEW`, chosen (none) → `missed`
- **Search** (search): `Email to Gabe Northfold offsite Cedar Hollow kickoff late`
- **Search** (search): `Halcyon Chimney sweep booking service@halcyonchimney.ca`
