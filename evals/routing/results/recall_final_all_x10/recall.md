# Agent search recall

- **Queries:** evals/routing/results/final_all_x10
- **Embeddings:** openai/text-embedding-3-small (512 dims)
- **Search returns:** top 10 (rosters of 10 or fewer return every agent)

## Recall@10 by scoring method

| method | 25 | 50 | 100 | 200 | 400 | 800 | 1600 | all |
|---|---|---|---|---|---|---|---|---|
| max (production) | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| max+bonus | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| top2 mean | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| soft max | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |

## Recall@K by scoring method (choosing K)

**max** (production)

| K | 25 | 50 | 100 | 200 | 400 | 800 | 1600 | all |
|---|---|---|---|---|---|---|---|---|
| 1 | 100% | 100% | 100% | 100% | 100% | 98% | 97% | 99% |
| 2 | 100% | 100% | 100% | 100% | 100% | 100% | 97% | 99% |
| 3 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 5 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 10 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 20 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |

**max+bonus**

| K | 25 | 50 | 100 | 200 | 400 | 800 | 1600 | all |
|---|---|---|---|---|---|---|---|---|
| 1 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 2 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 3 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 5 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 10 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 20 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |

**top2 mean**

| K | 25 | 50 | 100 | 200 | 400 | 800 | 1600 | all |
|---|---|---|---|---|---|---|---|---|
| 1 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 2 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 3 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 5 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 10 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 20 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |

**soft max**

| K | 25 | 50 | 100 | 200 | 400 | 800 | 1600 | all |
|---|---|---|---|---|---|---|---|---|
| 1 | 100% | 100% | 100% | 100% | 100% | 98% | 97% | 99% |
| 2 | 100% | 100% | 100% | 100% | 100% | 100% | 97% | 100% |
| 3 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 5 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 10 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 20 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |

## Worst gold rank per size (how deep search must go to find every gold)

| method | 25 | 50 | 100 | 200 | 400 | 800 | 1600 |
|---|---|---|---|---|---|---|---|
| max | 1 | 1 | 1 | 1 | 3 | 3 | 4 |
| max+bonus | 1 | 1 | 1 | 1 | 1 | 1 | 2 |
| top2 mean | 1 | 1 | 2 | 1 | 1 | 1 | 1 |
| soft max | 1 | 1 | 1 | 1 | 2 | 2 | 4 |

## Gold rank per case, production scoring (max)

| case | gold | 25 | 50 | 100 | 200 | 400 | 800 | 1600 |
|---|---|---|---|---|---|---|---|---|
| c01_followup_named_counterpart | Harrow Hill Venue Deposit | 1 (worst 1) | 1 | 1 | 1 (worst 1) | - | 1 | 1 (worst 1) |
| c02_new_task_known_counterpart | Priya Roadmap Sync | 1 | - | 1 (worst 1) | - | 1 (worst 1) | - | 1 |
| c03_counterpart_not_in_owner_name | Kitchen Reno Quote Follow-up | - | 1 | 1 (worst 1) | 1 | 1 (worst 1) | 1 (worst 1) | 1 |
| c04_reply_to_email_found_by_unrelated_agent | Inbox Catch-Up Scan | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c05_confirm_pending_draft | Copperleaf Renewal Thread | 1 (worst 1) | 1 | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 | 1 (worst 1) |
| c06_modify_existing_trigger | Sunday Week Ahead Brief | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 3) | 2 (worst 3) | 3 (worst 4) |
| c07_revive_dormant_counterpart | Mortgage Renewal Paperwork | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c08_same_first_name_other_person | Engagement Shoot Booking | 1 | 1 (worst 1) | - | 1 (worst 1) | - | - | 1 (worst 1) |
| c10_parallel_known_and_new | Email to Gabe Offsite Agenda | 1 (worst 1) | 1 | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c11_dormant_name_match_noor | Save the Date Printing | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c12_dormant_inference_noor | Save the Date Printing | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c13_dormant_name_match_tidewater | Dentist Cleaning Reschedule | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c14_dormant_inference_tidewater | Dentist Cleaning Reschedule | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c15_dormant_name_match_ironwood | Gym Membership Freeze | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c16_dormant_inference_ironwood | Gym Membership Freeze | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c17_dormant_name_match_harold | Neighbour Fence Repair | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c18_dormant_inference_harold | Neighbour Fence Repair | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c19_dormant_name_match_marcus | Fernway Designer Search | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c20_dormant_inference_marcus | Fernway Designer Search | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c21_dormant_paraphrase_wendell | Mortgage Renewal Paperwork | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c22_dormant_paraphrase_ironwood | Gym Membership Freeze | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c23_dormant_paraphrase_harold | Neighbour Fence Repair | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c24_dormant_paraphrase_tidewater | Dentist Cleaning Reschedule | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c28_dormant_typo_wendell | Mortgage Renewal Paperwork | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c29_dormant_typo_tidewater | Dentist Cleaning Reschedule | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c30_dormant_typo_ironwood | Gym Membership Freeze | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |
| c31_dormant_typo_harold | Neighbour Fence Repair | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) | 1 (worst 1) |

Bold: the gold fell outside the top 10 (for --from-run, the median rank across the IA's queries, and the worst).
