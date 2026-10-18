# World bible: Theo Marchetti (routing-eval persona)

Reference only. The system under test never reads this file. Everything here is fictional:
people, companies and email domains are invented. Real cities and public places only appear as
locations.

## The user

- **Theo Marchetti**, 34, co-founder and head of product at **Northfold Studio**, a 12-person
  product design and engineering studio on Queen St E, Toronto.
- Email: `theo@northfoldstudio.ca`. This is a Google Workspace account and the one connected to OpenPoke.
  Theo uses it for both work and personal mail.
- Lives in Leslieville, Toronto, in a semi-detached house he owns with his fiancé **Jules Arden**.
  The mortgage is with Brightmoor Credit Union, and its term ends 2026-12-01.
- The wedding is **Saturday 2027-06-12** at Harrow Hill Estate (~110 guests).
- He plays Sunday rec-league soccer and hurt his left knee in August, so he's seeing a physio and his
  gym membership is frozen.
- His mom, Rosa, lives in Halifax and visited for Thanksgiving (Oct 9-13).
- Timezone: America/Toronto.
- Texting style: lowercase, terse, "u"/"pls"/"lol", rarely punctuates, sometimes sends a follow-up
  message a few seconds after the first one.

## Core counterparts and their single owner agent

Each counterpart below has one **core** owner. Real distractors (`REAL_DISTRACTORS` in `build_fixtures.py`) add `same_topic` siblings (different person, same kind of work) and a few `same_person` siblings, but only for counterparts whose case gold is fixed by a thread, draft or trigger. Counterparts whose gold rests on affinity alone keep exactly one owner.

| # | Counterpart | Email | Org | Owner agent (core) | Status at "now" |
|---|-------------|-------|-----|--------------------|-----------------|
| 1 | Celeste Moreau, events coordinator | celeste@harrowhillestate.ca (+ events@harrowhillestate.ca) | Harrow Hill Estate (wedding venue) | Harrow Hill Venue Deposit | $4,000 second deposit e-transferred and emailed 2026-10-15; no confirmation yet |
| 2 | Priya Natarajan, engineering lead | priya@northfoldstudio.ca | Northfold Studio | Priya Roadmap Sync | Q4 roadmap doc promised for Mon 2026-10-19 EOD |
| 3 | Dmitri Volkov, owner | dmitri@ironbarkreno.ca | Ironbark Renovations | Kitchen Reno Quote Follow-up | $36,800 kitchen reno, start 2026-11-09, cabinet order asked 2026-10-16 |
| 4 | (inbox items, e.g. Bramblewood Auto Service, service@bramblewoodauto.ca) | n/a | n/a | Inbox Catch-Up Scan | Found the winter-tire booking email on 2026-10-17 (slots Sat Oct 24 9:00 / Tue Oct 27 16:30) |
| 5 | Hana Ishikawa, account manager | hana.ishikawa@copperleafdata.com | Copperleaf Data (analytics vendor) | Copperleaf Renewal Thread | Reply drafted 2026-10-19 evening, **pending user confirmation** |
| 6 | Weekly inbox rundown (standing routine) | n/a | n/a | Sunday Week Ahead Brief | Trigger: Sundays 19:00, created 2026-08-05 |
| 7 | Wendell Achebe, mortgage advisor | wendell.achebe@brightmoorcu.ca | Brightmoor Credit Union | Mortgage Renewal Paperwork | Docs sent 2026-09-10; renewal offer by 2026-10-30; rate decision before 2026-11-04. **Dormant since 2026-09-10** |
| 8 | Priya Sandhu, photographer | priya@lumenandlinen.ca | Lumen & Linen Photography | Engagement Shoot Booking | Shoot done 2026-10-10; proofs promised by 2026-10-23 |
| 9 | Marco Bellandi, league organizer | marco@riverdalerecsoccer.ca | Riverdale Rec Soccer League | Email to Marco Soccer League | Theo pulled out for the rest of the season 2026-10-13 (knee) |
| 10 | Gabe Lindqvist, co-founder/CEO | gabe@northfoldstudio.ca | Northfold Studio | Email to Gabe Offsite Agenda | Team offsite Wed-Thu 2026-10-21/22 at Cedar Hollow Lodge; final agenda sent 2026-10-15 |
| 11 | Marcus Oyelaran, recruiter | marcus@fernwaytalent.com | Fernway Talent | Fernway Designer Search | Senior designer search, portfolios received |
| 12 | Lakeport Hydro (electric utility) | billing@lakeporthydro.ca | Lakeport Hydro | Hydro Bill Reminder | Trigger: monthly on the 20th at 09:00 |
| 13 | Tidewater Dental front desk | frontdesk@tidewaterdental.ca | Tidewater Dental | Dentist Cleaning Reschedule | Cleaning moved to 2026-10-15 16:30 |
| 14 | Rosa Marchetti (mom) | rosa.marchetti@quaymail.net | n/a | Mom Thanksgiving Visit | Visit Oct 9-13 done; one-off pickup reminder trigger (fired) |
| 15 | Tomasz Wierzbicki, book club organizer | tomasz.wierzbicki@quaymail.net | n/a | Email to Tomasz Book Club | Theo hosted 2026-09-17 |
| 16 | Adaeze Nwosu, program chair | cfp@prairieuxconf.org | Prairie UX Conference | Prairie UX Talk Proposal | Talk accepted, Winnipeg 2026-11-19 |
| 17 | Osteria Valdina (restaurant) | reservations@osteriavaldina.ca | Osteria Valdina | Jules Birthday Dinner | Table for 2, Sat 2026-11-14 19:30 |
| 18 | Oakhurst Furniture (orders) | orders@oakhurstfurniture.ca | Oakhurst Furniture | Standing Desk Receipt Lookup | Receipt forwarded to expenses 2026-08-03 |
| 19 | Dr. Leena Haddad, physiotherapist | leena@corktownphysio.ca | Corktown Physio | Physio Knee Appointment | Assessment was 2026-08-25 |
| 20 | Hôtel Verrière (Montréal) | reservations@hotelverriere.ca | Hôtel Verrière | Montreal Weekend Hotel | King room booked Nov 6-8, $289/night |
| 21 | Elaine Fairbanks, fractional CFO | elaine@ledgerlinepartners.ca | Ledgerline Partners | Q3 Financials Elaine | Q3 package promised by 2026-10-16 |
| 22 | Noor Hassan, stationer | noor@inkwellandvine.ca | Inkwell & Vine Stationery | Save the Date Printing | Quote $780 for 120 letterpress save-the-dates |
| 23 | Ironwood Athletic Club (memberships) | members@ironwoodathletic.ca | Ironwood Athletic Club | Gym Membership Freeze | Frozen Sep 1 - Oct 31 |
| 24 | Harold Pemberton (neighbour) | harold.pemberton@quaymail.net | n/a | Neighbour Fence Repair | Agreed to split fence repair |
| 25 | Sofia Brandt (friend, cottage) | sofia.brandt@quaymail.net | n/a | Email to Sofia Cottage Weekend | Cottage weekend Aug 7-9 done |

`quaymail.net` is a fictional consumer mail provider, like gmail. Distractor people may also use it.
Only the specific core addresses are reserved.

### Counterparts used only by cases (no owner anywhere in the roster)
- **Marco Ferrante**, piano teacher, Keyhaven Music, `marco@keyhavenmusic.ca` (case 9, NEW).
- **Halcyon Chimney Co.**, `service@halcyonchimney.ca` (case 10, NEW).
- **Bramblewood Auto Service**, `service@bramblewoodauto.ca`. It's known only through the email the
  "Inbox Catch-Up Scan" agent found, so that agent owns the thread (case 4).

## Hard-negative design

- **Same first name, different person:** Priya Natarajan (`priya@northfoldstudio.ca`, Northfold engineering lead,
  owner "Priya Roadmap Sync") vs Priya Sandhu (`priya@lumenandlinen.ca`, Lumen & Linen
  Photography, owner "Engagement Shoot Booking", whose name doesn't say Priya). Both addresses start
  with `priya@`. Only the domain or org tells them apart.
- **Similar wording:**
  - Marco Bellandi (soccer), Marco Ferrante (piano, new), and Marcus Oyelaran (Fernway recruiter).
  - Ironbark Renovations vs Ironwood Athletic Club.
  - Copperleaf Data vs the distractor "Copper Kettle Catering Quote".
  - Harrow Hill vs the distractor "Hillcrest Cabin Booking".
- **Shared topic words across different counterparts:**
  - "Renewal": Copperleaf Renewal Thread, Mortgage Renewal Paperwork, distractor "Passport Renewal Appointment".
  - "Deposit": Harrow Hill Venue Deposit, distractor "Security Deposit Refund".
  - "Inbox": Inbox Catch-Up Scan, distractors "Inbox Summary", "Unread Email Check".
  - "Reminder": Hydro Bill Reminder, and many distractor reminders with triggers.
  - "Email to …": many distractors.

## Timeline (America/Toronto)

- 2026-07-20 Mon: first chat with Poke.
- 07-21: Harrow Hill availability inquiry sent.
- 07-24: Hydro bill reminder trigger (monthly, 20th 09:00).
- 07-27: inquiry to Priya Sandhu about engagement shoot packages.
- 07-29: Sofia cottage-weekend email. 08-04: her reply (bring paddles, Aug 7-9).
- 07-31: Priya Natarajan asked to set up Q4 roadmap review. 08-14: she replies (review Aug 25).
- 08-03: standing desk receipt found and forwarded to expenses.
- 08-05: Sunday Week Ahead Brief trigger created (Sundays 19:00, first fire Aug 9).
- 08-06: quote request to Dmitri (Ironbark). 08-27: quote $38,500, counter at $36,000.
  09-09: he agrees to $36,800, start Nov 9.
- 08-11: signed up for Riverdale Rec fall league (Marco).
- 08-12: engagement shoot booked for Sat 2026-10-10, golden hour, Humber Bay Park.
- 08-13: Fernway recruiter (Marcus) call set up. 09-02: three portfolios found.
- 08-18 / 08-21: physio booked (Aug 25, 08:00, Dr. Haddad).
- 08-19: Harrow Hill: June 12 2027 chosen, deposit schedule asked.
- 08-25: mortgage renewal started with Wendell. 09-03: his doc list arrives. 09-10: pay stub and
  property tax bill forwarded to him. He'll send the renewal offer by Oct 30, and the rate decision
  is due before the Nov 4 rate announcement.
- 08-26: Theo offers to host book club on Sep 17 (Tomasz). 09-17: 7 people coming.
- 09-01: gym freeze request (Ironwood). Frozen Sep 1 to Oct 31.
- 09-08 / 09-15 / 10-02: Prairie UX CFP found, proposal sent, talk accepted (Nov 19, Winnipeg).
- 09-14 / 09-16: Mom's flight time (Oct 9, lands 15:40). 10-09: one-off pickup reminder fires.
- 09-15: Copperleaf renewal notice (+12%, $18,400 → $20,608/yr, renews Nov 30).
  10-01: usage report requested.
- 09-22 / 10-08: Elaine asked for Q3 close, promised by Oct 16.
- 09-24 / 10-06: save-the-date quote request and quote (Inkwell & Vine).
- 09-25 / 09-29: Montréal hotel inquiry and booking (Nov 6-8).
- 09-28: Gabe asks for the offsite agenda. Draft sent.
- 09-29 / 10-02: dentist cleaning moved to Oct 15 16:30.
- 09-30 / 10-03: fence repair split with Harold.
- 10-05 / 10-07: Osteria Valdina booking for Jules' birthday (Nov 14 19:30).
- 10-10: engagement shoot happens. 10-12: Thanksgiving. 10-13: Theo tells Marco he's out for the season.
- **Recent window (working memory, entries 300-379), 10-14 → 10-19:**
  - Priya roadmap nudge (10-14) and her reply (10-16).
  - Harrow Hill second deposit note (10-15).
  - Engagement proofs ETA from Priya Sandhu (10-15).
  - Final offsite agenda to Gabe (10-15).
  - Cabinet-order question to Dmitri (10-16).
  - Inbox catch-up finds the Bramblewood tire email (10-17).
  - Sunday brief fires (10-18).
  - Copperleaf reply drafted and pending (10-19 ~19:40).
- "Now" = Mon 2026-10-19, ~19:45. Every case message arrives right after the pending Copperleaf draft.
