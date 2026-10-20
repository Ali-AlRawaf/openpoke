# Agent search recall

- **Queries:** case messages
- **Embeddings:** openai/text-embedding-3-small (512 dims)
- **Search returns:** top 10 (rosters of 10 or fewer return every agent)

## Recall@10 by scoring method

| method | 25 | 50 | 100 | 200 | 400 | 800 | 1600 | all |
|---|---|---|---|---|---|---|---|---|
| max (production) | 96% | 96% | 96% | 96% | 93% | 89% | 85% | 93% |
| max+bonus | 96% | 96% | 96% | 96% | 93% | 93% | 89% | 94% |
| top2 mean | 96% | 96% | 96% | 96% | 96% | 93% | 93% | 95% |
| soft max | 96% | 96% | 96% | 93% | 93% | 93% | 89% | 94% |

## Recall@K by scoring method (choosing K)

**max** (production)

| K | 25 | 50 | 100 | 200 | 400 | 800 | 1600 | all |
|---|---|---|---|---|---|---|---|---|
| 1 | 81% | 81% | 81% | 81% | 74% | 67% | 52% | 74% |
| 2 | 96% | 93% | 85% | 81% | 81% | 74% | 63% | 82% |
| 3 | 96% | 96% | 89% | 89% | 85% | 78% | 70% | 86% |
| 5 | 96% | 96% | 96% | 89% | 85% | 81% | 78% | 89% |
| 10 | 96% | 96% | 96% | 96% | 93% | 89% | 85% | 93% |
| 20 | 96% | 96% | 96% | 96% | 96% | 93% | 89% | 95% |

**max+bonus**

| K | 25 | 50 | 100 | 200 | 400 | 800 | 1600 | all |
|---|---|---|---|---|---|---|---|---|
| 1 | 89% | 89% | 89% | 85% | 74% | 67% | 56% | 78% |
| 2 | 96% | 93% | 89% | 89% | 85% | 78% | 63% | 85% |
| 3 | 96% | 96% | 89% | 89% | 85% | 78% | 70% | 86% |
| 5 | 96% | 96% | 96% | 89% | 89% | 89% | 78% | 90% |
| 10 | 96% | 96% | 96% | 96% | 93% | 93% | 89% | 94% |
| 20 | 96% | 96% | 96% | 96% | 96% | 93% | 93% | 95% |

**top2 mean**

| K | 25 | 50 | 100 | 200 | 400 | 800 | 1600 | all |
|---|---|---|---|---|---|---|---|---|
| 1 | 93% | 93% | 81% | 81% | 74% | 59% | 52% | 76% |
| 2 | 96% | 96% | 93% | 89% | 89% | 81% | 63% | 87% |
| 3 | 96% | 96% | 96% | 93% | 89% | 85% | 70% | 89% |
| 5 | 96% | 96% | 96% | 93% | 93% | 93% | 81% | 93% |
| 10 | 96% | 96% | 96% | 96% | 96% | 93% | 93% | 95% |
| 20 | 96% | 96% | 96% | 96% | 96% | 96% | 93% | 96% |

**soft max**

| K | 25 | 50 | 100 | 200 | 400 | 800 | 1600 | all |
|---|---|---|---|---|---|---|---|---|
| 1 | 89% | 89% | 81% | 78% | 67% | 59% | 52% | 74% |
| 2 | 93% | 93% | 93% | 85% | 81% | 74% | 59% | 83% |
| 3 | 96% | 96% | 93% | 93% | 89% | 78% | 67% | 87% |
| 5 | 96% | 96% | 93% | 93% | 93% | 89% | 74% | 90% |
| 10 | 96% | 96% | 96% | 93% | 93% | 93% | 89% | 94% |
| 20 | 96% | 96% | 96% | 96% | 93% | 93% | 93% | 95% |

## Worst gold rank per size (how deep search must go to find every gold)

| method | 25 | 50 | 100 | 200 | 400 | 800 | 1600 |
|---|---|---|---|---|---|---|---|
| max | 21 | 44 | 92 | 180 | 361 | 740 | 1471 |
| max+bonus | 21 | 44 | 92 | 180 | 358 | 733 | 1459 |
| top2 mean | 21 | 42 | 86 | 168 | 332 | 673 | 1353 |
| soft max | 22 | 46 | 93 | 187 | 378 | 763 | 1516 |

## Gold rank per case, production scoring (max)

| case | gold | 25 | 50 | 100 | 200 | 400 | 800 | 1600 |
|---|---|---|---|---|---|---|---|---|
| c01_followup_named_counterpart | Harrow Hill Venue Deposit | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| c02_new_task_known_counterpart | Priya Roadmap Sync | 1 | 1 | 1 | 1 | 1 | 1 | 2 |
| c03_counterpart_not_in_owner_name | Kitchen Reno Quote Follow-up | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| c04_reply_to_email_found_by_unrelated_agent | Inbox Catch-Up Scan | 1 | 1 | 1 | 1 | 1 | 1 | 2 |
| c05_confirm_pending_draft | Copperleaf Renewal Thread | **21** | **44** | **92** | **180** | **361** | **740** | **1471** |
| c06_modify_existing_trigger | Sunday Week Ahead Brief | 2 | 2 | 2 | 3 | 3 | 7 | **11** |
| c07_revive_dormant_counterpart | Mortgage Renewal Paperwork | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| c08_same_first_name_other_person | Engagement Shoot Booking | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| c10_parallel_known_and_new | Email to Gabe Offsite Agenda | 2 | 2 | 4 | 8 | **14** | **26** | **76** |
| c11_dormant_name_match_noor | Save the Date Printing | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| c12_dormant_inference_noor | Save the Date Printing | 2 | 3 | 5 | 8 | 10 | **14** | **23** |
| c13_dormant_name_match_tidewater | Dentist Cleaning Reschedule | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| c14_dormant_inference_tidewater | Dentist Cleaning Reschedule | 1 | 1 | 1 | 1 | 1 | 1 | 2 |
| c15_dormant_name_match_ironwood | Gym Membership Freeze | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| c16_dormant_inference_ironwood | Gym Membership Freeze | 1 | 1 | 1 | 1 | 1 | 1 | 3 |
| c17_dormant_name_match_harold | Neighbour Fence Repair | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| c18_dormant_inference_harold | Neighbour Fence Repair | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| c19_dormant_name_match_marcus | Fernway Designer Search | 1 | 1 | 1 | 1 | 2 | 3 | 3 |
| c20_dormant_inference_marcus | Fernway Designer Search | 1 | 1 | 1 | 1 | 2 | 4 | 7 |
| c21_dormant_paraphrase_wendell | Mortgage Renewal Paperwork | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| c22_dormant_paraphrase_ironwood | Gym Membership Freeze | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| c23_dormant_paraphrase_harold | Neighbour Fence Repair | 2 | 2 | 3 | 3 | 6 | 6 | 10 |
| c24_dormant_paraphrase_tidewater | Dentist Cleaning Reschedule | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| c28_dormant_typo_wendell | Mortgage Renewal Paperwork | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| c29_dormant_typo_tidewater | Dentist Cleaning Reschedule | 1 | 1 | 1 | 1 | 1 | 2 | 5 |
| c30_dormant_typo_ironwood | Gym Membership Freeze | 1 | 1 | 1 | 1 | 1 | 2 | 4 |
| c31_dormant_typo_harold | Neighbour Fence Repair | 1 | 1 | 1 | 1 | 1 | 1 | 1 |

Bold: the gold fell outside the top 10 (for --from-run, the median rank across the IA's queries, and the worst).
