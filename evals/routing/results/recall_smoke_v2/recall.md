# Agent search recall

Queries: evals/routing/results/smoke_v2. Embeddings: openai/text-embedding-3-small. Production search returns the top 10. 235 query x task rankings.

## Gold recall@K

| K | 25 | 400 | 1600 | all |
|---:|---:|---:|---:|---:|
| 1 | 100% | 98% | 94% | 97% |
| 3 | 100% | 100% | 100% | 100% |
| 5 | 100% | 100% | 100% | 100% |
| 10 (production) | 100% | 100% | 100% | 100% |
| 20 | 100% | 100% | 100% | 100% |

Worst gold rank: 25: 1, 400: 2, 1600: 2.

## By case

Each cell: the gold's median rank (worst in brackets when the queries disagree), then how many of the task's traps present at that size reached the top 10 for at least one query. **Bold**: the gold missed the top 10. -: no ranked search for that case at that size (the IA sent to a known agent directly, or the decision crashed).

| Case | Gold | 25 | 400 | 1600 |
|---|---|---|---|---|
| c01_followup_named_counterpart | Harrow Hill Venue Deposit | 1 · no traps | - | - |
| c02_new_task_known_counterpart | Priya Roadmap Sync | - | 1 · traps 3/6 | - |
| c03_counterpart_not_in_owner_name | Kitchen Reno Quote Follow-up | 1 · no traps | - | - |
| c04_reply_to_email_found_by_unrelated_agent | Inbox Catch-Up Scan | 1 · no traps | 1 · traps 2/5 | 2 · traps 2/6 |
| c05_confirm_pending_draft | Copperleaf Renewal Thread | - | 1 · traps 3/4 | - |
| c06_modify_existing_trigger | Sunday Week Ahead Brief | 1 · no traps | 1 (2) · traps 4/4 | 2 · traps 2/4 |
| c07_revive_dormant_counterpart | Mortgage Renewal Paperwork | 1 · no traps | 1 · traps 2/4 | 1 · traps 2/6 |
| c08_same_first_name_other_person | Engagement Shoot Booking | - | - | 1 · traps 5/6 |
| c09_new_counterpart_overlapping_name | NEW | traps 2/2 | traps 3/4 | traps 2/4 |
| c10_parallel_known_and_new | Email to Gabe Offsite Agenda | 1 · no traps | 1 · traps 4/4 | 1 · traps 1/4 |
| c10_parallel_known_and_new | NEW | no traps | traps 2/2 | traps 1/3 |
| c11_dormant_name_match_noor | Save the Date Printing | 1 · no traps | 1 · traps 3/3 | 1 · traps 3/4 |
| c12_dormant_inference_noor | Save the Date Printing | 1 · no traps | 1 · traps 3/3 | 1 · traps 4/4 |
| c13_dormant_name_match_tidewater | Dentist Cleaning Reschedule | 1 · no traps | 1 · traps 3/4 | 1 · traps 1/4 |
| c14_dormant_inference_tidewater | Dentist Cleaning Reschedule | 1 · no traps | 1 · traps 3/4 | 1 · traps 2/4 |
| c15_dormant_name_match_ironwood | Gym Membership Freeze | 1 · no traps | 1 · traps 2/3 | 1 · traps 2/4 |
| c16_dormant_inference_ironwood | Gym Membership Freeze | 1 · no traps | 1 · traps 2/3 | 1 · traps 2/4 |
| c17_dormant_name_match_harold | Neighbour Fence Repair | 1 · no traps | 1 · traps 3/3 | 1 · traps 3/5 |
| c18_dormant_inference_harold | Neighbour Fence Repair | 1 · no traps | 1 · traps 3/3 | 1 · traps 4/5 |
| c19_dormant_name_match_marcus | Fernway Designer Search | 1 · no traps | 1 · traps 2/4 | 1 · traps 2/4 |
| c20_dormant_inference_marcus | Fernway Designer Search | 1 · no traps | 1 · traps 3/4 | 1 · traps 3/4 |
| c21_dormant_paraphrase_wendell | Mortgage Renewal Paperwork | 1 · no traps | 1 · traps 1/4 | 1 · traps 3/6 |
| c22_dormant_paraphrase_ironwood | Gym Membership Freeze | 1 · no traps | 1 · traps 2/3 | 1 · traps 2/4 |
| c23_dormant_paraphrase_harold | Neighbour Fence Repair | 1 · no traps | 1 · traps 3/3 | 1 · traps 3/5 |
| c24_dormant_paraphrase_tidewater | Dentist Cleaning Reschedule | 1 · no traps | 1 · traps 3/4 | 1 · traps 1/4 |
| c25_new_familiar_topic_dentist | NEW | traps 1/1 | traps 4/4 | traps 4/4 |
| c26_new_familiar_topic_mechanic | NEW | traps 1/1 | traps 3/4 | traps 3/4 |
| c27_new_familiar_topic_restaurant | NEW | traps 1/1 | traps 1/1 | traps 1/2 |
| c28_dormant_typo_wendell | Mortgage Renewal Paperwork | 1 · no traps | 1 · traps 1/4 | 1 · traps 1/6 |
| c29_dormant_typo_tidewater | Dentist Cleaning Reschedule | 1 · no traps | 1 · traps 3/4 | 1 · traps 1/4 |
| c30_dormant_typo_ironwood | Gym Membership Freeze | 1 · no traps | 1 · traps 2/3 | 1 · traps 1/4 |
| c31_dormant_typo_harold | Neighbour Fence Repair | 1 · no traps | 1 · traps 3/3 | 1 · traps 3/5 |
