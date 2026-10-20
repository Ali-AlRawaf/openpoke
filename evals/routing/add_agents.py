"""Add agents to the routing-eval roster from written briefs, and check that traps reach search results.

    python -m evals.routing.add_agents                      # card for every brief not yet in roster.json
    python -m evals.routing.add_agents --only "Agent Name"  # (re)build one
    python -m evals.routing.add_agents check results/<run>  # rank each case's gold and traps for that run's queries

A card is made the way a real agent's card is made:
  1. Haiku writes the agent's task history from its brief (fixtures/agent_briefs.json): per task, Poke's
     instructions, the tool calls and results, and the agent's final report.
  2. Each task goes into a throwaway data dir through the production log store, then the production card
     updater runs, as the batch manager does after every task.
  3. The card joins fixtures/roster.json with role "trap", replacing one unreferenced noise card with the same
     min_size, so every roster size keeps its agent count.
Only roster.json changes; add the new agent to a case's `traps` in cases.json by hand.
"""

from __future__ import annotations

import os
import tempfile

os.environ.setdefault("OPENPOKE_DATA_DIR", tempfile.mkdtemp(prefix="openpoke-add-agents-"))

import argparse
import asyncio
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict

from server.config import data_dir, get_settings
from server.openrouter_client import request_chat_completion
from server.services.execution import AgentCard, get_agent_roster, get_execution_agent_logs
from server.services.execution import card_updater
from server.services.execution.agent_search import _embed, card_texts, get_embedding_store

FIXTURES = Path(__file__).resolve().parent / "fixtures"
ROSTER_PATH = FIXTURES / "roster.json"
CASES_PATH = FIXTURES / "cases.json"
BRIEFS_PATH = FIXTURES / "agent_briefs.json"
EMBEDDINGS_CACHE = FIXTURES / "embeddings.npz"  # gitignored; vectors for every card text, keyed like production
SIZES = (25, 50, 100, 200, 400, 800, 1600)
WINDOW = ("2026-07-20 00:00", "2026-10-13 22:30")  # agent history must end before the recent conversation window

# The core counterparts each belong to exactly one gold-labelled agent. A trap that mentions one would make
# that case's label ambiguous, so these must not appear in a trap's history or card.
CORE_TERMS = [
    "Celeste", "harrowhillestate", "Harrow Hill", "Natarajan", "Priya", "Volkov", "ironbarkreno", "Ironbark",
    "Ishikawa", "Hana", "copperleaf", "Achebe", "Wendell", "Brightmoor", "Sandhu", "lumenandlinen", "Bellandi",
    "riverdalerecsoccer", "Gabe", "Lindqvist", "Oyelaran", "Marcus", "Fernway", "lakeporthydro", "Tidewater",
    "Wierzbicki", "prairieux", "osteriavaldina", "Oakhurst", "Haddad", "corktownphysio", "Verrière", "Verriere",
    "Fairbanks", "ledgerline", "Noor", "inkwellandvine", "Inkwell", "Ironwood", "Pemberton", "Harold", "Brandt",
]

PERSONA = (
    "The user is Theo Marchetti <theo@northfoldstudio.ca>, co-founder and head of product at Northfold Studio, a "
    "12-person product design studio on Queen St E, Toronto. He lives in Leslieville with his fiance Jules Arden "
    "(jules.arden@quaymail.net); they marry June 12, 2027. Timezone America/Toronto. 'Poke' is his AI assistant: it "
    "delegates tasks to named execution agents that have Gmail and trigger tools. Calendar anchors: Mon 2026-07-20, "
    "Mon 2026-08-17, Mon 2026-09-14, Mon 2026-10-12, Wed 2026-10-21; the weekdays in the brief are correct, copy them."
)

SYSTEM = (
    "You write realistic fixture data for an AI email assistant's execution agent. Given a brief, write the agent's "
    "task history. For each task: the exact instructions Poke sent (explicit and complete: who, what, email "
    "addresses, dates, and 'do not send' when only drafting), the tool calls the agent made, a realistic result for "
    "each call, and the agent's final report to Poke (factual, specific: dates, amounts, IDs, and 'Nothing was "
    "sent.' when nothing was sent). Tool arguments are a JSON object as a string. Results look like the real tools: "
    "task_email_search returns a JSON list of emails with id, thread_id, subject, sender, recipient, timestamp, "
    "snippet; gmail_create_draft returns a draft id; gmail_execute_draft / gmail_reply_to_thread return a message id; "
    "createTrigger / updateTrigger return trigger_id, status and next_trigger. Use only the people, companies and "
    "addresses in the brief plus Theo and Jules. Every started_at is 'YYYY-MM-DD HH:MM' local time, in the order "
    "of the tasks, matching the dates in the brief."
)


class _Step(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: Literal["task_email_search", "gmail_create_draft", "gmail_execute_draft", "gmail_reply_to_thread",
                  "gmail_forward_email", "gmail_search_people", "createTrigger", "updateTrigger", "listTriggers"]
    arguments: str
    result: str


class _Task(BaseModel):
    model_config = ConfigDict(extra="forbid")
    started_at: str
    instructions: str
    steps: List[_Step]
    final_response: str


class _History(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tasks: List[_Task]


_HISTORY_FORMAT = {"type": "json_schema",
                   "json_schema": {"name": "task_history", "strict": True, "schema": _History.model_json_schema()}}


class Spend:
    def __init__(self) -> None:
        self.usd = 0.0
        self.calls = 0

    def add(self, response: Dict[str, Any]) -> Dict[str, Any]:
        self.usd += float((response.get("usage") or {}).get("cost") or 0.0)
        self.calls += 1
        return response


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def _core_terms_in(text: str) -> List[str]:
    return [t for t in CORE_TERMS if re.search(rf"\b{re.escape(t)}\b", text, re.I)]


def _problems(brief: Dict[str, Any], history: _History) -> List[str]:
    problems = []
    times = []
    for task in history.tasks:
        try:
            times.append(datetime.strptime(task.started_at, "%Y-%m-%d %H:%M"))
        except ValueError:
            problems.append(f"bad started_at {task.started_at!r}")
    if times and (times != sorted(times) or min(times) < datetime.strptime(WINDOW[0], "%Y-%m-%d %H:%M")
                  or max(times) > datetime.strptime(WINDOW[1], "%Y-%m-%d %H:%M")):
        problems.append(f"task times out of order or outside {WINDOW}")
    if not history.tasks or not all(t.steps for t in history.tasks):
        problems.append("a task has no tool calls")
    text = history.model_dump_json()
    email = re.search(r"<([^>]+@[^>]+)>", brief["counterpart"])
    if email and email.group(1).lower() not in text.lower():
        problems.append(f"counterpart address {email.group(1)} never appears")
    leaked = _core_terms_in(text)
    if leaked:
        problems.append(f"mentions core counterparts {leaked}")
    return problems


async def _write_history(brief: Dict[str, Any], spend: Spend) -> _History:
    prompt = (f"{PERSONA}\n\nAgent name: {brief['name']}\nCounterpart: {brief['counterpart']}\n"
              f"First task starts: {brief['start']}\nBrief: {brief['brief']}")
    problems: List[str] = []
    for _ in range(3):
        response = spend.add(await request_chat_completion(
            model=get_settings().execution_agent_model, system=SYSTEM, max_tokens=8000,
            messages=[{"role": "user", "content": prompt}], response_format=_HISTORY_FORMAT))
        content = ((response.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        history = _History.model_validate_json(content)
        problems = _problems(brief, history)
        if not problems:
            return history
    raise RuntimeError(f"{brief['name']}: {problems}")


async def _build_card(brief: Dict[str, Any], spend: Spend) -> Dict[str, Any]:
    history = await _write_history(brief, spend)
    name = brief["name"]
    roster, logs = get_agent_roster(), get_execution_agent_logs()
    roster.add_card(AgentCard(name=name))
    for task in history.tasks:
        # the log lines the execution agent writes (server/agents/execution_agent/agent.py truncates the same way)
        logs.record_request(name, task.instructions)
        for step in task.steps:
            logs.record_action(name, f"Calling {step.tool} with: {step.arguments[:200]}")
            logs.record_tool_response(name, step.tool, step.result[:500])
        logs.record_agent_response(name, task.final_response)
        # the updater finds its task by the request text as the log store reads it back
        instructions = next(p for tag, _, p in reversed(list(logs.iter_entries(name))) if tag == "agent_request")
        for _ in range(2):  # the updater keeps the old card on failure: retry once
            before = roster.get_card(name).model_dump()
            await card_updater.update_agent_card(name, instructions)
            roster.load()
            if roster.get_card(name).model_dump() != before:
                break
    card = roster.get_card(name)
    leaked = _core_terms_in(" ".join([card.summary, *card.artifacts]))
    if not card.summary or leaked:
        raise RuntimeError(f"{name}: unusable card (leaked {leaked})")
    started = [datetime.strptime(t.started_at, "%Y-%m-%d %H:%M") for t in history.tasks]
    return {"name": name, "summary": card.summary, "artifacts": card.artifacts,
            "created_at": started[0].strftime("%Y-%m-%d %H:%M:05"),
            "last_active_at": started[-1].strftime("%Y-%m-%d %H:%M:40"),
            "role": "trap", "min_size": brief["min_size"]}


async def add(only: str | None) -> int:
    roster_cards: List[Dict[str, Any]] = _load(ROSTER_PATH)
    briefs = [b for b in _load(BRIEFS_PATH) if (b["name"] == only if only else True)]
    present = {c["name"] for c in roster_cards}
    todo = briefs if only else [b for b in briefs if b["name"] not in present]
    if not todo:
        print("nothing to add")
        return 0

    spend = Spend()
    production_call = card_updater.request_chat_completion

    async def counted_call(**kwargs: Any) -> Dict[str, Any]:
        return spend.add(await production_call(**kwargs))

    card_updater.request_chat_completion = counted_call  # the production call, with spend accounting

    sem = asyncio.Semaphore(8)

    async def one(brief: Dict[str, Any]) -> Dict[str, Any] | Exception:
        async with sem:
            try:
                card = await _build_card(brief, spend)
                print(f"  built {brief['name']}: {len(card['artifacts'])} artifacts", flush=True)
                return card
            except Exception as exc:
                print(f"  FAILED {brief['name']}: {exc}", flush=True)
                return exc

    results = await asyncio.gather(*(one(b) for b in todo))
    built = [r for r in results if isinstance(r, dict)]

    referenced = {t for c in _load(CASES_PATH) for e in c["expected"] for t in [e["gold"], *e["traps"]]}
    for card in built:
        if card["name"] in present:  # rebuild in place
            roster_cards = [card if c["name"] == card["name"] else c for c in roster_cards]
            continue
        # replace one unreferenced noise card with the same min_size (chosen by name hash, so reruns agree)
        noise = sorted((c for c in roster_cards if c["role"] == "noise" and c["min_size"] == card["min_size"]
                        and c["name"] not in referenced),
                       key=lambda c: hashlib.sha1(c["name"].encode()).hexdigest())
        roster_cards.remove(noise[0])
        roster_cards.append(card)
    roster_cards.sort(key=lambda c: (c["created_at"], c["name"]))
    _save(ROSTER_PATH, roster_cards)
    print(f"added {len(built)}/{len(todo)} agents; spend ${spend.usd:.4f} over {spend.calls} calls")
    return 0 if len(built) == len(todo) else 1


# --------------------------------------------------------------------------- check


def _ranks(scores: np.ndarray) -> np.ndarray:
    order = np.argsort(-scores, kind="stable")
    ranks = np.empty(len(scores), dtype=int)
    ranks[order] = np.arange(1, len(scores) + 1)
    return ranks


async def check(run_dir: Path) -> int:
    """For every case: the best rank its gold and each trap reach for the queries the IA wrote in a run, at each
    roster size, scored the way search_agent_cards scores (an agent's best-matching card text)."""
    cards = [AgentCard(**{k: c[k] for k in ("name", "summary", "artifacts", "created_at", "last_active_at")})
             for c in _load(ROSTER_PATH)]
    min_size = {c["name"]: c["min_size"] for c in _load(ROSTER_PATH)}
    cases = _load(CASES_PATH)
    queries: Dict[str, set] = {}
    with open(run_dir / "decisions.jsonl", encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            queries.setdefault(row["case_id"], set()).update(s["query"] for s in row["searches"])
    all_queries = sorted({q for qs in queries.values() for q in qs})
    if not all_queries:
        print("no searches in that run")
        return 1

    store = _load_store()
    texts = [card_texts(c) for c in cards]
    flat = [t for ts in texts for t in ts]
    missing = store.missing(flat)
    if missing:
        store.add(missing, await _embed(missing))
        _save_store(store, flat)
    query_vectors = np.concatenate([await _embed(all_queries[i:i + 256]) for i in range(0, len(all_queries), 256)])
    owners = np.array([i for i, ts in enumerate(texts) for _ in ts])
    sims = store.rows(flat) @ query_vectors.T  # texts x queries
    top_k = get_settings().agent_search_top_k
    qindex = {q: i for i, q in enumerate(all_queries)}

    print(f"Best rank over the IA's queries in {run_dir.name} (top {top_k} reach search results)\n")
    for size in SIZES:
        member = np.array([min_size[c.name] <= size for c in cards])
        print(f"## size {size}")
        for case in cases:
            qs = [qindex[q] for q in queries.get(case["id"], ())]
            if not qs:
                continue
            best: Dict[str, int] = {}
            for q in qs:
                scores = np.full(len(cards), -np.inf, dtype=np.float32)
                np.maximum.at(scores, owners, sims[:, q])
                scores[~member] = -np.inf
                ranks = _ranks(scores)
                for i, card in enumerate(cards):
                    if member[i]:
                        best[card.name] = min(best.get(card.name, 10**6), int(ranks[i]))
            for e in case["expected"]:
                gold = "NEW" if e["gold"] == "NEW" else best.get(e["gold"])
                present = [t for t in e["traps"] if t in best]
                reached = [f"{t} ({best[t]})" for t in present if best[t] <= top_k]
                print(f"  {case['id'][:40]:40} gold rank {gold!s:>4}  traps in top {top_k}: {len(reached)}/{len(present)}"
                      + (f"  {', '.join(reached)}" if reached else ""))
    return 0


def _load_store():
    """The production embedding store, seeded from the fixtures cache so known texts aren't re-embedded."""
    target = data_dir() / "execution_agents" / "agent_embeddings.npz"
    if EMBEDDINGS_CACHE.exists() and not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(EMBEDDINGS_CACHE, target)
    return get_embedding_store()


def _save_store(store, keep: List[str]) -> None:
    store.save(keep=keep)
    shutil.copyfile(data_dir() / "execution_agents" / "agent_embeddings.npz", EMBEDDINGS_CACHE)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", nargs="?", default="add", choices=["add", "check"])
    parser.add_argument("run_dir", nargs="?", type=Path, help="check: a results directory with decisions.jsonl")
    parser.add_argument("--only", help="add: build just this brief (rebuilds it if already in the roster)")
    args = parser.parse_args(argv)
    if args.command == "check":
        if not args.run_dir:
            parser.error("check needs a results directory")
        return asyncio.run(check(args.run_dir))
    return asyncio.run(add(args.only))


if __name__ == "__main__":
    sys.exit(main())
