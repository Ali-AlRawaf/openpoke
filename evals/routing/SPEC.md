# Routing eval

The eval measures **one decision**: given the current state, which execution agent the Interaction Agent (IA) sends a new user message to: an existing agent, or a new one. Model: whatever `server/config.py` sets (Claude Haiku 5.5 through OpenRouter).

Section 0 is the story: what goes wrong, how the eval shows it, how the solution fixes it, and what the cases do and don't cover. Sections 1–6 are the reference (formats, labelling policy, harness, commands).

Ground rules:
- **Never read or write `server/data/`** from eval code; runs use a temp `OPENPOKE_DATA_DIR`, set **before** anything under `server` is imported.
- Use `/home/ali/openpoke/.venv/bin/python` and run modules from the repo root (`python -m evals.routing.<module>`). The OpenRouter key comes from `.env` through `server.config.get_settings()`.

---

## 0. The story

### 0.1 The problem: agent overload
Every task the IA delegates goes to a named execution agent, and the IA prefers to **reuse** the agent that already handles a counterpart (a person, an organization, a standing project) rather than start a new one (§3). In the original system the IA chose from a flat list of agent **names**, injected into every prompt. As the roster grows, routing gets worse.

The baseline (`results/baseline_all_x10`: names-only system, 20 cases × 7 roster sizes × 10 repeats) shows exactly how:
- **It fails by fragmentation.** Every one of the 169 failures is a `false_create`: the IA starts a duplicate agent instead of finding the owner. It never reuses the wrong agent.
- **It fails on the link, not on the size alone.** The decline is concentrated in **dormant counterparts referenced by a name that isn't in the owner's agent name**: "ask **ironwood** if they can extend my hold", whose owner is "Gym Membership Freeze". The only link is the conversation summary ("Ironwood Athletic membership freeze, knee rehab"). The matched controls, the same owners referenced by words in their names ("extend my **gym membership freeze**"), stay flat. So the IA isn't getting generally worse; it loses the ability to connect a counterpart to an agent whose name doesn't mention it, once that agent is one name among hundreds.

| Baseline pass rate | 25 | 50 | 100 | 200 | 400 | 800 | 1600 |
|---|---|---|---|---|---|---|---|
| **Overload target** (dormant, inference) | 98% | 98% | 93% | 87% | 77% | 67% | **62%** |
| Dormant control (name match) | 100% | 100% | 100% | 100% | 92% | 100% | 88% |
| Easy recent | 97% | 100% | 100% | 100% | 98% | 100% | 98% |

### 0.2 The solution: agent cards + agent search
1. **Agent cards** replace names (`server/services/execution/roster.py`). Each agent carries a `summary` (what it's for, what it has done, any thread or draft it owns) and `artifacts`: the people, organizations, email addresses, events, places and topics its work involves, *as someone would mention them later*. Artifacts are **affinity**; the summary is **ownership**. Neither holds system IDs.
2. **Cards stay current.** The IA writes the first card with `create_agent`; after every finished task the **card updater** (`card_updater.py`, one Haiku call with structured output) rewrites it from the task's log.
3. **The roster leaves the prompt.** The IA calls `search_agents(query)`: up to 10 agents it gets the whole roster; above 10, the query is embedded and the 10 most similar cards come back (`agent_search.py`: one vector for "name: summary" plus one per artifact, an agent scores its best vector). The IA writes the query from the message **and the conversation**, so "ask wendell…" becomes "Brightmoor mortgage renewal Wendell Achebe rate lock".
4. **Creating is explicit.** `create_agent` is a separate tool and `send_message_to_agent` rejects unknown names, so a misspelled or invented name can no longer silently start a duplicate. The prompt defines **relevance**: an agent is relevant only if the task continues its work or involves the same specific things on its card; being *able* to do the task never makes an agent relevant.

**Why this fixes the overload failure.** The link the IA lost lived only in the summary ("Ironwood → gym freeze"). Now the IA turns that link into a query, and the owner's card carries the counterpart ("Ironwood Athletic <members@…>"), so search returns the owner at the top whatever the roster size. The IA chooses among ~10 cards, the size at which it never failed.

### 0.3 Results (`results/final_all_x10`: 31 cases × 7 sizes × 10 repeats, 2,170 decisions)
| Pass rate (baseline → solution) | 25 | 400 | 800 | 1600 |
|---|---|---|---|---|
| **Original 20 cases (accuracy)** | 95% → 100% | 83% → 100% | 86% → 100% | 78% → 100% |
| **Overload target** | 98% → 100% | 77% → 100% | 67% → 100% | **62% → 100%** |
| Dormant control | 100% → 100% | 92% → 100% | 100% → 100% | 88% → 100% |
| Stress: paraphrase (no name) | → 100% | → 100% | → 100% | → 100% |
| Stress: typo | → 100% | → 100% | → 100% | → 100% |
| Stress: new counterpart, familiar topic | → 100%* | → 100%* | → 100%* | → 100%* |

- **0 wrong reuses, 0 false reuses, 0 false creates** in 2,170 decisions. The only misses (65, all `missed`) were c27, a **case bug**: its "this thursday" fell on the Cedar Hollow offsite day, and the IA rightly asked which Thursday instead of booking. *With the date made explicit, c27 passed 70/70 (`results/final_c27_fixed_x10`); the run itself is kept as recorded.
- **Retrieval** (`results/recall_final_all_x10`): for all 1,544 searches the IA made, the gold agent was in the top 10 at every size (worst rank 4 at 1,600, production `max` scoring; `top2 mean` would have ranked it at most 2nd).
- **Cost of the design:** ~1.8 LLM calls per decision (a search, then the delegation) instead of 1; ~4.2s instead of ~3.0s at 25 agents; about $0.0011 per decision, roughly flat across roster sizes, where the baseline paid for every name on every call.
- Earlier runs: `results/solution_all_x10` (the original 20 cases, same result), `results/gate_new_cases_x10` (c09/c10 with a search-before-create gate, since removed for latency).

### 0.4 Case groups: what each tests
Groups are defined in `score.py` (`GROUPS`) and reported as pass rates per size.

| Group | Cases | What it tests | Why it matters |
|---|---|---|---|
| **Overload target** | c07, c12, c14, c16, c18, c20 | A dormant counterpart (only in the summary) referenced by a name that **isn't** in its owner's agent name ("ask ironwood…" → "Gym Membership Freeze") | The failure itself: the baseline falls from 98% to 62% |
| **Dormant control** | c11, c13, c15, c17, c19 | The **same owners**, referenced by words in their agent names ("my gym membership freeze") | Paired with the targets (c11/c12 … c19/c20): proves the baseline decline is the missing link, not dormancy or roster size |
| **Easy recent** | c01, c03, c05, c06, c08, c09 | Follow-ups to agents in the recent conversation: a named counterpart, a pending draft ("yep send it"), a trigger change, the same first name on a different person, a new counterpart with an overlapping name | Regression guard: the new flow must not break the everyday cases |
| **Policy-ambiguous** | c02, c04 | Where the reuse policy is hardest to apply (a new task for a known counterpart; replying to an email an unrelated-sounding agent found) | Shows whether the policy, not just retrieval, is followed |
| **Multi-task** | c10 | One message, two tasks: one for a known agent, one needing a new agent | Parallel routing; both halves must be right |
| **Stress: paraphrase** | c21–c24 | A dormant owner referred to by description only, no name ("our guy at the credit union", "the guy next door", "my teeth appointment") | Search can't match a name; the IA must rebuild the identity from the summary |
| **Stress: new, familiar topic** | c25–c27 | A **new** counterpart on a topic existing agents already cover (a different dentist, a mechanic other than "the tire place", a lunch with a new client), no name or email given | The solution's new risk is false reuse of a similar agent (the "Starbucks agent used for Mary" bug); these must create |
| **Stress: typo** | c28–c31 | The overload targets with the name misspelled ("wendel", "tidwater", "ironwod", "harrold") | Embedding search and the IA must tolerate misspelled names |

The stress groups (split `stress`) were written **after** the solution was built, to probe it where it is likely weakest. They pass end to end at every size (§0.3); the one failure found was a case bug (c27's date clashed with the persona's calendar), fixed and rerun.

### 0.5 Coverage and limits
What the evidence supports: on the reproduced overload failure, routing no longer degrades with roster size, without regressions or new error types.

What it does **not** cover:
- **One world.** One persona, one conversation, 31 cases. Repeats measure model variance, not variety of requests.
- **Saturation.** Every group, stress groups included, is at 100%: the suite shows the failure is fixed and the obvious weak spots hold, but not where the design breaks. Finding that needs harder cases (vaguer paraphrases, several plausible owners, longer multi-step requests).
- **Clean cards.** Fixture cards come from complete synthetic task histories; real early cards are thinner (one create, one update) and see tool arguments cut to 200 chars.
- **Excluded by design:** near-duplicate agents left over from the old fragmentation, and two agents for the same counterpart in an affinity case (the policy can't pick one).
- **Routing only.** The harness stops once routing is done; execution, card updates and later turns are not exercised.
- **Authorship.** The cases, labels and the solution's prompt were written by the same author; held-out (`split: heldout`, c11–c20) and stress cases informed or followed the design.

**Keeping this section current:** when adding cases, add them to a group in `score.py` `GROUPS` and to the table in §0.4; when a run changes the picture, update §0.3 with the run directory.

---

## 1. Directory layout

```
evals/routing/
  SPEC.md              # this file
  logfmt.py            # format_line / parse_line / agent_log_filename (server-exact). USE IT; don't re-implement
  build_fixtures.py    # writes state/, rosters/ (agent cards), cases.json from Python data + frozen generated/ JSON
  generate.py          # one-off LLM generation (stages: names, names_more, filler, summary, logs, cards, embeddings)
  run.py               # CLI: validate / dry-run / run (the IA loop, side-effecting tools stubbed)
  score.py             # JSONL -> report.md + report.json (outcomes, agent-search metrics, before/after)
  recall.py            # offline: does agent search return each case's gold? (no IA calls)
  fixtures/
    world.md           # persona + people/orgs/projects bible (reference only, never loaded by the system)
    cases.json         # gold labels (never copied into the data dir)
    rosters/roster_25.json ... roster_1600.json   # agent cards, exactly like server roster.json
    generated/         # frozen LLM output: distractor_names, distractors (task logs), cards, summary, filler, cost
    embeddings/agent_embeddings.npz              # gitignored; `generate embeddings` (~$0.01)
    state/             # copied verbatim into OPENPOKE_DATA_DIR for a run
      timezone.txt                              # "America/Toronto"
      conversation/poke_conversation.log
      conversation/poke_working_memory.log
      execution_agents/                         # empty: no logs, no roster.json (the harness installs those)
  results/<run_id>/    # run output (decisions.jsonl, run_meta.json, report.md, report.json)
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
- A JSON list of **agent cards** in **creation order** (the roster only appends), in the server's exact `roster.json` format (indent 2):
  `{"name", "summary", "artifacts": [...], "created_at", "last_active_at"}`.
- **Nested:** `roster_25 ⊂ roster_50 ⊂ … ⊂ roster_1600` (by name).
- **`roster_25` = all core agents.** Each larger roster adds the next distractors. Merge by `created_at` so the core agents sit at their natural positions (early, middle and late), not all at the top.
- `created_at` is the agent's first request; `last_active_at` its last finished task (any `agent_response`, trigger fires included: both go through the batch manager).
- Execution logs are **not** in `state/`: the IA never reads them. They exist (in memory, from `build()`) only to produce the cards.

### 2.5 How the cards are made (`generate logs`, then `generate cards`)
Every card comes from the **production card updater** (`server/services/execution/card_updater.update_agent_card`), run over each agent's execution log, one IA request at a time, exactly as the batch manager runs it after a task:
1. **Logs.** Core agents' logs are hand-designed in `build_fixtures.py`. Distractor logs are synthetic: Haiku writes each request's instructions, tool steps and agent report from the agent's brief and counterpart (`generate logs`), and `render_agent` turns them into production-format lines. The first request is at the agent's roster creation time.
2. **Cards.** Each agent starts as a bare card (name only; production cards start from the IA's `create_agent` summary, which the first update replaces). Its log is appended up to the end of each request, then `update_agent_card` runs (same code, prompt, model and structured output as production). Trigger fires write no `agent_request`, so they never update a card, as in production.
3. **Contamination check.** No distractor's log or card may mention a core counterpart (that would plant a second correct owner for a case); real distractors may mention only their own counterpart (`text_violations` in `build_fixtures.py`, enforced during generation and by `--check`).

Real execution can't be replayed offline (it needs a live inbox and would take real actions), so the task history is synthetic; the cards themselves are written by production code.

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

- Optional fields: `pair` (links a dormant case to its matched siblings, e.g. `"ironwood"`: control c15, target c16, paraphrase c22, typo c30) and `split` (`heldout` for c11–c20, `stress` for c21–c31).
- Cases live in `CASES` in `build_fixtures.py` (`cases.json` is generated). **31 cases**: c01–c10 one per original case type, c11–c20 five dormant control/target pairs, c21–c31 the stress groups. §0.4 lists what each group tests.

---

## 5. Harness contract

- **Per size N:**
  - fresh temp `OPENPOKE_DATA_DIR`
  - copy `state/` verbatim
  - write `rosters/roster_N.json` (cards) as `execution_agents/roster.json`
  - copy `embeddings/agent_embeddings.npz` into `execution_agents/` (the server's search store loads it once; it covers every size, so searches only embed their query)
- **Per case:**
  - Build the prompt with `build_system_prompt()` and `prepare_message_with_history(message, get_working_memory_log().render_transcript())`.
  - Loop like `InteractionAgentRuntime._run_interaction_loop` (`_make_llm_call`, assistant entries with `reasoning_details`, `_format_tool_result`), running tool calls in order.
  - `search_agents` runs for real (read-only). `create_agent`, `send_message_to_agent`, `send_message_to_user`, `send_draft` and `wait` are stubbed with **production-identical results and error texts**: `create_agent` rejects existing names; `send_message_to_agent` rejects names that are neither in the roster nor created earlier in the case. Nothing is written, so concurrent cases never see each other's agents.
  - **Stop** once a response delegates successfully with nothing in flight (no `search_agents` in it, no created agent left unsent, no rejected send), or after 6 iterations. A message can take several responses to route, e.g. task A sent to its known agent while task B's is searched for.
- **Classification:** a delegation to a roster agent is a reuse; to an agent created during the case (or any other name) a create (`NEW`).
- **Outcome for each expected delegation:** `correct`, `wrong_reuse`, `false_create`, `false_reuse`, or `missed`. Extra unexpected delegations are recorded separately.
- **Also recorded per case:** every search (query, mode `all`/`search`/`fallback`, agents returned), creates (with the card the IA wrote, and whether it searched first), and rejected sends. The report adds an *Agent search* table (gold in search results, creates without a search, fallbacks), case-group pass rates, and a before/after comparison with `--baseline` (default `results/baseline_all_x10`).

---

## 6. Rebuilding and running

```bash
# fixtures (LLM stages are one-off and frozen under fixtures/generated/; spend in generated/cost.json)
python -m evals.routing.generate logs          # synthetic task logs for every distractor (Haiku; $1.30 actual)
python -m evals.routing.generate cards         # every card via the production card updater ($0.75 actual)
python -m evals.routing.generate embeddings    # prebuilt search vectors, gitignored (~$0.01)
python -m evals.routing.build_fixtures --check # write state/, rosters/ (cards), cases.json + self-check

# checks before spending on the IA
python -m evals.routing.run validate
python -m evals.routing.recall                 # offline: is each gold in the top 10? (queries = case messages)

# the eval (compare against the names-only baseline in the report)
python -m evals.routing.run run --repeats 10 --concurrency 8 --out evals/routing/results/<name>   # ~$2.40 for all 31 cases
python -m evals.routing.recall --from-run evals/routing/results/<name>   # recall with the IA's own queries
```

Generation stages resume where they stopped (`--fresh` redoes everything; `--limit N` is a smoke test). After changing logs, rerun `cards --fresh` and `embeddings`.
