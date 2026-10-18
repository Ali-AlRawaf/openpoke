# Routing eval report: 20261017T200920Z

- **Model:** anthropic/claude-haiku-5.5
- **Commit:** e7c5df6 (dirty)
- **Sizes:** 25, 50, 100, 200, 400
- **Cases:** 10
- **Fixtures:** evals/routing/fixtures
- **Total cost:** $0.1345
- **Started:** 2026-10-17T20:09:20+00:00  **Finished:** 2026-10-17T20:10:02+00:00

## Per size

| size | accuracy | correct | wrong_reuse | false_create | false_reuse | missed | error | extra | calls | mean prompt tok | mean cached tok | mean completion tok | mean reasoning tok | cost $ | mean latency s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 25 | 82% (9/11) | 9 | 0 | 2 | 0 | 0 | 0 | 0 | 10 | 16486 | 0 | 525 | 191.7 | 0.0232 | 3.0 |
| 50 | 91% (10/11) | 10 | 0 | 1 | 0 | 0 | 0 | 0 | 10 | 17009 | 0 | 542.3 | 223 | 0.0240 | 3.1 |
| 100 | 64% (7/11) | 7 | 0 | 3 | 0 | 1 | 0 | 0 | 11 | 18113 | 1641 | 520 | 215.8 | 0.0257 | 3.4 |
| 200 | 82% (9/11) | 9 | 0 | 1 | 0 | 1 | 0 | 0 | 11 | 20,161.3 | 1,828.1 | 513 | 219.3 | 0.0282 | 3.3 |
| 400 | 82% (9/11) | 9 | 0 | 2 | 0 | 0 | 0 | 0 | 10 | 24321 | 0 | 599.8 | 250.2 | 0.0334 | 3.5 |

Accuracy pools every repeat. Token columns are means per LLM call; latency is per case run.

## Case x size

| case | category | 25 | 50 | 100 | 200 | 400 | pattern |
|---|---|---|---|---|---|---|---|
| c01_followup_named_counterpart | followup_counterpart_in_name | ✓ | ✓ | ✓ | ✓ | ✓ | pass at every size |
| c02_new_task_known_counterpart | new_task_known_counterpart | false_create | false_create | false_create | ✓ | false_create | mixed |
| c03_counterpart_not_in_owner_name | new_task_owner_name_unrelated | ✓ | ✓ | ✓ | ✓ | ✓ | pass at every size |
| c04_reply_to_email_found_by_unrelated_agent | reply_to_found_email | false_create | ✓ | false_create | false_create | ✓ | mixed |
| c05_confirm_pending_draft | confirm_pending_draft | ✓ | ✓ | ✓ | ✓ | ✓ | pass at every size |
| c06_modify_existing_trigger | modify_reminder | ✓ | ✓ | ✓ | ✓ | ✓ | pass at every size |
| c07_revive_dormant_counterpart | dormant_counterpart_summary_only | ✓ | ✓ | ✓ | ✓ | false_create | passes small, fails large (overload?) |
| c08_same_first_name_other_person | same_first_name_other_person | ✓ | ✓ | missed | missed | ✓ | mixed |
| c09_new_counterpart_overlapping_name | new_counterpart_overlapping_name | ✓ | ✓ | ✓ | ✓ | ✓ | pass at every size |
| c10_parallel_known_and_new | parallel_known_and_new | ✓+✓ | ✓+✓ | false_create+✓ | ✓+✓ | ✓+✓ | mixed |

## Misses

### c02_new_task_known_counterpart @ 25 #0: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Priya Demo Coverage Request`
- **All delegations:** `Priya Demo Coverage Request`
- **Instructions:**

> Draft (do not send) an email to priya@northfoldstudio.ca (Priya Natarajan, Northfold Studio). Subject: Client demo Friday. Body: Theo is double booked on Friday Oct 23 and can't run the client demo. Ask if she can cover the demo that day. Keep it short, casual, and friendly, signed Theo. If there is an existing thread with Priya Natarajan about client demos or the Friday schedule, reply on that thread; otherwise create a new draft. Return the exact To, Subject, and Body, plus the Draft ID. Wait for explicit approval before sending anything.

### c02_new_task_known_counterpart @ 50 #0: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Priya Demo Request`
- **All delegations:** `Priya Demo Request`
- **Instructions:**

> Draft a short email to priya@northfoldstudio.ca (Priya Natarajan, Northfold Studio, not Priya Sandhu). Subject: Client demo Friday. Body: Theo is double booked this Friday (Oct 23) and asks if she can run the client demo that day. Keep it brief, casual, and friendly, signed Theo. If possible, reply in the existing Priya Natarajan thread (1a13a8af27844303 or thread 19fb855805877548). Do NOT send. Create the draft only and return the exact recipient, subject, and body, plus the draft ID.

### c02_new_task_known_counterpart @ 100 #0: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Priya Natarajan Demo Cover`
- **All delegations:** `Priya Natarajan Demo Cover`
- **Instructions:**

> Draft an email (do not send) to priya@northfoldstudio.ca (Priya Natarajan, Northfold Studio). Subject: Client demo Friday. Body: Theo is double booked and asks whether she can run the client demo this Friday, Oct 23. Keep it short, casual, and friendly, signed Theo. Do not contact Priya Sandhu (Lumen & Linen), who is a different person. Return the exact draft text and draft ID, and note whether a demo time or details from prior threads should be included.

### c02_new_task_known_counterpart @ 400 #0: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Priya Demo Coverage Request`
- **All delegations:** `Priya Demo Coverage Request`
- **Instructions:**

> Draft (do not send) an email from Theo Marchetti to Priya Natarajan at priya@northfoldstudio.ca. Subject: "Client demo Friday". Ask if she can run the client demo this Friday, Oct 23, because Theo is double booked. Keep it short and casual, 2-3 sentences, signed Theo. Do not mention the Lumen & Linen Priya (Priya Sandhu). Return the exact To, Subject, Body, and draft ID so it can be shown to Theo for approval. Nothing should be sent.

### c04_reply_to_email_found_by_unrelated_agent @ 25 #0: `false_create`

- **Task:** reply to Bramblewood Auto's winter tire email booking Sat Oct 24 9:00
- **Gold:** `Inbox Catch-Up Scan`
- **Chosen:** `Bramblewood Winter Tire Booking`
- **All delegations:** `Bramblewood Winter Tire Booking`
- **Instructions:**

> Draft a reply (do not send) to the Bramblewood Auto Service email "Time to book your winter tire changeover" (service@bramblewoodauto.ca, thread ID 1a13a9c097866746). Confirm Theo's winter tire changeover for Saturday October 24, 2026 at 9:00 AM. Keep it short and casual, signed Theo. Ask them to reply to confirm if the slot is held. Return the exact To, Subject, and Body, plus the Draft ID. Do not send anything.

### c04_reply_to_email_found_by_unrelated_agent @ 100 #0: `false_create`

- **Task:** reply to Bramblewood Auto's winter tire email booking Sat Oct 24 9:00
- **Gold:** `Inbox Catch-Up Scan`
- **Chosen:** `Bramblewood Winter Tire Booking`
- **All delegations:** `Bramblewood Winter Tire Booking`
- **Instructions:**

> Draft a reply to Bramblewood Auto Service (service@bramblewoodauto.ca) in the winter tire changeover thread (thread ID 1a13a9c097866746, subject "Time to book your winter tire changeover"). Book the Saturday Oct 24 at 9:00 AM slot for Theo's winter tire changeover ($89.95 + tax, they're storing his winter tires). Keep it short and polite, signed Theo. Do NOT send. Create the draft only and return the exact To, Subject, and Body, plus the draft ID.

### c04_reply_to_email_found_by_unrelated_agent @ 200 #0: `false_create`

- **Task:** reply to Bramblewood Auto's winter tire email booking Sat Oct 24 9:00
- **Gold:** `Inbox Catch-Up Scan`
- **Chosen:** `Bramblewood Tire Changeover Reply`
- **All delegations:** `Bramblewood Tire Changeover Reply`
- **Instructions:**

> Draft a reply (do NOT send) on the Bramblewood Auto thread (thread ID 1a13a9c097866746, from service@bramblewoodauto.ca, subject "Time to book your winter tire changeover") booking the winter tire changeover for Saturday October 24, 2026 at 9:00 AM. Keep it short and polite, signed Theo. Return the exact draft (to, subject, body, draft ID) so it can be shown to the user for approval.

### c07_revive_dormant_counterpart @ 400 #0: `false_create`

- **Task:** ask Wendell Achebe about locking the renewal rate before Nov 4
- **Gold:** `Mortgage Renewal Paperwork`
- **Chosen:** `Brightmoor Rate Lock Question`
- **All delegations:** `Brightmoor Rate Lock Question`
- **Instructions:**

> Draft (do not send) an email to Wendell Achebe at wendell.achebe@brightmoorcu.ca asking whether Theo Marchetti should lock the mortgage rate now or wait until after the Nov 4 rate announcement. Context to reference: the Brightmoor mortgage term ends Dec 1, 2026; Wendell previously advised deciding before the Nov 4 announcement and that holds are allowed up to 120 days before maturity. Ask him to outline the rate-lock options and any cost or deadline for a hold, and what he recommends. Keep it short and casual, signed Theo. Reply in the existing Brightmoor renewal thread if one is found. Return the exact To, Subject, Body, Draft ID, and Thread ID.

### c08_same_first_name_other_person @ 100 #0: `missed`

- **Task:** check whether Priya Sandhu sent the engagement proofs gallery
- **Gold:** `Engagement Shoot Booking`
- **Chosen:** (none)
- **All delegations:** (none)

### c08_same_first_name_other_person @ 200 #0: `missed`

- **Task:** check whether Priya Sandhu sent the engagement proofs gallery
- **Gold:** `Engagement Shoot Booking`
- **Chosen:** (none)
- **All delegations:** (none)

### c10_parallel_known_and_new @ 100 #0: `false_create`

- **Task:** tell Gabe Theo will be ~20 min late to Wednesday's offsite kickoff
- **Gold:** `Email to Gabe Offsite Agenda`
- **Chosen:** `Gabe Kickoff Late Notice`
- **All delegations:** `Gabe Kickoff Late Notice`, `Halcyon Chimney Sweep Request`
- **Every task in this case:**
  - tell Gabe Theo will be ~20 min late to Wednesday's offsite kickoff: gold `Email to Gabe Offsite Agenda`, chosen `Gabe Kickoff Late Notice` → `false_create`
  - ask Halcyon Chimney about a chimney sweep before mid-November: gold `NEW`, chosen `Halcyon Chimney Sweep Request` → `correct`
- **Instructions:**

> Draft a reply to Gabe (gabe@northfoldstudio.ca) in the existing Cedar Hollow offsite thread (thread 1a0e88ccde8db8a5, subject "Re: Offsite agenda - Cedar Hollow, Oct 21-22"). Tell him Theo will be about 20 minutes late to the Wednesday Oct 21 10:00 kickoff because of a train delay. Keep it to 2 short sentences, signed Theo. Do NOT send it. Return the draft with its draft ID and recipient, subject, and body.
