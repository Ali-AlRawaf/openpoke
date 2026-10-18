# Routing eval: shared spec

The eval measures **one decision**: given the current state, which execution agent the Interaction Agent sends a new user message to (an existing roster name, or a new agent). The goal is to reproduce **agent overload**, meaning routing gets worse as the roster grows.

Scope: **10 cases × roster sizes 25/50/100/200/400 × 1 run.** Model: whatever `server/config.py` sets (Claude Haiku 5.5 through OpenRouter).

Ground rules for everyone:
- **Never read or write `server/data/`**, except to look at it for format reference.
- **Don't modify `server/` code.**
- **Don't commit.**
- Use `/home/ali/openpoke/.venv/bin/python`, and run modules from the repo root (`python -m evals.routing.<module>`).
- The OpenRouter key comes from `.env` through `server.config.get_settings()`.
- The server's data directory is set with `OPENPOKE_DATA_DIR`. It must be set **before** anything under `server` is imported.

---

## 1. Directory layout

```
evals/routing/
  SPEC.md              # this file
  logfmt.py            # format_line / parse_line / agent_log_filename (server-exact). USE IT; don't re-implement
  build_fixtures.py    # (fixture designer) writes core state from structured Python data
  generate.py          # (fixture designer) one-off LLM generation: distractor agents + older conversation
  run.py               # (harness engineer) CLI: validate / dry-run / run
  score.py             # (harness engineer) JSONL -> report.md + report.json
  fixtures/
    world.md           # persona + people/orgs/projects bible (reference only, never loaded by the system)
    cases.json         # gold labels (never copied into the data dir)
    rosters/roster_25.json ... roster_400.json
    state/             # copied verbatim into OPENPOKE_DATA_DIR for a run
      timezone.txt                              # "America/Toronto"
      conversation/poke_conversation.log
      conversation/poke_working_memory.log
      execution_agents/<slug>.log               # one per agent in roster_400 (no roster.json here)
  results/<run_id>/    # run output (decisions.jsonl, report.md, report.json)
```

Not part of the fixtures: `gmail-execution-agent.log`, `task-email-search.log` (task memories), `triggers.db`, `gmail_seen.json`. The Interaction Agent never reads them.

---

## 2. File formats (must match `server/data` exactly)

Every `.log` line is `<tag timestamp="YYYY-MM-DD HH:MM:SS">PAYLOAD</tag>`, one entry per line:
- Timestamps are in the user's timezone (America/Toronto).
- PAYLOAD is HTML-escaped (`<` → `&lt;`, `>` → `&gt;`, `&` → `&amp;`; quotes are NOT escaped).
- Real newlines are written as the two characters `\n`.

**Always write lines with `logfmt.format_line(tag, payload, timestamp)`.** It reuses the server encoder. A malformed line isn't an error in production: the server **silently drops** it.

### 2.1 Execution agent log: `execution_agents/<slug>.log`
- **File name:** `logfmt.agent_log_filename(name)` (lowercase, non-alphanumerics → `-`). Two names that produce the same slug collide, which is not allowed.
- **Tags, in the order the runtime writes them, per request:**
  1. `agent_request`: the Interaction Agent's instructions to the agent (written when dispatched)
  2. **For each tool call:** `agent_action` with `Calling <tool_name> with: <json args, cut to 200 chars>`, then `tool_response` with `<tool_name>: <json result, cut to 500 chars>`
     - Trigger tools also write their own action **before** the `Calling …` line: `createTrigger succeeded | trigger_id=<int>`, `updateTrigger succeeded | trigger_id=<int>`, `listTriggers succeeded | count=<int>`
  3. `agent_response`: the agent's final report to the Interaction Agent
- **Tool names:** `gmail_create_draft`, `gmail_execute_draft`, `gmail_forward_email`, `gmail_reply_to_thread`, `gmail_delete_draft`, `gmail_get_contacts`, `gmail_get_people`, `gmail_list_drafts`, `gmail_search_people`, `task_email_search`, `createTrigger`, `updateTrigger`, `listTriggers`.

Real example (from `server/data/execution_agents/email-to-ali-japan-itinerary.log`):
```
<agent_request timestamp="2026-10-17 14:19:48">Create a draft email (do not send it yet) to alrawafali@gmail.com inviting Ali to lunch tomorrow (Sunday, October 18, 2026) at 1:00 PM at Chipotle. Mention that Alice is coming too. Keep the tone friendly and casual, and short. Reply with the exact draft (to, subject, body) so the user can review it before anything is sent.</agent_request>
<agent_action timestamp="2026-10-17 14:07:46">Calling gmail_create_draft with: {"recipient_email": "alrawafali@gmail.com", "subject": "Itinerary for Japan trip", "body": "Hey Ali,\n\nCould you send over the itinerary for our Japan trip next week?\n\nThanks!", "is_html": false}</agent_action>
<tool_response timestamp="2026-10-17 14:07:46">gmail_create_draft: {"error": "Gmail not connected. Please connect Gmail in settings first."}</tool_response>
<agent_response timestamp="2026-10-17 14:07:48">The email has not been sent. I created the draft, but ...</agent_response>
```
Successful Gmail results contain ids, e.g. `gmail_create_draft: {"successful": true, "data": {"id": "r5255513545109994129", "message": {"threadId": "1a14b17727a956b7", ...}}}`. `task_email_search` results are a JSON list of emails with `id`, `thread_id`, `subject`, `sender`, `recipient`, `timestamp`, `clean_text`.

### 2.2 Conversation log: `conversation/poke_conversation.log`
- Append-only. Tags are `user_message`, `poke_reply`, `agent_message`, `wait`.
- `agent_message` payload: `[SUCCESS] <Agent Name>: <agent_response text>` (or `[FAILED] …`). The batch manager writes one line per agent; several results in one batch are joined with real newlines.
- Drafts shown to the user are a `poke_reply` with payload `To: …\nSubject: …\n\n<body>`, usually followed by a second `poke_reply` asking to confirm.
- `wait` payload: the reason (orchestration noise; the UI hides it).

Real example:
```
<user_message timestamp="2026-10-17 14:19:26">can you email ali and invite him to lunch tomorrow? alice is coming too.</user_message>
<poke_reply timestamp="2026-10-17 14:19:48">Got it. I'll draft the lunch invite to alrawafali@gmail.com for tomorrow at 1pm at Chipotle, with Alice coming too.</poke_reply>
<wait timestamp="2026-10-17 14:19:49">Waiting for the lunch invite draft from the execution agent before showing the user anything.</wait>
<agent_message timestamp="2026-10-17 14:19:52">[SUCCESS] Email to Ali Japan Itinerary: Draft created. It has not been sent.\n\n- **To:** alrawafali@gmail.com\n...</agent_message>
```

### 2.3 Working memory: `conversation/poke_working_memory.log`
**This is the only conversation state the Interaction Agent reads.**
```
<summary_info>{"last_index": 299, "updated_at": "2026-10-17T02:11:09.512331+00:00"}</summary_info>
<conversation_summary>Summary generated: ...</conversation_summary>
<user_message timestamp="...">...</user_message>      # the unsummarized entries, identical to the
...                                                    # LAST 80 lines of poke_conversation.log
```
- `summary_info` and `conversation_summary` have **no timestamp attribute**.
- **Consistency rule:** the conversation log has 380 entries (indices 0–379). `last_index = 299`. The working memory holds the summary plus entries 300–379, byte-identical to the conversation log.
- That's the state the real summarizer leaves: it fires when 110 or more entries are unsummarized, and summarizes the first 100 each time.

### 2.4 Rosters: `fixtures/rosters/roster_N.json`
- A JSON list of agent names in **creation order** (the roster only appends), indented by 2 like the server writes it.
- **Nested:** `roster_25 ⊂ roster_50 ⊂ … ⊂ roster_400`.
- **`roster_25` = all core agents.** Each larger roster adds the next distractors. Merge by `created_at` so the core agents sit at their natural positions (early, middle and late), not all at the top.
- Every name has exactly one log in `state/execution_agents/`.

---

## 3. Labelling policy (the definition of "correct")

The source is `server/agents/interaction_agent/system_prompt.md:19`:
> "always prefer to send messages to a relevant existing agent rather than starting a new one UNLESS the tasks can be accomplished in parallel. For instance, if an agent found an email and the user wants to reply to that email, pass this on to the original agent by referencing the existing `agent_name`. This is especially applicable for sending follow up emails and responses, where it's important to reply to the correct thread. Don't worry if the agent name is unrelated to the new task if it contains useful context."

**How the system applies it in practice: affinity.**
- In a live session, an agent named "Email to Ali Japan Itinerary" was **reused** for a brand-new lunch invite to the same person, Ali, on a new thread with no shared context needed.
- It was then reused again for "did ali respond?" across both threads.
- So an agent becomes the **owner of a counterpart**: a person, an organization, or a standing topic or project.

**Rule, in order of precedence:**
1. **Thread, draft or trigger owner.** If the message refers to specific work an agent did (a thread it found or sent, a draft it made, a trigger it created), route to that agent.
2. **Counterpart owner (affinity).** Otherwise, if an agent already handles the same counterpart (the same person, organization or standing project), route to it even for a new task on a new thread.
3. **`NEW`.** No agent owns the thread or the counterpart, **or** the message contains a separate task that can run in parallel (that task gets its own agent).

**Exactly one correct answer for each expected delegation:** an exact existing roster name, or `NEW` (any name not in the roster). A two-task message has two expected delegations.

**Case design rules (these are what make a single answer possible):**
- **Noise distractors** never concern a core counterpart (name, email address or organization).
- **Real distractors** (`REAL_DISTRACTORS` in `build_fixtures.py`) model the hybrid reuse/create behaviour and replace noise one for one, so roster sizes stay fixed. There are two kinds:
  - `same_topic`: a different person or vendor on the same kind of work. Common.
  - `same_person`: the same counterpart on a different topic. Rare, and **only** for counterparts whose case gold is fixed by a specific thread, draft or trigger (rule 1) or that no case uses.
- **Counterparts whose gold rests on affinity alone (rule 2) keep exactly one owner**, so every case keeps a single correct answer.
- **Hard negatives look related but belong to a different counterpart:**
  - the **same first name on a different person**, told apart by email address and organization
  - similar wording ("Email to Alina", "AliExpress Order Tracking")
  - the same topic word on another counterpart's agent
- **No case may set person affinity against topic affinity.** If two agents could both reasonably claim the message, the case is invalid.
- **The gold answer must be derivable from production-visible state:** the summary, the 80 recent entries, the agent logs, and the roster names. Never from `world.md` or `cases.json`.

---

## 4. `cases.json` schema

```json
{
  "version": 1,
  "cases": [
    {
      "id": "c02_new_task_known_counterpart",
      "category": "new_task_known_counterpart",
      "rule": 2,
      "message": "can you email priya and ask if she's free for a call thursday?",
      "expected": [
        {"task": "ask Priya about Thursday call", "gold": "Priya Venue Contract"}
      ],
      "rationale": "Priya Shah <priya@...> is owned by 'Priya Venue Contract' (see priya-venue-contract.log, 2026-09-14 request). Hard negative 'Email to Priya Patel' is a different Priya (...)."
    }
  ]
}
```
- `gold` is an exact roster name, or the literal string `"NEW"`.
- Every non-`NEW` gold name must be in `roster_25`, and therefore in every size.
- `message` is the user's raw text, written in the persona's casual texting style.

**The 10 case types (one each):**
1. A follow-up where the counterpart **is** in the owner's name (easy control)
2. A new task for a known counterpart on a new thread (rule 2)
3. A new task for a counterpart whose owner's name **doesn't** mention them (rule 2)
4. A reply to an email that an agent with an unrelated name found (rule 1)
5. "ok send it" / "yep go ahead", tied to a draft pending in the recent 80 entries (rule 1)
6. Change a reminder ("push my nightly digest to 10pm"). The gold answer is the agent whose log contains `createTrigger succeeded` (rule 1)
7. Revive a dormant counterpart that appears **only in the summary**, not in the recent 80 (rule 2)
8. Same first name, different person: the message clearly means the *other* person, who has an owner (rules 1–2)
9. A genuinely new counterpart whose name overlaps existing names. Gold: `NEW` (rule 3)
10. Two parallel tasks in one message: one for a known counterpart (reuse) and one for a new counterpart (`NEW`)

---

## 5. Harness contract (summary; the engineer brief has details)

- **Per size N:**
  - fresh temp `OPENPOKE_DATA_DIR`
  - copy `state/` verbatim
  - write `rosters/roster_N.json` as `execution_agents/roster.json`
  - delete agent logs not in `roster_N`
- **Per case:**
  - Build the prompt with `build_system_prompt()` and `prepare_message_with_history(message, get_working_memory_log().render_transcript())`.
  - Loop with `InteractionAgentRuntime._make_llm_call`, intercepting `send_message_to_agent`, `send_message_to_user`, `send_draft` and `wait`.
  - Stop after the first response containing `send_message_to_agent`, or after 3 iterations.
- **Classification:** a delegated name that **exactly** equals a roster name is a reuse; anything else is a create (`NEW`).
- **Outcome for each expected delegation:** `correct`, `wrong_reuse`, `false_create`, `false_reuse`, or `missed`. Extra unexpected delegations are recorded separately.
