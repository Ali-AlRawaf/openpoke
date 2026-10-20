# Routing eval

**Question:** when the user sends a message, does the interaction agent (IA) give each task to the right execution agent, reusing the agent that owns that work or creating a new one, as the roster grows from 25 to 1,600 agents?

## How it works

Each **case** is a frozen snapshot plus one new user message:

- **Conversation:** `fixtures/working_memory.log`, a summary of ~300 older messages followed by the 80 most recent ones, in the server's own file format. It's the same for every case.
- **Roster:** the first N agent cards of `fixtures/roster.json`, where N is the roster size (25, 50, 100, 200, 400, 800 or 1,600).
- **Message:** taken from `fixtures/cases.json`, together with the gold answer for each task (an existing agent's name, or `NEW`).

`run.py` calls the production `InteractionAgentRuntime.execute()` on the message, as the chat route does. Only the parts that touch the outside world are replaced, separately for each case:

| Replaced | With | Why |
|---|---|---|
| The roster file | A copy for this case | The real `create_agent` / `send_message_to_agent` can write to it without affecting other cases |
| The execution batch manager | A stub that accepts tasks | Delegated tasks never actually run (no Gmail) |
| The conversation log | A stub that keeps the replies | Replies would otherwise land in the shared working memory and start the summarizer |

Everything else is production code: the prompt, the model call, the tool loop, every tool, agent search and the embeddings. The harness wraps the model call and tool execution only to record them. The turn runs to completion, exactly as in the app.

`score.py` then matches each task's gold answer to what the IA sent and writes `report.md`.

## Files

```
run.py                 harness: python -m evals.routing.run
score.py               scorer:  python -m evals.routing.score results/<run>
add_agents.py          fixture tool: brief -> agent card (production card updater); `check` ranks traps offline
fixtures/
  cases.json           31 cases: message, expected tasks (gold + traps), group, note on why the gold is right
  roster.json          1,600 agent cards in creation order; each has role (core/trap/noise) and min_size
  working_memory.log   the conversation every case starts from
  agent_briefs.json    the written briefs behind the 48 traps made by add_agents.py
  world.md             the fictional user, the people around them and the timeline (reference only)
  embeddings.npz       vector cache for agent search (gitignored, rebuilt when missing)
results/<run>/         decisions.jsonl (every model call and tool call), report.md, report.json, run_meta.json
results/v1/            the original before/after runs (history; see below)
archive/               the v1 generators, harness and spec, kept for reference (not runnable as is)
```

## The roster

| Role | Count | What it is | In rosters |
|---|---|---|---|
| **core** | 25 | Hand-written agents with full histories; the only ones the conversation mentions. 14 of them are gold answers; the other 11 are familiar agents that must *not* be reused for new work. | Every size |
| **trap** | 92 | Near-misses for a specific gold agent: the same kind of work (a deposit, a reschedule, a membership hold, a cost split) with a different person or company. Some have a similar name ("Harrowfield Rentals" vs "Harrow Hill"), the same first name ("Dmitri Sokolov" vs Dmitri Volkov), or the same counterpart on an unrelated task. Each case lists its traps in `cases.json`. | Phased in: by size 400, every gold agent has at least 3 |
| **noise** | 1,483 | Realistic agents from the same person's life (bills, bookings, lookups, emails to other people) that aren't aimed at any case | Fill each size up to N |

Rosters are nested: each size contains every agent of the smaller sizes. The cards were all written by the production card updater from task logs, so they read like real cards.

## Case groups

| Group | Cases | What it tests |
|---|---|---|
| Overload target (dormant, inference) | c07, c12, c14, c16, c18, c20 | A counterpart last active weeks ago (only in the summary), named in a way the owner's agent name doesn't match ("ask ironwood…" → "Gym Membership Freeze"). This is the failure the solution fixes. |
| Dormant control (name match) | c11, c13, c15, c17, c19 | The same owners, referred to by words from their agent names. Pairs with the targets above. |
| Easy recent | c01, c03, c05, c06, c08, c09 | Follow-ups on recent work: a named counterpart, "yep send it" for a pending draft, changing a trigger, the same first name on a different person, a new person with an overlapping name |
| Policy-ambiguous | c02, c04 | A new task for a known person; replying to an email an unrelated-sounding agent found |
| Multi-task | c10 | One message, two tasks: one for a known agent, one that needs a new agent |
| Stress: paraphrase | c21–c24 | A dormant counterpart described without its name ("our guy at the credit union") |
| Stress: new counterpart, familiar topic | c25–c27 | A new dentist, mechanic or lunch spot when similar agents exist. The answer is to create a new agent. |
| Stress: typo | c28–c31 | The overload targets with the name misspelled ("wendel", "ironwod") |

## Commands

```bash
python -m evals.routing.run --smoke                     # sizes 25, 400, 1600 x 3 repeats: 279 decisions, ~$0.50, ~5 min
python -m evals.routing.run --repeats 10                # everything: 2,170 decisions, ~$4, ~35 min
python -m evals.routing.run --cases c07,c21 --sizes 1600
python -m evals.routing.run --smoke --baseline results/<earlier run>   # adds a before/after table

python -m evals.routing.score results/<run>             # re-score an existing run
python -m evals.routing.add_agents                      # build cards for new briefs in agent_briefs.json
python -m evals.routing.add_agents check results/<run>  # do each case's traps reach the top 10 for the IA's queries?
```

## Reading the report

Each expected task gets one outcome:

| Outcome | Meaning |
|---|---|
| `correct` | Sent to the gold agent (or, when the gold is `NEW`, to an agent created in that turn) |
| `wrong_reuse` | Sent to a different existing agent. *Picked a trap* counts the ones that were the case's own traps. |
| `false_create` | Created a new agent although the gold agent exists (fragmentation) |
| `false_reuse` | The gold is `NEW`, but it reused an existing agent |
| `missed` | Nothing was sent for the task, e.g. the IA asked the user to clarify |

A decision passes when every task in it is `correct`.

The other columns:
- **Searched:** how often the IA called `search_agents`.
- **Gold in results / traps shown:** how often the gold agent, or at least one trap, came back from those searches. These count single-task cases only, because nothing records which search served which task in c10.
- **Calls, cost, latency:** per decision.

## How the fixtures were made

1. **v1.** The persona, the conversation, the 25 core agents and the cases were written by hand. 1,575 distractor agents were generated with Haiku, and their task logs were run through the production card updater to get their cards. That code is in `archive/` (see `archive/SPEC.md`).
2. **v2.** The traps were redesigned so that each case meets real near-misses at scale. In v1, about a third of the cases never had their intended trap appear in search results at 1,600 agents. Each new trap is a written brief in `fixtures/agent_briefs.json`, turned into a card by `add_agents.py`: Haiku writes 2–3 tasks of history, the production log store records them, and the production card updater writes the card. Each new trap replaced one noise card of the same `min_size`, so roster sizes are unchanged. `add_agents.py check` verified against the queries the IA wrote in v1 that the traps now reach its top-10 results.

The working-memory log, the core agents and the cases are unchanged from v1. The cases are now plain data: edit `cases.json` directly.

## Limits

- **One fictional user and one conversation.** Every task history is synthetic, and the cases, gold labels and traps were written by the same people who built the solution.
- **The run stops at routing.** Execution is stubbed, so the eval doesn't test what the agents then do, card updates after a task, or later turns.
- **Labels follow one policy:** reuse the owner of the thread, draft or trigger first, then the owner of the counterpart, otherwise create. That policy comes from the IA's system prompt (see the `note` on each case). Cases where the policy itself is ambiguous are left out rather than labelled by decree.
- **Search coverage figures leave out the multi-task case.**

## v1 results (history)

`results/v1/` holds the original before/after runs, made with the v1 harness and fixtures:
- **Before:** `baseline_all_x10`, the names-only roster in the prompt.
- **After:** `final_all_x10`, agent cards with `search_agents`.

On the overload-target cases, accuracy at 1,600 agents went from 62% to 100%, with 0 wrong reuses and 0 false creates in 2,170 decisions. Those numbers aren't directly comparable with runs of this suite, because the traps and the harness changed. New runs are compared with earlier runs of this suite using `--baseline`.
