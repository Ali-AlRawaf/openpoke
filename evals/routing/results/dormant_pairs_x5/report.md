# Routing eval report: 20261018T160841Z

- **Model:** anthropic/claude-haiku-5.5
- **Commit:** fd13e2e (dirty)
- **Sizes:** 25, 50, 100, 200, 400, 800, 1600
- **Cases:** 10
- **Fixtures:** evals/routing/fixtures
- **Total cost:** $0.4005
- **Started:** 2026-10-18T16:08:41+00:00  **Finished:** 2026-10-18T16:11:20+00:00

## Per size

| size | accuracy | correct | wrong_reuse | false_create | false_reuse | missed | error | extra | calls | mean prompt tok | mean cached tok | mean completion tok | mean reasoning tok | cost $ | mean latency s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 25 | 100% (50/50) | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 50 | 16,472.8 | 13,175.0 | 537.1 | 200.7 | 0.0406 | 3.0 |
| 50 | 100% (50/50) | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 50 | 16,994.8 | 13,592.6 | 526.2 | 197.4 | 0.0412 | 2.9 |
| 100 | 100% (50/50) | 50 | 0 | 0 | 0 | 0 | 0 | 0 | 50 | 18,053.8 | 14,439.8 | 568.2 | 223.5 | 0.0440 | 3.1 |
| 200 | 94% (47/50) | 47 | 0 | 3 | 0 | 0 | 0 | 0 | 50 | 20,125.8 | 16,097.4 | 589.5 | 240.8 | 0.0480 | 3.2 |
| 400 | 88% (44/50) | 44 | 0 | 6 | 0 | 0 | 0 | 0 | 50 | 24,347.8 | 19,475.0 | 609.0 | 256.4 | 0.0554 | 3.4 |
| 800 | 90% (45/50) | 45 | 0 | 5 | 0 | 0 | 0 | 0 | 50 | 33,552.8 | 26,839.0 | 577.9 | 238.1 | 0.0698 | 3.2 |
| 1600 | 82% (41/50) | 41 | 0 | 9 | 0 | 0 | 0 | 0 | 50 | 51,971.8 | 41,574.2 | 627.3 | 275.3 | 0.1014 | 3.5 |

Accuracy pools every repeat. Token columns are means per LLM call; latency is per case run.

## Case x size

| case | category | 25 | 50 | 100 | 200 | 400 | 800 | 1600 | pattern |
|---|---|---|---|---|---|---|---|---|---|
| c11_dormant_name_match_noor | dormant_name_match | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | pass at every size |
| c12_dormant_inference_noor | dormant_inference | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | pass at every size |
| c13_dormant_name_match_tidewater | dormant_name_match | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 3/5 (false_create×2) | pass at every size |
| c14_dormant_inference_tidewater | dormant_inference | 5/5 | 5/5 | 5/5 | 3/5 (false_create×2) | 1/5 (false_create×4) | 4/5 (false_create×1) | 2/5 (false_create×3) | mixed |
| c15_dormant_name_match_ironwood | dormant_name_match | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | pass at every size |
| c16_dormant_inference_ironwood | dormant_inference | 5/5 | 5/5 | 5/5 | 4/5 (false_create×1) | 3/5 (false_create×2) | 1/5 (false_create×4) | 1/5 (false_create×4) | passes small, fails large (overload?) |
| c17_dormant_name_match_harold | dormant_name_match | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | pass at every size |
| c18_dormant_inference_harold | dormant_inference | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | pass at every size |
| c19_dormant_name_match_marcus | dormant_name_match | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | pass at every size |
| c20_dormant_inference_marcus | dormant_inference | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | pass at every size |

## Misses

### c13_dormant_name_match_tidewater @ 1600 #1: `false_create`

- **Task:** ask Tidewater Dental to move the cleaning to 17:00
- **Gold:** `Dentist Cleaning Reschedule`
- **Chosen:** `Tidewater Dental 5pm Cleaning Request`
- **All delegations:** `Tidewater Dental 5pm Cleaning Request`
- **Instructions:**

> Theo Marchetti wants to ask his dentist, Tidewater Dental (frontdesk@tidewaterdental.ca), whether his cleaning can be moved to 5:00 PM instead. Find the most recent Tidewater Dental thread about his cleaning appointment (thread 1a0ee1f0348a9b4c is the earlier request to move the Oct 6 cleaning to a late-afternoon slot; check for any newer replies or the currently booked date). Draft a short reply in that thread asking if his cleaning can be moved to 5:00 PM instead, on the currently booked date, or the next available 5:00 PM if the date is unclear. Keep it brief and polite and sign off as Theo. Do NOT send. Return the draft details (to, subject, body, draft ID), and state the appointment date you based it on. If there is no reply from the clinic yet, mention that too.

### c13_dormant_name_match_tidewater @ 1600 #3: `false_create`

- **Task:** ask Tidewater Dental to move the cleaning to 17:00
- **Gold:** `Dentist Cleaning Reschedule`
- **Chosen:** `Tidewater Dental Cleaning 5pm Request`
- **All delegations:** `Tidewater Dental Cleaning 5pm Request`
- **Instructions:**

> Draft (do not send) a reply to Tidewater Dental (frontdesk@tidewaterdental.ca) on the existing thread 1a0ee1f0348a9b4c, asking whether Theo's cleaning can be moved to 5:00 PM instead. Check the thread first to confirm which appointment is pending (the earlier request was to move the Tuesday Oct 6 cleaning to a late-afternoon slot the following week) and whether they already replied. If the cleaning date is unclear, mention the date from the thread. Keep the email short, polite, and signed Theo. Return the draft's To, Subject, Body, and Draft ID, and note whether a reply already came in. Do not send.

### c14_dormant_inference_tidewater @ 200 #1: `false_create`

- **Task:** ask Tidewater Dental to move the cleaning to 17:00
- **Gold:** `Dentist Cleaning Reschedule`
- **Chosen:** `Tidewater Dental Reschedule`
- **All delegations:** `Tidewater Dental Reschedule`
- **Instructions:**

> Draft (do not send) a reply to Tidewater Dental (frontdesk@tidewaterdental.ca) on the existing cleaning reschedule thread (thread 1a0ee1f0348a9b4c, message 1a0ee1f0b18d6c2e). Ask whether Theo Marchetti can get a 5:00 PM slot instead of the currently requested late-afternoon time. Before drafting, check the thread for the most recent status: if a confirmed new time already exists or the appointment date has passed, report that instead of drafting. Keep the draft short and polite, signed Theo. Return the draft details (To, Subject, Body, Draft ID) and the appointment date it refers to.

### c14_dormant_inference_tidewater @ 200 #3: `false_create`

- **Task:** ask Tidewater Dental to move the cleaning to 17:00
- **Gold:** `Dentist Cleaning Reschedule`
- **Chosen:** `Tidewater Dental 5pm Request`
- **All delegations:** `Tidewater Dental 5pm Request`
- **Instructions:**

> Draft (do NOT send) a reply to frontdesk@tidewaterdental.ca on the existing thread 1a0ee1f0348a9b4c (earlier message 1a0ee1f0b18d6c2e), which requested moving Theo Marchetti's Tuesday Oct 6 cleaning to a late-afternoon slot the following week. Ask whether a 5:00 PM slot is available instead, in the same week as the earlier request. Keep it short and polite, signed Theo. Return the exact draft (to, subject, body, draft ID) for approval. Do not send anything.

### c14_dormant_inference_tidewater @ 400 #0: `false_create`

- **Task:** ask Tidewater Dental to move the cleaning to 17:00
- **Gold:** `Dentist Cleaning Reschedule`
- **Chosen:** `Tidewater Dental 5pm Request`
- **All delegations:** `Tidewater Dental 5pm Request`
- **Instructions:**

> Draft (do not send) a reply to Tidewater Dental (frontdesk@tidewaterdental.ca) in the existing cleaning reschedule thread (thread ID 1a0ee1f0348a9b4c, latest message 1a0ee1f0b18d6c2e). Ask whether Theo Marchetti can get a 5:00 PM slot instead of the currently requested late-afternoon time. Keep it short and polite, signed Theo. Return the exact recipient, subject, and body so I can show Theo for approval. Include the draft ID. If there is a more recent reply from Tidewater with available times, mention those too.

### c14_dormant_inference_tidewater @ 400 #1: `false_create`

- **Task:** ask Tidewater Dental to move the cleaning to 17:00
- **Gold:** `Dentist Cleaning Reschedule`
- **Chosen:** `Tidewater Dental 5pm Request`
- **All delegations:** `Tidewater Dental 5pm Request`
- **Instructions:**

> Draft a reply to Tidewater Dental (frontdesk@tidewaterdental.ca) in the existing thread 1a0ee1f0348a9b4c, replying to message 1a0ee1f0b18d6c2e. Ask whether Theo can get a 5:00 PM appointment instead of the late-afternoon slot previously requested for the cleaning. Keep it short and polite, signed Theo. Do NOT send. Create the draft only, then report back the exact recipient, subject, body, and draft ID.

### c14_dormant_inference_tidewater @ 400 #2: `false_create`

- **Task:** ask Tidewater Dental to move the cleaning to 17:00
- **Gold:** `Dentist Cleaning Reschedule`
- **Chosen:** `Tidewater Dental 5pm Request`
- **All delegations:** `Tidewater Dental 5pm Request`
- **Instructions:**

> Draft (do not send) a reply to Tidewater Dental (frontdesk@tidewaterdental.ca) on the existing cleaning reschedule thread (thread 1a0ee1f0348a9b4c, message 1a0ee1f0b18d6c2e). Ask if Theo Marchetti can get a 5:00 PM slot instead of the currently requested late-afternoon time for his cleaning. Keep it short and polite, signed Theo. Check the thread first for the exact appointment being discussed and reference it briefly. Return the full draft (to, subject, body, draft ID) and wait for Theo's explicit approval before sending anything.

### c14_dormant_inference_tidewater @ 400 #3: `false_create`

- **Task:** ask Tidewater Dental to move the cleaning to 17:00
- **Gold:** `Dentist Cleaning Reschedule`
- **Chosen:** `Tidewater Dental 5pm Request`
- **All delegations:** `Tidewater Dental 5pm Request`
- **Instructions:**

> Draft (do NOT send) a reply to Tidewater Dental (frontdesk@tidewaterdental.ca) on existing thread 1a0ee1f0348a9b4c, replying to message 1a0ee1f0b18d6c2e. Theo previously asked to move his cleaning to a late-afternoon slot the following week. He now wants to know if he can get a 5:00 PM slot instead. Keep the draft short and polite, signed Theo. Check the thread for the exact appointment being discussed and its current status, and include the date it refers to in the draft if it's clear. If the thread shows Tidewater already confirmed a time, report that instead of drafting. Report back the draft (to, subject, body, draft ID) and the appointment date/time it refers to, and flag anything that looks out of date (the original request referenced Tue Oct 6, which has passed).

### c14_dormant_inference_tidewater @ 800 #2: `false_create`

- **Task:** ask Tidewater Dental to move the cleaning to 17:00
- **Gold:** `Dentist Cleaning Reschedule`
- **Chosen:** `Tidewater Dental Reschedule`
- **All delegations:** `Tidewater Dental Reschedule`
- **Instructions:**

> Draft (do not send) a reply to Tidewater Dental (frontdesk@tidewaterdental.ca) in the existing thread 1a0ee1f0348a9b4c, which covers Theo Marchetti's cleaning reschedule request. Ask whether Theo can get a 5:00 PM slot instead of the previously requested late-afternoon time. Keep it short, polite, and signed Theo. Check the thread for the most recent details first (the original request was for the Tuesday cleaning moved to the following week, and the Oct 6 date has already passed, so confirm which appointment is being moved). Return the full draft (to, subject, body, draft ID) for Theo's review. Do not send anything.

### c14_dormant_inference_tidewater @ 1600 #0: `false_create`

- **Task:** ask Tidewater Dental to move the cleaning to 17:00
- **Gold:** `Dentist Cleaning Reschedule`
- **Chosen:** `Tidewater Dental 5pm Slot Request`
- **All delegations:** `Tidewater Dental 5pm Slot Request`
- **Instructions:**

> Draft (do NOT send) a reply in the existing Tidewater Dental thread (thread ID 1a0ee1f0348a9b4c, to frontdesk@tidewaterdental.ca) asking whether Theo can get a 5:00 PM slot instead of the currently requested late-afternoon time for his cleaning. Check the thread for the current appointment details and reference them briefly. Keep it short, polite, and in Theo's casual-direct tone, signed "Theo". Return the exact To, Subject, and Body, plus the draft ID, and wait for approval before sending anything.

### c14_dormant_inference_tidewater @ 1600 #2: `false_create`

- **Task:** ask Tidewater Dental to move the cleaning to 17:00
- **Gold:** `Dentist Cleaning Reschedule`
- **Chosen:** `Tidewater Dental 5pm Request`
- **All delegations:** `Tidewater Dental 5pm Request`
- **Instructions:**

> Draft (do NOT send) a reply in the existing Tidewater Dental thread (thread ID 1a0ee1f0348a9b4c, to frontdesk@tidewaterdental.ca) from Theo Marchetti. Ask whether a 5:00 PM appointment is available instead of the late-afternoon slot previously requested for the cleaning moved from Tuesday Oct 6. Keep it short, polite, and casual, signed Theo. Return the exact recipient, subject, body, and draft ID, and wait for explicit user confirmation before anything is sent.

### c14_dormant_inference_tidewater @ 1600 #3: `false_create`

- **Task:** ask Tidewater Dental to move the cleaning to 17:00
- **Gold:** `Dentist Cleaning Reschedule`
- **Chosen:** `Tidewater Dental 5pm Slot Request`
- **All delegations:** `Tidewater Dental 5pm Slot Request`
- **Instructions:**

> Draft (do not send) a reply to Tidewater Dental (frontdesk@tidewaterdental.ca) on the existing thread 1a0ee1f0348a9b4c, replying to message 1a0ee1f0b18d6c2e. Ask whether Theo Marchetti can get a 5:00 PM slot instead of the late-afternoon slot previously requested for the cleaning moved from Tuesday Oct 6 to the following week. Keep it short, polite, and signed Theo. Return the exact draft (to, subject, body, draft ID) for review. Do not send.

### c16_dormant_inference_ironwood @ 200 #3: `false_create`

- **Task:** ask Ironwood Athletic to extend the membership freeze through November
- **Gold:** `Gym Membership Freeze`
- **Chosen:** `Ironwood Membership Freeze`
- **All delegations:** `Ironwood Membership Freeze`
- **Instructions:**

> Draft (do NOT send) a reply to Ironwood Athletic (members@ironwoodathletic.ca) on the existing membership freeze thread (Message ID 1a05cbcdf88a9b95). Ask whether they can extend Theo Marchetti's membership hold through November 2026. Keep it short and polite. Mention that Theo's knee rehab is ongoing and that he's keen to keep his spot. Sign off as Theo. Ask them to confirm the extended hold dates and any fee. Return the exact To, Subject, and Body, plus the Draft ID, for Theo's review. Wait for explicit confirmation before sending anything.

### c16_dormant_inference_ironwood @ 400 #3: `false_create`

- **Task:** ask Ironwood Athletic to extend the membership freeze through November
- **Gold:** `Gym Membership Freeze`
- **Chosen:** `Ironwood Membership Freeze Extension`
- **All delegations:** `Ironwood Membership Freeze Extension`
- **Instructions:**

> Draft (do not send) a reply to Ironwood Athletic (members@ironwoodathletic.ca) on the existing membership freeze thread (the one for Theo's knee rehab, Message ID 1a05cbcdf88a9b95). Ask if they can extend Theo's membership hold/freeze through the end of November 2026. Keep it short and polite, signed Theo Marchetti. Also ask them to confirm the freeze dates and any fee for the extension if they haven't already. Create the draft only and return the exact To, Subject, and Body, plus the Draft ID. Do not send anything.

### c16_dormant_inference_ironwood @ 400 #4: `false_create`

- **Task:** ask Ironwood Athletic to extend the membership freeze through November
- **Gold:** `Gym Membership Freeze`
- **Chosen:** `Ironwood Membership Freeze Extension`
- **All delegations:** `Ironwood Membership Freeze Extension`
- **Instructions:**

> Draft (do NOT send) a reply on the existing Ironwood Athletic membership freeze thread (to members@ironwoodathletic.ca, related to Message ID 1a05cbcdf88a9b95). Ask Ironwood if Theo's membership hold can be extended through the end of November 2026, since the knee rehab is still ongoing. Keep it short and polite, sign off as Theo. Also ask them to confirm the freeze dates and any fee if they haven't yet. Return the exact draft (to, subject, body, draft ID) so Theo can review it before anything goes out.

### c16_dormant_inference_ironwood @ 800 #0: `false_create`

- **Task:** ask Ironwood Athletic to extend the membership freeze through November
- **Gold:** `Gym Membership Freeze`
- **Chosen:** `Ironwood Membership Freeze Hold Extension`
- **All delegations:** `Ironwood Membership Freeze Hold Extension`
- **Instructions:**

> Draft (do NOT send) a reply in the existing Ironwood Athletic membership freeze thread with members@ironwoodathletic.ca (the knee rehab freeze request, Message ID 1a05cbcdf88a9b95). Ask whether they can extend Theo's membership hold through the end of November 2026. Keep it short and polite, sign off as Theo. Also ask them to confirm any fee and the exact freeze dates if this changes anything. Return the exact To, Subject, Body, and Draft ID so the user can review. Wait for explicit confirmation before sending.

### c16_dormant_inference_ironwood @ 800 #1: `false_create`

- **Task:** ask Ironwood Athletic to extend the membership freeze through November
- **Gold:** `Gym Membership Freeze`
- **Chosen:** `Ironwood Athletic Membership Freeze`
- **All delegations:** `Ironwood Athletic Membership Freeze`
- **Instructions:**

> Draft a reply to members@ironwoodathletic.ca in the existing Ironwood Athletic membership freeze thread (the one from the knee rehab freeze request, Message ID 1a05cbcdf88a9b95). Ask if they can extend Theo's membership hold/freeze through the end of November. Keep it short, polite, and in Theo's voice. Sign off as Theo. Do NOT send it. Return the exact draft (to, subject, body, draft ID) for Theo's review. If you can't find the thread, say so and don't draft anything.

### c16_dormant_inference_ironwood @ 800 #2: `false_create`

- **Task:** ask Ironwood Athletic to extend the membership freeze through November
- **Gold:** `Gym Membership Freeze`
- **Chosen:** `Ironwood Membership Freeze Extension`
- **All delegations:** `Ironwood Membership Freeze Extension`
- **Instructions:**

> Draft (do not send yet) a reply to Ironwood Athletic (members@ironwoodathletic.ca) on the existing membership freeze thread (original request Message ID 1a05cbcdf88a9b95, sent by Theo Marchetti). Ask them to extend Theo's membership hold/freeze through the end of November 2026, since the knee rehab is ongoing. Keep it short and polite, sign as Theo. Also ask them to confirm the freeze dates and any fee for the extension. Return the exact draft (to, subject, body, draft ID) for Theo's review and wait for explicit approval before sending.

### c16_dormant_inference_ironwood @ 800 #3: `false_create`

- **Task:** ask Ironwood Athletic to extend the membership freeze through November
- **Gold:** `Gym Membership Freeze`
- **Chosen:** `Ironwood Membership Hold Extension`
- **All delegations:** `Ironwood Membership Hold Extension`
- **Instructions:**

> Draft (do NOT send) a reply to Ironwood Athletic (members@ironwoodathletic.ca) asking whether Theo Marchetti's membership freeze hold can be extended through November 2026. Reply in the existing Ironwood freeze thread (Message ID 1a05cbcdf88a9b95) if you can find it. Keep it short and polite. Mention that Theo is out for knee rehab and that Ironwood has already said they would hold the spot. Ask them to confirm the new end date and any fee. Sign off as Theo. Return the exact recipient, subject, body, and draft ID so the user can review it.

### c16_dormant_inference_ironwood @ 1600 #0: `false_create`

- **Task:** ask Ironwood Athletic to extend the membership freeze through November
- **Gold:** `Gym Membership Freeze`
- **Chosen:** `Ironwood Freeze Extension`
- **All delegations:** `Ironwood Freeze Extension`
- **Instructions:**

> Draft (do NOT send) a reply to Ironwood Athletic (members@ironwoodathletic.ca) about Theo Marchetti's membership freeze, which is for knee rehab. Find the existing freeze request thread (Message ID 1a05cbcdf88a9b95) and reply in that thread. Ask if they can extend Theo's freeze hold through the end of November 2026. Keep it short and polite. Mention that Theo is still waiting on the freeze dates and any fee, so please confirm both along with the extension. Sign off as Theo. Return the draft with recipient, subject, body, and draft ID for Theo's approval.

### c16_dormant_inference_ironwood @ 1600 #1: `false_create`

- **Task:** ask Ironwood Athletic to extend the membership freeze through November
- **Gold:** `Gym Membership Freeze`
- **Chosen:** `Ironwood Hold Extension`
- **All delegations:** `Ironwood Hold Extension`
- **Instructions:**

> Theo Marchetti wants to extend his Ironwood Athletic membership freeze hold through November. Find the existing thread with Ironwood Athletic (members@ironwoodathletic.ca) about the knee-rehab membership freeze (earlier request Message ID 1a05cbcdf88a9b95). Draft a reply in that thread asking Ironwood to extend Theo's freeze hold through the end of November 2026, and ask them to confirm the new end date and any fee. Keep it short and polite, signed Theo. Do NOT send it. Return the draft To, Subject, Body, and Draft ID for Theo's review.

### c16_dormant_inference_ironwood @ 1600 #3: `false_create`

- **Task:** ask Ironwood Athletic to extend the membership freeze through November
- **Gold:** `Gym Membership Freeze`
- **Chosen:** `Ironwood Membership Freeze Extension`
- **All delegations:** `Ironwood Membership Freeze Extension`
- **Instructions:**

> Create a draft email (do NOT send it) to members@ironwoodathletic.ca replying in the existing Ironwood membership freeze thread (Message ID 1a05cbcdf88a9b95), asking if Theo Marchetti's membership freeze can be extended through the end of November 2026. Keep it short and polite. Mention the freeze is for knee rehab, as in the original request. Ask them to confirm the new end date and whether there is any fee. Return the exact To, Subject, Body and Draft ID so the user can review it. Nothing should be sent until the user explicitly approves.

### c16_dormant_inference_ironwood @ 1600 #4: `false_create`

- **Task:** ask Ironwood Athletic to extend the membership freeze through November
- **Gold:** `Gym Membership Freeze`
- **Chosen:** `Ironwood Membership Freeze Extension`
- **All delegations:** `Ironwood Membership Freeze Extension`
- **Instructions:**

> Draft (do not send) a reply to Ironwood Athletic (members@ironwoodathletic.ca) on the existing membership freeze thread (original request Message ID 1a05cbcdf88a9b95). Ask if Theo's membership hold/freeze can be extended through the end of November 2026, for knee rehab. Keep it short and polite, signed Theo Marchetti. Also ask them to confirm the freeze dates and any fee for the extension, since those were still outstanding. Return the draft with recipient, subject, body, and draft ID. Wait for Theo's explicit approval before sending.
