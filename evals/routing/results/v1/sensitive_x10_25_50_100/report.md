# Routing eval report: 20261018T013701Z

- **Model:** anthropic/claude-haiku-5.5
- **Commit:** e7c5df6 (dirty)
- **Sizes:** 25, 50, 100
- **Cases:** 4
- **Fixtures:** evals/routing/fixtures
- **Total cost:** $0.1056
- **Started:** 2026-10-18T01:37:01+00:00  **Finished:** 2026-10-18T01:37:57+00:00

## Per size

| size | accuracy | correct | wrong_reuse | false_create | false_reuse | missed | error | extra | calls | mean prompt tok | mean cached tok | mean completion tok | mean reasoning tok | cost $ | mean latency s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 25 | 88% (44/50) | 44 | 0 | 6 | 0 | 0 | 0 | 0 | 40 | 16,490.5 | 13,189.2 | 622.2 | 245.9 | 0.0342 | 3.6 |
| 50 | 88% (44/50) | 44 | 0 | 6 | 0 | 0 | 0 | 0 | 40 | 17,013.5 | 13,607.6 | 615.3 | 238.4 | 0.0348 | 3.5 |
| 100 | 62% (31/50) | 31 | 0 | 19 | 0 | 0 | 0 | 0 | 40 | 18,067.5 | 14,450.8 | 635.8 | 242.3 | 0.0366 | 3.6 |

Accuracy pools every repeat. Token columns are means per LLM call; latency is per case run.

## Case x size

| case | category | 25 | 50 | 100 | pattern |
|---|---|---|---|---|---|
| c02_new_task_known_counterpart | new_task_known_counterpart | 7/10 (false_create×3) | 6/10 (false_create×4) | 2/10 (false_create×8) | passes small, fails large (overload?) |
| c04_reply_to_email_found_by_unrelated_agent | reply_to_found_email | 7/10 (false_create×3) | 9/10 (false_create×1) | 2/10 (false_create×8) | passes small, fails large (overload?) |
| c07_revive_dormant_counterpart | dormant_counterpart_summary_only | 10/10 | 9/10 (false_create×1) | 10/10 | pass at every size |
| c10_parallel_known_and_new | parallel_known_and_new | 10/10 | 10/10 | 7/10 (false_create×3) | pass at every size |

## Misses

### c02_new_task_known_counterpart @ 25 #0: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Email to Priya Natarajan Client Demo`
- **All delegations:** `Email to Priya Natarajan Client Demo`
- **Instructions:**

> Draft (do NOT send) an email to Priya Natarajan at priya@northfoldstudio.ca, a Northfold colleague (not Priya Sandhu the photographer). Ask if she can run the client demo this Friday, Oct 23, since Theo is double booked. Keep it short, casual, and friendly, signed Theo. If there is an existing client demo thread with Priya Natarajan, draft the reply in that thread. Return the exact recipient, subject, body, and draft ID for Theo's review.

### c02_new_task_known_counterpart @ 25 #3: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Priya Client Demo Cover`
- **All delegations:** `Priya Client Demo Cover`
- **Instructions:**

> Draft (do not send) an email to priya@northfoldstudio.ca (Priya Natarajan, Northfold Studio). Subject: Client demo Friday. Body: ask if she can run the client demo this Friday (Oct 23) because Theo is double booked. Keep it short and casual, signed Theo. Use a new draft, not the Q4 roadmap thread. Report back the draft details for Theo's review.

### c02_new_task_known_counterpart @ 25 #4: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Priya Natarajan Client Demo Cover`
- **All delegations:** `Priya Natarajan Client Demo Cover`
- **Instructions:**

> Draft (do NOT send) an email to Priya Natarajan at priya@northfoldstudio.ca (Northfold Studio, not Priya Sandhu the photographer). Ask if she can run the client demo this Friday, Oct 23, 2026, because Theo is double booked. Keep it short, casual, and friendly. Offer to brief her on anything she needs beforehand. If there is an existing Northfold thread with Priya Natarajan, use it; otherwise start a new email. Return the exact To, Subject, and Body, plus the Draft ID, and wait for the user's confirmation before sending.

### c02_new_task_known_counterpart @ 50 #0: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Priya Demo Coverage Request`
- **All delegations:** `Priya Demo Coverage Request`
- **Instructions:**

> Draft a new email to priya@northfoldstudio.ca (Priya Natarajan, Northfold Studio, not Priya Sandhu the photographer). Subject: Client demo this Friday. Body: Theo is double booked and asks if she can run the client demo this Friday, Oct 23. Keep it short, casual, and polite, signed Theo. Do not send it. Create the draft only and return the exact To, Subject, and Body along with the draft ID. Wait for the user's explicit confirmation before sending.

### c02_new_task_known_counterpart @ 50 #3: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Priya Demo Coverage Request`
- **All delegations:** `Priya Demo Coverage Request`
- **Instructions:**

> Draft a new email (do not send) to Priya Natarajan at priya@northfoldstudio.ca. Subject: "Client demo Friday - can you cover?" Body: Theo is double booked for the client demo this Friday (Oct 23) and asks whether Priya can run it instead. Keep it short, casual, and friendly, signed Theo. Do not mention her Q4 roadmap thread. Return the exact draft text and draft ID. Do not send anything.

### c02_new_task_known_counterpart @ 50 #4: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Priya Demo Coverage Request`
- **All delegations:** `Priya Demo Coverage Request`
- **Instructions:**

> Draft (do NOT send) an email from Theo Marchetti to Priya Natarajan at priya@northfoldstudio.ca asking if she can run the client demo this Friday (Oct 23, 2026). Theo is double booked. Keep it short, casual, and friendly. Ask her to reply if she can take it, and mention he can send the demo notes or materials over. Return the exact recipient, subject, body, and draft ID for Theo to review. Do not send.

### c02_new_task_known_counterpart @ 50 #8: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Priya Demo Coverage Request`
- **All delegations:** `Priya Demo Coverage Request`
- **Instructions:**

> Draft (do NOT send) a short email to Priya Natarajan at priya@northfoldstudio.ca asking if she can run the client demo this Friday, since Theo is double booked. Keep it brief and friendly. Ask her to confirm if she can take it, and mention he'll send the demo details or notes if she can. Use the existing Priya Natarajan thread if one is available for the reply. Do not send. Return the exact recipient, subject, and body, plus the draft ID.

### c02_new_task_known_counterpart @ 100 #0: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Priya Client Demo Swap`
- **All delegations:** `Priya Client Demo Swap`
- **Instructions:**

> Draft (do not send) an email to Priya Natarajan at priya@northfoldstudio.ca asking if she can run the client demo this Friday (Oct 23, 2026) because Theo is double booked. Keep it short, casual, and friendly. Sign off as Theo. Do not send anything. If there is an existing Priya Natarajan thread about the client demo or Friday schedule, reply in that thread; otherwise create a new draft. Return the exact recipient, subject, and body, plus the draft ID.

### c02_new_task_known_counterpart @ 100 #1: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Priya Demo Coverage Request`
- **All delegations:** `Priya Demo Coverage Request`
- **Instructions:**

> Draft a new email (do not send) to priya@northfoldstudio.ca (Priya Natarajan, Northfold Studio). Subject: Client demo Friday. Body: Theo is double booked and asks whether she can run the client demo this Friday. Keep it short, casual and polite, signed Theo. Do not start a new thread; create a fresh draft. Report back the draft details (to, subject, body, draft ID) and nothing else.

### c02_new_task_known_counterpart @ 100 #2: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Priya Demo Coverage Request`
- **All delegations:** `Priya Demo Coverage Request`
- **Instructions:**

> Draft (do not send) a short email to Priya Natarajan at priya@northfoldstudio.ca asking if she can run the client demo on Friday because Theo is double booked. Keep it brief and casual, friendly tone, and ask her to confirm if she can. Ideally reply in the existing Northfold thread with Priya Natarajan if one exists (e.g. the Q4 roadmap thread). Do not send. Return the exact To, Subject, and Body, plus the draft ID.

### c02_new_task_known_counterpart @ 100 #4: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Priya Client Demo Cover`
- **All delegations:** `Priya Client Demo Cover`
- **Instructions:**

> Draft a new email (do not send) to priya@northfoldstudio.ca from Theo. Subject: Client demo Friday. Body: a short, casual note from Theo saying he's double booked on Friday Oct 23 and asking if she can run the client demo that day instead. Keep it to 2-3 sentences, signed Theo. Create the draft and return the exact to, subject, body, and draft ID. Do not send.

### c02_new_task_known_counterpart @ 100 #5: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Priya Demo Coverage Request`
- **All delegations:** `Priya Demo Coverage Request`
- **Instructions:**

> Draft an email (do not send) to priya@northfoldstudio.ca (Priya Natarajan, Northfold Studio, colleague) asking if she can run the client demo this Friday, Oct 23, since Theo is double booked. Keep it short and casual, signed Theo. Ask her to reply to confirm, and mention Theo can brief her on the demo beforehand if useful. Return the exact subject and body and the draft ID. Do not send anything. If there's a demo invite or calendar entry for Friday in the inbox, note the time and client name in your reply so Theo can review it, but don't include confidential details in the email itself.

### c02_new_task_known_counterpart @ 100 #6: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Priya Client Demo Cover`
- **All delegations:** `Priya Client Demo Cover`
- **Instructions:**

> Draft (do NOT send) an email to priya@northfoldstudio.ca (Priya Natarajan, Northfold Studio, not Priya Sandhu the photographer). Subject: Client demo this Friday. Body: Theo is double booked this Friday and asks whether she can run the client demo instead. Keep it short, casual, and friendly, signed Theo. Offer to send over any notes or context she needs. Return the exact draft text, recipient, subject, and draft ID for Theo's review. Nothing should be sent.

### c02_new_task_known_counterpart @ 100 #7: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Priya Client Demo Cover`
- **All delegations:** `Priya Client Demo Cover`
- **Instructions:**

> Draft (do not send) an email from Theo Marchetti to Priya Natarajan at priya@northfoldstudio.ca. Subject: Client demo Friday. Body: ask if she can run the client demo this Friday, since Theo is double booked. Keep it short and friendly, sign off as Theo. Use the upcoming Friday relative to today. Reply with the exact draft (to, subject, body, draft ID). Wait for Theo's approval before sending anything.

### c02_new_task_known_counterpart @ 100 #9: `false_create`

- **Task:** ask Priya Natarajan to run Friday's client demo
- **Gold:** `Priya Roadmap Sync`
- **Chosen:** `Priya Demo Cover Request`
- **All delegations:** `Priya Demo Cover Request`
- **Instructions:**

> Create a draft email (do NOT send) to priya@northfoldstudio.ca (Priya Natarajan, Northfold Studio, not Priya Sandhu the photographer). Subject: Client demo Friday. Body: a short, friendly note from Theo asking if she can run the client demo this Friday (Oct 23, 2026) because Theo is double booked. Keep it to 2-3 sentences, casual and direct, signed Theo. Ask her to reply if it works. Return the exact draft content (to, subject, body) and the draft ID. If there is an existing thread with Priya about the demo, put the draft in that thread and note the thread ID.

### c04_reply_to_email_found_by_unrelated_agent @ 25 #0: `false_create`

- **Task:** reply to Bramblewood Auto's winter tire email booking Sat Oct 24 9:00
- **Gold:** `Inbox Catch-Up Scan`
- **Chosen:** `Bramblewood Tire Booking`
- **All delegations:** `Bramblewood Tire Booking`
- **Instructions:**

> Create a reply draft (do NOT send) to Bramblewood Auto Service (service@bramblewoodauto.ca) in the existing thread 1a13a9c097866746, responding to their "Time to book your winter tire changeover" email. Book the winter tire changeover for Saturday, Oct 24 at 9:00 AM. Keep it short and polite, signed Theo. Note Theo's winter tires are in their storage. Return the full draft text (to, subject, body) and draft ID for review.

### c04_reply_to_email_found_by_unrelated_agent @ 25 #1: `false_create`

- **Task:** reply to Bramblewood Auto's winter tire email booking Sat Oct 24 9:00
- **Gold:** `Inbox Catch-Up Scan`
- **Chosen:** `Bramblewood Tire Changeover Reply`
- **All delegations:** `Bramblewood Tire Changeover Reply`
- **Instructions:**

> Draft a reply (do not send) to the Bramblewood Auto Service email "Time to book your winter tire changeover" (service@bramblewoodauto.ca, thread 1a13a9c097866746). Tell them Theo is booking the winter tire changeover for Saturday Oct 24 at 9:00 AM. Keep it short and casual, signed Theo. Return the exact To, Subject, and body, plus the draft ID. Do not send anything until I confirm.

### c04_reply_to_email_found_by_unrelated_agent @ 25 #5: `false_create`

- **Task:** reply to Bramblewood Auto's winter tire email booking Sat Oct 24 9:00
- **Gold:** `Inbox Catch-Up Scan`
- **Chosen:** `Bramblewood Tire Booking`
- **All delegations:** `Bramblewood Tire Booking`
- **Instructions:**

> Reply to the Bramblewood Auto Service email "Time to book your winter tire changeover" (service@bramblewoodauto.ca, thread ID 1a13a9c097866746). Booking: Saturday Oct 24, 2026 at 9:00 AM for the winter tire changeover ($89.95 + tax). Keep the reply short and casual, signed Theo. Create a draft only. Do NOT send it. Return the full draft (to, subject, body, draft ID) so I can show it to the user for approval.

### c04_reply_to_email_found_by_unrelated_agent @ 50 #0: `false_create`

- **Task:** reply to Bramblewood Auto's winter tire email booking Sat Oct 24 9:00
- **Gold:** `Inbox Catch-Up Scan`
- **Chosen:** `Bramblewood Winter Tire Booking`
- **All delegations:** `Bramblewood Winter Tire Booking`
- **Instructions:**

> Draft a reply (do NOT send) to the Bramblewood Auto Service email about the winter tire changeover. Reply in thread ID 1a13a9c097866746 to service@bramblewoodauto.ca. Confirm the booking for Saturday Oct 24 at 9:00 AM for the winter tire changeover ($89.95 + tax) for Theo Marchetti. Keep it short and friendly, signed Theo. Return the full draft text (to, subject, body, draft ID) so I can show it to the user for approval.

### c04_reply_to_email_found_by_unrelated_agent @ 100 #0: `false_create`

- **Task:** reply to Bramblewood Auto's winter tire email booking Sat Oct 24 9:00
- **Gold:** `Inbox Catch-Up Scan`
- **Chosen:** `Bramblewood Winter Tire Booking`
- **All delegations:** `Bramblewood Winter Tire Booking`
- **Instructions:**

> Draft a reply (do not send) to Bramblewood Auto Service (service@bramblewoodauto.ca) in the existing thread 1a13a9c097866746 ("Time to book your winter tire changeover", Oct 14). Confirm Theo's winter tire changeover for Saturday Oct 24 at 9:00 AM ($89.95 + tax). Keep it short, signed Theo. Return the exact draft (to, subject, body, draft ID) for review. Do not send.

### c04_reply_to_email_found_by_unrelated_agent @ 100 #1: `false_create`

- **Task:** reply to Bramblewood Auto's winter tire email booking Sat Oct 24 9:00
- **Gold:** `Inbox Catch-Up Scan`
- **Chosen:** `Bramblewood Winter Tire Booking`
- **All delegations:** `Bramblewood Winter Tire Booking`
- **Instructions:**

> Draft a reply (do not send) to the Bramblewood Auto Service email "Time to book your winter tire changeover" (from service@bramblewoodauto.ca, thread ID 1a13a9c097866746). The reply should confirm the Saturday, October 24, 2026 at 9:00 AM slot for the winter tire changeover ($89.95 + tax). Sign off as Theo. Keep it short and polite. Return the exact recipient, subject, and body, plus the draft ID. Nothing should be sent.

### c04_reply_to_email_found_by_unrelated_agent @ 100 #3: `false_create`

- **Task:** reply to Bramblewood Auto's winter tire email booking Sat Oct 24 9:00
- **Gold:** `Inbox Catch-Up Scan`
- **Chosen:** `Bramblewood Winter Tire Booking`
- **All delegations:** `Bramblewood Winter Tire Booking`
- **Instructions:**

> Draft a reply (do not send) to the Bramblewood Auto Service email "Time to book your winter tire changeover" (thread ID 1a13a9c097866746, sent to service@bramblewoodauto.ca). Confirm Theo's booking for the Saturday, October 24, 2026 at 9:00 AM slot for the winter tire changeover ($89.95 + tax). Keep it short and signed "Theo". Return the exact recipient, subject, body, and draft ID. Do not send anything.

### c04_reply_to_email_found_by_unrelated_agent @ 100 #4: `false_create`

- **Task:** reply to Bramblewood Auto's winter tire email booking Sat Oct 24 9:00
- **Gold:** `Inbox Catch-Up Scan`
- **Chosen:** `Bramblewood Tire Booking Reply`
- **All delegations:** `Bramblewood Tire Booking Reply`
- **Instructions:**

> Draft a reply (do not send) to the Bramblewood Auto Service email "Time to book your winter tire changeover" (thread ID 1a13a9c097866746, sender service@bramblewoodauto.ca). Confirm Theo's booking for Saturday Oct 24 at 9:00 AM for the winter tire changeover ($89.95 + tax). Keep it short and polite, signed Theo. Return the exact To, Subject, and Body, plus the draft ID. Wait for explicit user confirmation before sending anything.

### c04_reply_to_email_found_by_unrelated_agent @ 100 #5: `false_create`

- **Task:** reply to Bramblewood Auto's winter tire email booking Sat Oct 24 9:00
- **Gold:** `Inbox Catch-Up Scan`
- **Chosen:** `Bramblewood Tire Changeover Reply`
- **All delegations:** `Bramblewood Tire Changeover Reply`
- **Instructions:**

> Draft a reply (do not send) to Bramblewood Auto Service (service@bramblewoodauto.ca) in the existing thread 1a13a9c097866746, subject "Time to book your winter tire changeover". Tell them Theo would like to book the Saturday, October 24 at 9:00 AM slot for the winter tire changeover ($89.95 + tax). Keep it short and signed Theo. Return the exact recipient, subject, body, and draft ID. Do not send anything.

### c04_reply_to_email_found_by_unrelated_agent @ 100 #6: `false_create`

- **Task:** reply to Bramblewood Auto's winter tire email booking Sat Oct 24 9:00
- **Gold:** `Inbox Catch-Up Scan`
- **Chosen:** `Bramblewood Tire Changeover Booking`
- **All delegations:** `Bramblewood Tire Changeover Booking`
- **Instructions:**

> Reply to Bramblewood Auto Service (service@bramblewoodauto.ca) in thread 1a13a9c097866746, the "Time to book your winter tire changeover" email. Book the Saturday October 24, 2026 at 9:00 AM slot for the winter tire changeover. Keep it short and polite, sign off as Theo. Create a draft only and do NOT send it. Return the exact To, Subject, and Body, plus the Draft ID, and wait for my explicit confirmation before sending.

### c04_reply_to_email_found_by_unrelated_agent @ 100 #7: `false_create`

- **Task:** reply to Bramblewood Auto's winter tire email booking Sat Oct 24 9:00
- **Gold:** `Inbox Catch-Up Scan`
- **Chosen:** `Bramblewood Winter Tire Booking`
- **All delegations:** `Bramblewood Winter Tire Booking`
- **Instructions:**

> Draft a reply (do NOT send) to Bramblewood Auto Service (service@bramblewoodauto.ca) in thread 1a13a9c097866746, replying to their "Time to book your winter tire changeover" email. Content: Theo wants to book the winter tire changeover for Saturday Oct 24 at 9:00 AM. Keep it short and polite, signed Theo. Return the exact To, Subject, and Body, plus the draft ID, so I can show Theo for approval.

### c04_reply_to_email_found_by_unrelated_agent @ 100 #8: `false_create`

- **Task:** reply to Bramblewood Auto's winter tire email booking Sat Oct 24 9:00
- **Gold:** `Inbox Catch-Up Scan`
- **Chosen:** `Bramblewood Winter Tire Booking`
- **All delegations:** `Bramblewood Winter Tire Booking`
- **Instructions:**

> Draft a reply (do NOT send) to service@bramblewoodauto.ca in the existing winter tire changeover thread (thread ID 1a13a9c097866746, email "Time to book your winter tire changeover"). The reply should book the changeover for Saturday Oct 24 at 9:00 AM for Theo Marchetti, and be short and casual, signed Theo. Confirm the slot in the body. Return the exact To, Subject, Body, and Draft ID so the user can review. Do not send anything.

### c07_revive_dormant_counterpart @ 50 #7: `false_create`

- **Task:** ask Wendell Achebe about locking the renewal rate before Nov 4
- **Gold:** `Mortgage Renewal Paperwork`
- **Chosen:** `Brightmoor Rate Lock Question`
- **All delegations:** `Brightmoor Rate Lock Question`
- **Instructions:**

> Draft (do NOT send) an email to Wendell Achebe at wendell.achebe@brightmoorcu.ca, from Theo Marchetti, asking whether we should lock the mortgage rate now or wait until after the Nov 4 rate announcement. Reply in the existing Brightmoor renewal thread if one exists. Keep it short and direct. Ask him for his recommendation and the lock terms/fees for each option, and confirm the hold window (up to 120 days before the Dec 1 maturity). Return the exact draft (To, Subject, Body, Draft ID) so I can show it to the user for approval.

### c10_parallel_known_and_new @ 100 #4: `false_create`

- **Task:** tell Gabe Theo will be ~20 min late to Wednesday's offsite kickoff
- **Gold:** `Email to Gabe Offsite Agenda`
- **Chosen:** `Email to Gabe Kickoff Late`
- **All delegations:** `Email to Gabe Kickoff Late`, `Halcyon Chimney Sweep Request`
- **Every task in this case:**
  - tell Gabe Theo will be ~20 min late to Wednesday's offsite kickoff: gold `Email to Gabe Offsite Agenda`, chosen `Email to Gabe Kickoff Late` → `false_create`
  - ask Halcyon Chimney about a chimney sweep before mid-November: gold `NEW`, chosen `Halcyon Chimney Sweep Request` → `correct`
- **Instructions:**

> Draft a reply to Gabe (gabe@northfoldstudio.ca) in the existing Cedar Hollow offsite thread (thread 1a0e88ccde8db8a5, subject "Re: Offsite agenda - Cedar Hollow, Oct 21-22"). Message: Theo will be about 20 minutes late to the Wednesday Oct 21 10:00 kickoff because of a train. Keep it short and casual, signed Theo. Create the draft only. Do NOT send it. Return the exact To, Subject, and Body, plus the draft ID.

### c10_parallel_known_and_new @ 100 #5: `false_create`

- **Task:** tell Gabe Theo will be ~20 min late to Wednesday's offsite kickoff
- **Gold:** `Email to Gabe Offsite Agenda`
- **Chosen:** `Gabe Offsite Late Arrival`
- **All delegations:** `Gabe Offsite Late Arrival`, `Halcyon Chimney Sweep Request`
- **Every task in this case:**
  - tell Gabe Theo will be ~20 min late to Wednesday's offsite kickoff: gold `Email to Gabe Offsite Agenda`, chosen `Gabe Offsite Late Arrival` → `false_create`
  - ask Halcyon Chimney about a chimney sweep before mid-November: gold `NEW`, chosen `Halcyon Chimney Sweep Request` → `correct`
- **Instructions:**

> Draft (do not send) a reply to gabe@northfoldstudio.ca on the existing Cedar Hollow offsite thread (thread ID 1a0e88ccde8db8a5, subject "Re: Offsite agenda - Cedar Hollow, Oct 21-22"). Message content: Theo will be about 20 minutes late to the Wednesday Oct 21 10:00 kickoff because of a train. Keep it short, signed Theo. Return the exact draft (to, subject, body, draft ID) for review. Do not send.

### c10_parallel_known_and_new @ 100 #8: `false_create`

- **Task:** tell Gabe Theo will be ~20 min late to Wednesday's offsite kickoff
- **Gold:** `Email to Gabe Offsite Agenda`
- **Chosen:** `Gabe Offsite Late Note`
- **All delegations:** `Gabe Offsite Late Note`, `Halcyon Chimney Sweep Request`
- **Every task in this case:**
  - tell Gabe Theo will be ~20 min late to Wednesday's offsite kickoff: gold `Email to Gabe Offsite Agenda`, chosen `Gabe Offsite Late Note` → `false_create`
  - ask Halcyon Chimney about a chimney sweep before mid-November: gold `NEW`, chosen `Halcyon Chimney Sweep Request` → `correct`
- **Instructions:**

> Draft a reply (do NOT send) to Gabe at gabe@northfoldstudio.ca on the existing Cedar Hollow offsite thread (thread ID 1a0e88ccde8db8a5). Message: Theo will be about 20 minutes late to the Wednesday Oct 21 10:00 kickoff because of a train. Keep it to two or three short lines, signed Theo. Return the exact draft (to, subject, body, draft ID) for user review and wait for explicit approval before sending.
