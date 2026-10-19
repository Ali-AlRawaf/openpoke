# Agent search recall

- **Queries:** evals/routing/results/solution_25_x3
- **Embeddings:** openai/text-embedding-3-small (512 dims)
- **Search returns:** top 10 (rosters of 10 or fewer return every agent)

## Recall@10 by scoring method

| method | 25 | all |
|---|---|---|
| max (production) | 100% | 100% |
| max+bonus | 100% | 100% |
| top2 mean | 100% | 100% |
| soft max | 100% | 100% |

## Recall@K, production scoring (max)

| K | 25 |
|---|---|
| 1 | 100% |
| 3 | 100% |
| 5 | 100% |
| 10 | 100% |
| 20 | 100% |

## Gold rank per case, production scoring (max)

| case | gold | 25 |
|---|---|---|
| c04_reply_to_email_found_by_unrelated_agent | Inbox Catch-Up Scan | 1 (worst 1) |
| c05_confirm_pending_draft | Copperleaf Renewal Thread | 1 |
| c06_modify_existing_trigger | Sunday Week Ahead Brief | 1 (worst 1) |
| c07_revive_dormant_counterpart | Mortgage Renewal Paperwork | 1 (worst 1) |
| c08_same_first_name_other_person | Engagement Shoot Booking | 1 |
| c11_dormant_name_match_noor | Save the Date Printing | 1 (worst 1) |
| c12_dormant_inference_noor | Save the Date Printing | 1 (worst 1) |
| c13_dormant_name_match_tidewater | Dentist Cleaning Reschedule | 1 (worst 1) |
| c14_dormant_inference_tidewater | Dentist Cleaning Reschedule | 1 (worst 1) |
| c15_dormant_name_match_ironwood | Gym Membership Freeze | 1 (worst 1) |
| c16_dormant_inference_ironwood | Gym Membership Freeze | 1 (worst 1) |
| c17_dormant_name_match_harold | Neighbour Fence Repair | 1 (worst 1) |
| c18_dormant_inference_harold | Neighbour Fence Repair | 1 (worst 1) |
| c19_dormant_name_match_marcus | Fernway Designer Search | 1 (worst 1) |
| c20_dormant_inference_marcus | Fernway Designer Search | 1 (worst 1) |

Bold: the gold fell outside the top 10 (for --from-run, the median rank across the IA's queries, and the worst).
