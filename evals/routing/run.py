"""Routing eval harness: run the real interaction agent on each case and record which agent it picked.

    python -m evals.routing.run --smoke                        # sizes 25, 400, 1600 x 3 repeats (~$0.50)
    python -m evals.routing.run --repeats 10                   # every case x every size x 10 (ask first: ~$4)
    python -m evals.routing.run --cases c07,c21 --sizes 1600   # a few cases, one size

Each case is a frozen snapshot: the conversation (fixtures/working_memory.log) and a roster of N agent cards
(every card in fixtures/roster.json with min_size <= N). The harness calls InteractionAgentRuntime.execute()
with the case's message, as the chat route does, and swaps out only what touches the outside world, per case:
  - the roster is a per-case copy of roster.json, so the real create_agent / send_message_to_agent write to it;
  - the execution batch manager is a stub, so delegated tasks never run;
  - the conversation log is a stub, so replies don't land in the shared working memory (which would leak into
    other cases and start the summarizer).
Everything else is production code: prompt, model call, tool loop, tools, agent search and embeddings.
Results go to results/<name>/decisions.jsonl and are scored into report.md by score.py.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

SERVER_DATA = (Path(__file__).resolve().parents[2] / "server" / "data").resolve()
DATA = Path(tempfile.mkdtemp(prefix="openpoke-routing-eval-")).resolve()
os.environ["OPENPOKE_DATA_DIR"] = str(DATA)  # before any server import: modules bind their data paths on import

import argparse
import asyncio
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from server.agents.interaction_agent import tools
from server.agents.interaction_agent.agent import build_system_prompt
from server.agents.interaction_agent.runtime import InteractionAgentRuntime
from server.config import data_dir, get_settings
from server.services.execution.agent_search import _embed, card_texts, get_embedding_store
from server.services.execution.roster import AgentCard, AgentRoster

from . import score

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
RESULTS = ROOT / "results"
EMBEDDINGS_CACHE = FIXTURES / "embeddings.npz"
SIZES = (25, 50, 100, 200, 400, 800, 1600)
CARD_FIELDS = ("name", "summary", "artifacts", "created_at", "last_active_at")


# --------------------------------------------------------------------------- the outside world, per case


class _ConversationStub:
    """Stands in for the conversation log: the agent's replies are kept on the case instead of being written to
    the shared working memory."""

    def __init__(self) -> None:
        self.entries: List[Dict[str, str]] = []

    def record_user_message(self, content: str) -> None:
        self.entries.append({"tag": "user_message", "text": content})

    def record_agent_message(self, content: str) -> None:
        self.entries.append({"tag": "agent_message", "text": content})

    def record_reply(self, content: str) -> None:
        self.entries.append({"tag": "poke_reply", "text": content})

    def record_wait(self, reason: str) -> None:
        self.entries.append({"tag": "wait", "text": reason})

    def load_transcript(self) -> str:  # only used when working memory is empty, which never happens here
        return ""


class _NoExecution:
    """Stands in for the execution batch manager: delegated tasks are accepted but never run."""

    async def execute_agent(self, agent_name: str, instructions: str, *args: Any, **kwargs: Any) -> Any:
        return SimpleNamespace(success=True)


@dataclass
class _World:
    roster: AgentRoster
    conversation: _ConversationStub = field(default_factory=_ConversationStub)


_WORLD: ContextVar[_World] = ContextVar("routing_eval_world")


def _install_stubs() -> None:
    if data_dir().resolve() != DATA or SERVER_DATA in [DATA, *DATA.parents]:
        raise SystemExit(f"refusing to run: server data dir is {data_dir()}, expected the temp dir {DATA}")
    # if tools.py stops using these names, the stubs would silently miss: fail loudly instead
    missing = [n for n in ("get_agent_roster", "get_conversation_log", "_EXECUTION_BATCH_MANAGER") if not hasattr(tools, n)]
    if missing:
        raise SystemExit(f"tools.py no longer has {missing}: update the stubs in run.py")
    # the tools look these up on every call, so each case (its own asyncio task and context) sees its own world
    tools.get_agent_roster = lambda: _WORLD.get().roster
    tools.get_conversation_log = lambda: _WORLD.get().conversation
    tools._EXECUTION_BATCH_MANAGER = _NoExecution()
    # The store keeps every vector in memory for the whole run. Its save() prunes memory to the roster it was
    # given, and with cases of different sizes running at once that pruning would race (README: known issues).
    get_embedding_store().save = lambda keep: None


# --------------------------------------------------------------------------- fixtures


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _roster(size: int) -> List[Dict[str, Any]]:
    return [{k: c[k] for k in CARD_FIELDS} for c in _load(FIXTURES / "roster.json") if c["min_size"] <= size]


def _select_cases(wanted: Optional[str]) -> List[Dict[str, Any]]:
    cases = _load(FIXTURES / "cases.json")
    if not wanted:
        return cases
    prefixes = [w.strip() for w in wanted.split(",") if w.strip()]
    picked = [c for c in cases if any(c["id"] == p or c["id"].startswith(p + "_") for p in prefixes)]
    if not picked:
        raise SystemExit(f"no cases match {wanted}")
    return picked


def _prepare_data_dir() -> None:
    """Install the working memory and the embedding cache where the server reads them."""
    (DATA / "conversation").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIXTURES / "working_memory.log", DATA / "conversation" / "poke_working_memory.log")
    (DATA / "execution_agents").mkdir(parents=True, exist_ok=True)
    if EMBEDDINGS_CACHE.exists():
        shutil.copyfile(EMBEDDINGS_CACHE, DATA / "execution_agents" / "agent_embeddings.npz")


async def _warm_embeddings() -> None:
    """Embed any card text the cache lacks once, up front, instead of in every concurrent first search."""
    store = get_embedding_store()
    texts = [t for c in _roster(max(SIZES)) for t in card_texts(AgentCard(**c))]
    missing = store.missing(texts)
    if missing:
        print(f"embedding {len(missing)} card texts missing from the cache...", flush=True)
        store.add(missing, await _embed(missing))
        type(store).save(store, keep=texts)  # the real save, once: write the cache for next time
        shutil.copyfile(DATA / "execution_agents" / "agent_embeddings.npz", EMBEDDINGS_CACHE)


# --------------------------------------------------------------------------- one case


_AGENT_NAME = re.compile(r'<agent name="([^"]*)"')


def _search_record(query: Any, payload: Any) -> Dict[str, Any]:
    text = payload if isinstance(payload, str) else json.dumps(payload)
    mode = "search" if text.startswith("Search results") else "fallback" if "names only" in text else "all"
    return {"query": query, "mode": mode, "returned": [html.unescape(n) for n in _AGENT_NAME.findall(text)]}


async def _run_case(case: Dict[str, Any], size: int, repeat: int, cards: List[Dict[str, Any]]) -> Dict[str, Any]:
    case_dir = Path(tempfile.mkdtemp(prefix="case-", dir=DATA))
    (case_dir / "roster.json").write_text(json.dumps(cards), encoding="utf-8")
    world = _World(roster=AgentRoster(case_dir / "roster.json"))
    _WORLD.set(world)

    runtime = InteractionAgentRuntime()
    runtime.conversation_log = world.conversation
    calls: List[Dict[str, Any]] = []
    tool_calls: List[Dict[str, Any]] = []
    make_llm_call, execute_tool = runtime._make_llm_call, runtime._execute_tool

    async def recorded_llm_call(system_prompt: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        started = time.monotonic()
        response = await make_llm_call(system_prompt, messages)
        message = runtime._extract_assistant_message(response)
        usage = response.get("usage") or {}
        calls.append({
            "latency_s": round(time.monotonic() - started, 2),
            "cost": usage.get("cost"),
            "prompt_tokens": usage.get("prompt_tokens"),
            "cached_tokens": (usage.get("prompt_tokens_details") or {}).get("cached_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "content": message.get("content") or "",
            "reasoning": (message.get("reasoning") or "")[:2000],
        })
        return response

    async def recorded_execute_tool(tool_call: Any) -> Any:
        result = await execute_tool(tool_call)
        entry: Dict[str, Any] = {"name": tool_call.name, "arguments": tool_call.arguments, "success": result.success}
        if tool_call.name == "search_agents" and result.success:
            entry["search"] = _search_record(tool_call.arguments.get("query"), result.payload)
        else:
            entry["result"] = result.payload
        tool_calls.append(entry)
        return result

    runtime._make_llm_call = recorded_llm_call
    runtime._execute_tool = recorded_execute_tool

    started = time.monotonic()
    result = await runtime.execute(case["message"])
    created = [t["arguments"].get("agent_name") for t in tool_calls if t["name"] == "create_agent" and t["success"]]
    return {
        "case_id": case["id"],
        "group": case["group"],
        "size": size,
        "repeat": repeat,
        "message": case["message"],
        "expected": case["expected"],
        "delegations": [
            {"agent_name": t["arguments"]["agent_name"], "instructions": t["arguments"].get("instructions"),
             "kind": "create" if t["arguments"]["agent_name"] in created else "reuse"}
            for t in tool_calls if t["name"] == "send_message_to_agent" and t["success"]
        ],
        "searches": [t["search"] for t in tool_calls if "search" in t],
        "creates": [{"arguments": t["arguments"], "success": t["success"], "result": t.get("result")}
                    for t in tool_calls if t["name"] == "create_agent"],
        "tool_calls": tool_calls,
        "llm_calls": calls,
        "replies": world.conversation.entries[1:],  # [0] is the user's message
        "error": None if result.success else result.error,
        "latency_s": round(time.monotonic() - started, 2),
        "cost": round(sum(c["cost"] or 0.0 for c in calls), 6),
    }


def provider_error(row: Dict[str, Any]) -> bool:
    """execute() turns a failed model request into an error result. That's infrastructure, not routing."""
    return bool(row.get("error")) and "OpenRouter request failed" in row["error"]


async def _run_with_retry(case, size, repeat, cards, sem) -> Dict[str, Any]:
    async with sem:
        for attempt in range(1, 4):
            row = await _run_case(case, size, repeat, cards)  # a fresh world each attempt
            if not provider_error(row):
                break
            await asyncio.sleep(5 * attempt)
        row["attempts"] = attempt
        return row


# --------------------------------------------------------------------------- run


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def _hash(*parts: str) -> str:
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:12]


async def _run(args: argparse.Namespace) -> Path:
    _install_stubs()
    _prepare_data_dir()
    await _warm_embeddings()
    cases = _select_cases(args.cases)
    sizes = SIZES if args.sizes == "all" else tuple(int(s) for s in args.sizes.split(","))
    name = args.name or datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = RESULTS / name
    if run_dir.exists():
        raise SystemExit(f"{run_dir} already exists")
    run_dir.mkdir(parents=True)

    fixture_text = [(FIXTURES / f).read_text(encoding="utf-8") for f in ("roster.json", "cases.json", "working_memory.log")]
    meta = {
        "name": name,
        "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": _git("rev-parse", "--short", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain", "--", "server", "evals/routing/fixtures")),
        "model": get_settings().interaction_agent_model,
        "prompt_hash": _hash(build_system_prompt(), json.dumps(tools.get_tool_schemas(), sort_keys=True)),
        "fixtures_hash": _hash(*fixture_text),
        "sizes": list(sizes),
        "repeats": args.repeats,
        "cases": [c["id"] for c in cases],
    }
    (run_dir / "run_meta.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")

    jobs = [(c, s, r) for s in sizes for c in cases for r in range(1, args.repeats + 1)]
    print(f"{len(jobs)} decisions: {len(cases)} cases x sizes {list(sizes)} x {args.repeats} repeats -> {run_dir}", flush=True)
    rosters = {s: _roster(s) for s in sizes}
    sem = asyncio.Semaphore(args.concurrency)
    done = 0
    with open(run_dir / "decisions.jsonl", "w", encoding="utf-8") as out:
        for row in asyncio.as_completed([_run_with_retry(c, s, r, rosters[s], sem) for c, s, r in jobs]):
            row = await row
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            done += 1
            if done % 25 == 0 or done == len(jobs):
                print(f"  {done}/{len(jobs)}", flush=True)
    return run_dir


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cases", help="comma-separated case ids or prefixes (c07,c21); default all")
    parser.add_argument("--sizes", default="all", help="comma-separated roster sizes, or 'all' (default)")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--smoke", action="store_true", help="shorthand for --sizes 25,400,1600 --repeats 3")
    parser.add_argument("--concurrency", type=int, default=8, help="decisions in flight at once (default 8)")
    parser.add_argument("--name", help="results/<name>; default a timestamp")
    parser.add_argument("--baseline", type=Path, help="a previous results dir to compare against in the report")
    args = parser.parse_args(argv)
    if args.smoke:
        args.sizes, args.repeats = "25,400,1600", 3
    try:
        run_dir = asyncio.run(_run(args))
    finally:
        shutil.rmtree(DATA, ignore_errors=True)
    report = score.write_report(run_dir, args.baseline)
    print(f"\n{report['summary_line']}\nreport: {run_dir / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
