# Routing eval report: 20261019T071940Z

- **Model:** anthropic/claude-haiku-5.5
- **Commit:** fb1c361 (dirty)
- **Sizes:** 25
- **Cases:** 20
- **Fixtures:** evals/routing/fixtures
- **Total cost:** $0.0658
- **Started:** 2026-10-19T07:19:40+00:00  **Finished:** 2026-10-19T07:20:17+00:00

## Per size

| size | accuracy | correct | wrong_reuse | false_create | false_reuse | missed | error | extra | calls | mean prompt tok | mean cached tok | mean completion tok | mean reasoning tok | cost $ | mean latency s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 25 | 100% (63/63) | 63 | 0 | 0 | 0 | 0 | 0 | 0 | 107 | 19,488.4 | 17,268.8 | 329.4 | 99.9 | 0.0658 | 4.2 |

Accuracy pools every repeat. Token columns are means per LLM call; latency is per case run.

## Agent search

| size | runs that searched | searches per run | gold in search results | creates without a search | rejected sends | search fallbacks |
|---|---|---|---|---|---|---|
| 25 | 78% | 0.780 | 100% | 0 | 0 | 0 |

*Gold in search results*: of the existing-agent golds in runs where the query ranked agents (rosters above the search cutoff), how many the search returned. A false create with the gold returned is the IA's choice; without it, retrieval's.

## Before / after (baseline run `20261018T165232Z`)

| | 25 |
|---|---|
| **accuracy** | 95% → **100%** |
| overload target (dormant, inference) | 98% → **100%** |
| dormant control (name match) | 100% → **100%** |
| easy recent | 97% → **100%** |
| policy-ambiguous | 60% → **100%** |
| multi-task | 100% → **100%** |

## Case groups (pass rate)

| group | 25 |
|---|---|
| overload target (dormant, inference) | 100% |
| dormant control (name match) | 100% |
| easy recent | 100% |
| policy-ambiguous | 100% |
| multi-task | 100% |

## Case x size

| case | category | 25 | pattern |
|---|---|---|---|
| c01_followup_named_counterpart | followup_counterpart_in_name | 3/3 | pass at every size |
| c02_new_task_known_counterpart | new_task_known_counterpart | 3/3 | pass at every size |
| c03_counterpart_not_in_owner_name | new_task_owner_name_unrelated | 3/3 | pass at every size |
| c04_reply_to_email_found_by_unrelated_agent | reply_to_found_email | 3/3 | pass at every size |
| c05_confirm_pending_draft | confirm_pending_draft | 3/3 | pass at every size |
| c06_modify_existing_trigger | modify_reminder | 3/3 | pass at every size |
| c07_revive_dormant_counterpart | dormant_counterpart_summary_only | 3/3 | pass at every size |
| c08_same_first_name_other_person | same_first_name_other_person | 3/3 | pass at every size |
| c09_new_counterpart_overlapping_name | new_counterpart_overlapping_name | 3/3 | pass at every size |
| c10_parallel_known_and_new | parallel_known_and_new | 3/3 | pass at every size |
| c11_dormant_name_match_noor | dormant_name_match | 3/3 | pass at every size |
| c12_dormant_inference_noor | dormant_inference | 3/3 | pass at every size |
| c13_dormant_name_match_tidewater | dormant_name_match | 3/3 | pass at every size |
| c14_dormant_inference_tidewater | dormant_inference | 3/3 | pass at every size |
| c15_dormant_name_match_ironwood | dormant_name_match | 3/3 | pass at every size |
| c16_dormant_inference_ironwood | dormant_inference | 3/3 | pass at every size |
| c17_dormant_name_match_harold | dormant_name_match | 3/3 | pass at every size |
| c18_dormant_inference_harold | dormant_inference | 3/3 | pass at every size |
| c19_dormant_name_match_marcus | dormant_name_match | 3/3 | pass at every size |
| c20_dormant_inference_marcus | dormant_inference | 3/3 | pass at every size |

## Misses

None.
