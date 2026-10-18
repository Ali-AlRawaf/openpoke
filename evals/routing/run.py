"""Routing eval runner: validate fixtures, dry-run prompt sizes, or run the real IA routing loop.

    python -m evals.routing.run validate
    python -m evals.routing.run run --dry-run
    python -m evals.routing.run run --sizes 25,400 --cases c01_x,c05_y

Nothing under ``server`` is imported at module level: ``OPENPOKE_DATA_DIR`` is pointed at a
fresh temp dir first (see ``_init_data_dir``), because the server binds its data paths (and
creates files there) at import time.
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from . import score

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_DATA = (REPO_ROOT / "server" / "data").resolve()
DEFAULT_FIXTURES = "evals/routing/fixtures"
DEFAULT_SIZES = "25,50,100,200,400,800,1600"
MAX_ITERATIONS = 3
INTERCEPTED = {"send_message_to_agent", "send_message_to_user", "send_draft", "wait"}
CONVERSATION_TAGS = {"user_message", "poke_reply", "agent_message", "wait"}
AGENT_LOG_TAGS = {"agent_request", "agent_action", "tool_response", "agent_response"}
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

_DATA_DIR: Optional[Path] = None


# --------------------------------------------------------------------------- cases model (SPEC §4)


class Expected(BaseModel):
    model_config = ConfigDict(extra="allow")
    task: str
    gold: str = Field(min_length=1)


class Case(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str = Field(min_length=1)
    category: str
    rule: int | List[int]
    message: str = Field(min_length=1)
    expected: List[Expected] = Field(min_length=1)
    rationale: str


class CasesFile(BaseModel):
    model_config = ConfigDict(extra="allow")
    version: int
    cases: List[Case] = Field(min_length=1)

    @field_validator("cases")
    @classmethod
    def _unique_ids(cls, cases: List[Case]) -> List[Case]:
        seen, dupes = set(), set()
        for case in cases:
            (dupes if case.id in seen else seen).add(case.id)
        if dupes:
            raise ValueError(f"duplicate case ids: {sorted(dupes)}")
        return cases


# --------------------------------------------------------------------------- data dir / server import


def _init_data_dir() -> Path:
    """Point OPENPOKE_DATA_DIR at a fresh temp dir. Must run before any ``server`` import."""
    global _DATA_DIR
    if _DATA_DIR is not None:
        return _DATA_DIR
    loaded = [m for m in sys.modules if m == "server" or m.startswith("server.")]
    if loaded:
        raise SystemExit(f"refusing to run: server modules already imported ({loaded[:3]}...)")
    path = Path(tempfile.mkdtemp(prefix="openpoke-routing-eval-")).resolve()
    if path == SERVER_DATA or SERVER_DATA in path.parents or path in SERVER_DATA.parents:
        raise SystemExit(f"refusing to run: data dir {path} overlaps {SERVER_DATA}")
    os.environ["OPENPOKE_DATA_DIR"] = str(path)
    _DATA_DIR = path
    return path


def _check_server_paths() -> None:
    """After importing server, confirm every data path it bound lives in our temp dir."""
    from server.config import data_dir
    from server.services.execution import roster as roster_mod, log_store as log_store_mod
    from server.services.conversation import log as conv_mod
    from server.services.conversation.summarization import working_memory_log as wm_mod
    from server.services import timezone_store as tz_mod, triggers as triggers_mod
    from server.services.gmail import importance_watcher as gmail_mod

    bound = [
        data_dir(),
        roster_mod._ROSTER_PATH,
        log_store_mod._EXECUTION_LOG_DIR,
        conv_mod._CONVERSATION_LOG_PATH,
        wm_mod._WORKING_MEMORY_LOG_PATH,
        tz_mod._TIMEZONE_PATH,
        triggers_mod._default_db_path,
        gmail_mod._DEFAULT_SEEN_PATH,
    ]
    for p in bound:
        rp = Path(p).resolve()
        if rp == SERVER_DATA or SERVER_DATA in rp.parents or _DATA_DIR not in [rp, *rp.parents]:
            raise SystemExit(f"refusing to run: server bound data path {rp} outside temp dir {_DATA_DIR}")


def _server():
    """Lazily import the production modules the harness drives."""
    _init_data_dir()
    import server.agents.interaction_agent.agent as ia_agent
    import server.agents.interaction_agent.runtime as ia_runtime
    import server.agents.interaction_agent.tools as ia_tools
    from server.services.conversation import get_working_memory_log
    from server.openrouter_client import OpenRouterError

    _check_server_paths()
    return ia_agent, ia_runtime, ia_tools, get_working_memory_log, OpenRouterError


def _logfmt():
    _init_data_dir()
    from . import logfmt

    return logfmt


# --------------------------------------------------------------------------- fixtures


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else (REPO_ROOT / p)


def _parse_sizes(text: str) -> List[int]:
    sizes = sorted({int(s) for s in text.split(",") if s.strip()})
    if not sizes or any(s <= 0 for s in sizes):
        raise SystemExit(f"bad --sizes: {text!r}")
    return sizes


def _load_cases(fixtures: Path) -> CasesFile:
    return CasesFile.model_validate_json((fixtures / "cases.json").read_text(encoding="utf-8"))


def _load_roster(fixtures: Path, size: int) -> List[str]:
    return json.loads((fixtures / "rosters" / f"roster_{size}.json").read_text(encoding="utf-8"))


def validate_fixtures(fixtures: Path, sizes: List[int]) -> List[str]:
    """Return every problem found (empty list == valid)."""
    logfmt = _logfmt()
    problems: List[str] = []
    state = fixtures / "state"
    if not state.is_dir():
        return [f"missing state dir: {state}"]

    # every .log line parses (server silently drops unparseable lines)
    for log in sorted(state.rglob("*.log")):
        rel = log.relative_to(fixtures)
        raw = log.read_text(encoding="utf-8")
        if raw and not raw.endswith("\n"):
            problems.append(f"{rel}: last line has no trailing newline (next append would corrupt it)")
        for n, line in enumerate(raw.split("\n"), 1):
            if not line.strip():
                continue
            parsed = logfmt.parse_line(line)
            if parsed is None:
                problems.append(f"{rel}:{n}: unparseable line (server would drop it): {line[:120]!r}")
                continue
            tag, ts, _ = parsed
            in_wm = log.name == "poke_working_memory.log"
            if in_wm and tag in {"summary_info", "conversation_summary"}:
                continue
            allowed = AGENT_LOG_TAGS if log.parent.name == "execution_agents" else CONVERSATION_TAGS
            if tag not in allowed:
                problems.append(f"{rel}:{n}: unexpected tag <{tag}>")
            if not TIMESTAMP_RE.match(ts):
                problems.append(f"{rel}:{n}: bad/missing timestamp {ts!r}")

    # working memory consistency with the conversation log
    conv_path = state / "conversation" / "poke_conversation.log"
    wm_path = state / "conversation" / "poke_working_memory.log"
    if not conv_path.is_file():
        problems.append(f"missing {conv_path.relative_to(fixtures)}")
    if not wm_path.is_file() or wm_path.stat().st_size == 0:
        problems.append(f"missing or empty {wm_path.relative_to(fixtures)}")
    if conv_path.is_file() and wm_path.is_file() and wm_path.stat().st_size > 0:
        problems.extend(_validate_working_memory(conv_path, wm_path))

    if not (state / "timezone.txt").is_file():
        problems.append("state/timezone.txt missing (SPEC §1)")

    # forbidden files inside state/
    for name in ("roster.json", "cases.json"):
        for hit in state.rglob(name):
            problems.append(f"{hit.relative_to(fixtures)} must not be inside state/")

    # rosters
    rosters: Dict[int, List[str]] = {}
    for size in sizes:
        path = fixtures / "rosters" / f"roster_{size}.json"
        if not path.is_file():
            problems.append(f"missing rosters/roster_{size}.json")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"rosters/roster_{size}.json: invalid JSON: {exc}")
            continue
        if not isinstance(data, list) or not all(isinstance(x, str) and x.strip() for x in data):
            problems.append(f"rosters/roster_{size}.json: must be a JSON list of non-empty strings")
            continue
        if len(set(data)) != len(data):
            dupes = sorted({x for x in data if data.count(x) > 1})
            problems.append(f"rosters/roster_{size}.json: duplicate names {dupes}")
        if len(data) != size:
            problems.append(f"rosters/roster_{size}.json: has {len(data)} names, expected {size}")
        rosters[size] = data

    present = [s for s in sizes if s in rosters]
    for small, big in zip(present, present[1:]):
        a, b = rosters[small], rosters[big]
        missing = [x for x in a if x not in set(b)]
        if missing:
            problems.append(f"roster_{small} not a subset of roster_{big}; missing {missing[:5]}")
        elif not _is_subsequence(a, b):
            problems.append(f"roster_{big} does not preserve the relative order of roster_{small}")

    # largest roster <-> agent logs: either no logs at all (name-only fixtures; the IA never reads
    # execution logs) or a full bijection. A partial set would let a log-reading solution tell gold
    # agents from distractors by log presence alone.
    if present:
        largest = rosters[present[-1]]
        agents_dir = state / "execution_agents"
        name_only = not (agents_dir.is_dir() and any(agents_dir.glob("*.log")))
        slug_owner: Dict[str, str] = {}
        for name in largest:
            fname = logfmt.agent_log_filename(name)
            if fname in slug_owner:
                problems.append(f"slug collision: {name!r} and {slug_owner[fname]!r} -> {fname}")
            slug_owner[fname] = name
            if not name_only and not (agents_dir / fname).is_file():
                problems.append(f"missing log for {name!r}: state/execution_agents/{fname}")
        for log in sorted(agents_dir.glob("*.log")) if agents_dir.is_dir() else []:
            if log.name not in slug_owner:
                problems.append(f"orphan log not in roster_{present[-1]}: state/execution_agents/{log.name}")

    # cases
    cases_path = fixtures / "cases.json"
    if not cases_path.is_file():
        problems.append("missing cases.json")
    else:
        try:
            cases = _load_cases(fixtures)
        except (ValidationError, ValueError) as exc:
            problems.append(f"cases.json invalid: {exc}")
        else:
            smallest = rosters.get(present[0]) if present else None
            if smallest is not None:
                for case in cases.cases:
                    for exp in case.expected:
                        if exp.gold != score.NEW and exp.gold not in smallest:
                            problems.append(
                                f"case {case.id}: gold {exp.gold!r} not in roster_{present[0]}"
                            )
    return problems


def _is_subsequence(small: List[str], big: List[str]) -> bool:
    it = iter(big)
    return all(any(x == y for y in it) for x in small)


def _validate_working_memory(conv_path: Path, wm_path: Path) -> List[str]:
    logfmt = _logfmt()
    from server.services.conversation.summarization.working_memory_log import WorkingMemoryLog

    problems: List[str] = []
    conv_lines = [l for l in conv_path.read_text(encoding="utf-8").splitlines(keepends=True) if l.strip()]
    conv_count = sum(1 for l in conv_lines if logfmt.parse_line(l) is not None)

    # load a copy: WorkingMemoryLog() may write to its path
    tmp = Path(tempfile.mkdtemp(prefix="wm-check-", dir=_DATA_DIR)) / "poke_working_memory.log"
    shutil.copyfile(wm_path, tmp)
    state = WorkingMemoryLog(tmp).load_summary_state()
    shutil.rmtree(tmp.parent, ignore_errors=True)

    if not (state.summary_text or "").strip():
        problems.append("working memory: empty conversation_summary")
    n_unsum = len(state.unsummarized_entries)
    want = conv_count - n_unsum - 1
    if state.last_index != want:
        problems.append(
            f"working memory: last_index={state.last_index}, expected {want} "
            f"(conversation entries {conv_count} - unsummarized {n_unsum} - 1)"
        )

    wm_lines = [l for l in wm_path.read_text(encoding="utf-8").splitlines(keepends=True) if l.strip()]
    head_tags = [(logfmt.parse_line(l) or ("?",))[0] for l in wm_lines[:2]]
    if head_tags != ["summary_info", "conversation_summary"]:
        problems.append(f"working memory: first two lines must be summary_info, conversation_summary (got {head_tags})")
    tail = wm_lines[2:]
    if any((logfmt.parse_line(l) or ("?",))[0] in {"summary_info", "conversation_summary"} for l in tail):
        problems.append("working memory: summary_info/conversation_summary appear more than once")
    conv_tail = conv_lines[len(conv_lines) - len(tail):] if tail else []
    if tail != conv_tail:
        bad = next((i for i, (a, b) in enumerate(zip(tail, conv_tail)) if a != b), min(len(tail), len(conv_tail)))
        problems.append(
            f"working memory: unsummarized entries are not byte-identical to the last {len(tail)} "
            f"conversation lines (first difference at unsummarized entry {bad})"
        )
    return problems


# --------------------------------------------------------------------------- per-size setup


def _prepare_size(fixtures: Path, size: int) -> List[str]:
    """Wipe the data dir, copy state/, install roster_N, drop logs of agents outside roster_N."""
    logfmt = _logfmt()
    data = _DATA_DIR
    assert data is not None and data != SERVER_DATA
    shutil.rmtree(data)
    data.mkdir(parents=True)
    shutil.copytree(fixtures / "state", data, dirs_exist_ok=True)
    roster = _load_roster(fixtures, size)
    agents_dir = data / "execution_agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    with open(agents_dir / "roster.json", "w") as fh:
        json.dump(roster, fh, indent=2)
    keep = {logfmt.agent_log_filename(n) for n in roster}
    for log in agents_dir.glob("*.log"):
        if log.name not in keep:
            log.unlink()
    return roster


def _build_prompt(case: Case) -> Tuple[str, List[Dict[str, Any]]]:
    ia_agent, _, _, get_working_memory_log, _ = _server()
    system_prompt = ia_agent.build_system_prompt()
    transcript = get_working_memory_log().render_transcript()
    messages = ia_agent.prepare_message_with_history(case.message, transcript, message_type="user")
    return system_prompt, messages


def _prompt_chars(system_prompt: str, messages: List[Dict[str, Any]]) -> int:
    return len(system_prompt) + sum(len(str(m.get("content") or "")) for m in messages)


# --------------------------------------------------------------------------- the routing loop


def _usage(response: Dict[str, Any]) -> Dict[str, Any]:
    usage = response.get("usage") or {}
    pdet = usage.get("prompt_tokens_details") or {}
    cdet = usage.get("completion_tokens_details") or {}
    choice = (response.get("choices") or [{}])[0]
    return {
        "prompt_tokens": usage.get("prompt_tokens"),
        "cached_tokens": pdet.get("cached_tokens"),
        "cache_write_tokens": pdet.get("cache_write_tokens", usage.get("cache_write_tokens")),
        "completion_tokens": usage.get("completion_tokens"),
        "reasoning_tokens": cdet.get("reasoning_tokens"),
        "cost": usage.get("cost"),
        "finish_reason": choice.get("native_finish_reason") or choice.get("finish_reason"),
        "provider": response.get("provider"),
        "response_model": response.get("model"),
    }


async def _route_case(case: Case, roster: List[str]) -> Dict[str, Any]:
    """One attempt: drive the production LLM loop, intercepting side-effecting tools."""
    _, ia_runtime, ia_tools, _, _ = _server()
    ToolResult = ia_tools.ToolResult
    runtime = ia_runtime.InteractionAgentRuntime()
    system_prompt, messages = _build_prompt(case)
    roster_set = set(roster)
    created: set = set()

    rec: Dict[str, Any] = {
        "prompt_chars": _prompt_chars(system_prompt, messages),
        "delegations": [],
        "other_tool_calls": [],
        "usage": [],
        "transcript": [],
        "iterations": 0,
    }

    for iteration in range(1, MAX_ITERATIONS + 1):
        response = await runtime._make_llm_call(system_prompt, messages)
        rec["iterations"] = iteration
        rec["usage"].append(_usage(response))
        assistant_message = runtime._extract_assistant_message(response)
        raw_tool_calls = assistant_message.get("tool_calls") or []
        parsed = runtime._parse_tool_calls(raw_tool_calls)

        # append the assistant entry exactly as InteractionAgentRuntime._run_interaction_loop does
        assistant_entry: Dict[str, Any] = {"role": "assistant", "content": assistant_message.get("content", "") or ""}
        if raw_tool_calls:
            assistant_entry["tool_calls"] = raw_tool_calls
        if assistant_message.get("reasoning_details"):
            assistant_entry["reasoning_details"] = assistant_message["reasoning_details"]
        messages.append(assistant_entry)

        reasoning = assistant_message.get("reasoning") or _reasoning_text(assistant_message.get("reasoning_details"))
        rec["transcript"].append(
            {
                "iteration": iteration,
                "content": assistant_message.get("content") or "",
                "reasoning": (reasoning[:2000] if isinstance(reasoning, str) else None),
                "tool_calls": [{"name": tc.name, "arguments": tc.arguments} for tc in parsed],
            }
        )

        if not parsed:
            break

        delegated = False
        for tc in parsed:
            args = tc.arguments
            if tc.name in INTERCEPTED:
                result = _stub_tool(tc, roster_set, created, ToolResult)
                if tc.name == "send_message_to_agent" and result.success:
                    name = args["agent_name"]
                    rec["delegations"].append(
                        {
                            "agent_name": name,
                            "instructions": args["instructions"],
                            "kind": "reuse" if name in roster_set else "create",
                            "iteration": iteration,
                        }
                    )
                    delegated = True
                else:
                    rec["other_tool_calls"].append(
                        {"iteration": iteration, "name": tc.name, "arguments": args, "intercepted": True,
                         "success": result.success}
                    )
            else:
                result = runtime._execute_tool(tc)  # real handler (future read-only tools)
                if inspect.isawaitable(result):
                    result = await result
                if not isinstance(result, ToolResult):
                    result = ToolResult(success=True, payload=result)
                rec["other_tool_calls"].append(
                    {"iteration": iteration, "name": tc.name, "arguments": args, "intercepted": False,
                     "success": result.success, "result": _truncate(result.payload)}
                )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.identifier or tc.name,
                    "content": runtime._format_tool_result(tc, result),
                }
            )
        if delegated:
            break
    return rec


def _reasoning_text(details: Any) -> Optional[str]:
    if not isinstance(details, list):
        return None
    parts = [d.get("text") or d.get("summary") for d in details if isinstance(d, dict)]
    text = "\n".join(p for p in parts if isinstance(p, str) and p)
    return text or None


def _stub_tool(tc, roster_set: set, created: set, ToolResult) -> Any:
    """Shape-compatible stand-ins for the side-effecting IA tools (never call the real ones)."""
    args = tc.arguments
    if "__invalid_arguments__" in args:
        return ToolResult(success=False, payload={"error": args["__invalid_arguments__"]})
    required = {
        "send_message_to_agent": ("agent_name", "instructions"),
        "send_message_to_user": ("message",),
        "send_draft": ("to", "subject", "body"),
        "wait": ("reason",),
    }[tc.name]
    missing = [k for k in required if not isinstance(args.get(k), str)]
    unexpected = [k for k in args if k not in required]
    if missing or unexpected:
        return ToolResult(success=False, payload={"error": f"Missing required arguments: {missing or unexpected}"})
    if tc.name == "send_message_to_agent":
        name = args["agent_name"]
        is_new = name not in roster_set and name not in created
        if is_new:
            created.add(name)
        return ToolResult(success=True, payload={"status": "submitted", "agent_name": name, "new_agent_created": is_new})
    if tc.name == "send_message_to_user":
        return ToolResult(success=True, payload={"status": "delivered"}, user_message=args["message"], recorded_reply=True)
    if tc.name == "send_draft":
        return ToolResult(
            success=True, payload={"status": "draft_recorded", "to": args["to"], "subject": args["subject"]},
            recorded_reply=True,
        )
    return ToolResult(success=True, payload={"status": "waiting", "reason": args["reason"]}, recorded_reply=True)


def _truncate(payload: Any, limit: int = 2000) -> Any:
    text = json.dumps(payload, default=str)
    return payload if len(text) <= limit else text[:limit] + "...[truncated]"


async def _run_case(case: Case, size: int, roster: List[str], sem: asyncio.Semaphore, base: Dict[str, Any]) -> Dict[str, Any]:
    *_, OpenRouterError = _server()
    async with sem:
        rec: Optional[Dict[str, Any]] = None
        errors: List[str] = []
        attempts = 0
        start = time.monotonic()
        for attempt in (1, 2):
            attempts = attempt
            start = time.monotonic()
            try:
                rec = await _route_case(case, roster)
                break
            except OpenRouterError as exc:
                errors.append(f"OpenRouterError: {exc}")
                if attempt == 2:
                    break
            except Exception as exc:  # record, don't abort the run
                errors.append(f"{type(exc).__name__}: {exc}")
                break
        latency = round(time.monotonic() - start, 2)

    expected = [e.model_dump() for e in case.expected]
    rec = rec or {"prompt_chars": None, "delegations": [], "other_tool_calls": [], "usage": [], "transcript": [], "iterations": 0}
    error = errors[-1] if rec["iterations"] == 0 and errors else None
    outcomes, extras = score.match_case(expected, rec["delegations"], error)
    costs = [u.get("cost") for u in rec["usage"] if isinstance(u.get("cost"), (int, float))]
    row = {
        **base,
        "size": size,
        "case_id": case.id,
        "category": case.category,
        "message": case.message,
        "expected": expected,
        "delegations": rec["delegations"],
        "other_tool_calls": rec["other_tool_calls"],
        "outcomes": outcomes,
        "extra_delegations": extras,
        "iterations": rec["iterations"],
        "usage": rec["usage"],
        "total_cost": round(sum(costs), 8) if costs else 0.0,
        "latency_s": latency,
        "attempts": attempts,
        "prompt_chars": rec["prompt_chars"],
        "error": error,
        "attempt_errors": errors,
        "transcript": rec["transcript"],
    }
    mark = "ERR" if error else " ".join(o["outcome"] for o in outcomes)
    print(f"  [{size}#{base.get('repeat', 0)}] {case.id}: {mark}  -> {[d['agent_name'] for d in rec['delegations']]}", flush=True)
    return row


# --------------------------------------------------------------------------- commands


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout
    except Exception:
        return ""


def _select_cases(fixtures: Path, wanted: Optional[str]) -> List[Case]:
    cases = _load_cases(fixtures).cases
    if not wanted:
        return cases
    ids = [c.strip() for c in wanted.split(",") if c.strip()]
    known = {c.id for c in cases}
    unknown = [i for i in ids if i not in known]
    if unknown:
        raise SystemExit(f"unknown case ids: {unknown}")
    return [c for c in cases if c.id in ids]


def cmd_validate(args) -> int:
    fixtures, sizes = _resolve(args.fixtures), _parse_sizes(args.sizes)
    problems = validate_fixtures(fixtures, sizes)
    if problems:
        print(f"INVALID fixtures at {fixtures} ({len(problems)} problems):", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"OK: fixtures at {fixtures} valid for sizes {sizes}")
    return 0


def cmd_run(args) -> int:
    fixtures, sizes = _resolve(args.fixtures), _parse_sizes(args.sizes)
    problems = validate_fixtures(fixtures, sizes)
    if problems:
        print("refusing to run, fixtures invalid (run `validate` for details):", file=sys.stderr)
        for p in problems[:20]:
            print(f"  - {p}", file=sys.stderr)
        return 1
    cases = _select_cases(fixtures, args.cases)
    if args.dry_run:
        return _dry_run(fixtures, sizes, cases)
    return asyncio.run(_live_run(fixtures, sizes, cases, args))


def _dry_run(fixtures: Path, sizes: List[int], cases: List[Case]) -> int:
    _, _, ia_tools, _, _ = _server()
    tools_chars = len(json.dumps(ia_tools.get_tool_schemas()))
    print(f"dry run: {len(cases)} cases, sizes {sizes}; tool schemas {tools_chars} chars (not in counts below)")
    print(f"{'size':>6} {'roster':>7} {'prompt chars':>13} {'est tok':>8} {'min chars':>10} {'max chars':>10}  representative")
    for size in sizes:
        roster = _prepare_size(fixtures, size)
        chars = []
        for case in cases:
            system_prompt, messages = _build_prompt(case)
            chars.append(_prompt_chars(system_prompt, messages))
        rep = chars[0]
        print(f"{size:>6} {len(roster):>7} {rep:>13,} {rep // 4:>8,} {min(chars):>10,} {max(chars):>10,}  {cases[0].id}")
    return 0


async def _live_run(fixtures: Path, sizes: List[int], cases: List[Case], args) -> int:
    _, ia_runtime, ia_tools, _, _ = _server()
    from server.config import get_settings

    settings = get_settings()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = _resolve(args.out) if args.out else REPO_ROOT / "evals" / "routing" / "results" / run_id
    out.mkdir(parents=True, exist_ok=True)
    commit = _git("rev-parse", "--short", "HEAD").strip()
    dirty_files = [l[3:] for l in _git("status", "--porcelain", "--untracked-files=no").splitlines() if l.strip()]
    base = {
        "run_id": run_id,
        "git_commit": commit,
        "git_dirty": bool(dirty_files),
        "model": settings.interaction_agent_model,
    }
    meta = {
        **base,
        "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_dirty_files": dirty_files,
        "fixtures": str(fixtures.relative_to(REPO_ROOT) if fixtures.is_relative_to(REPO_ROOT) else fixtures),
        "sizes": sizes,
        "cases": [c.id for c in cases],
        "concurrency": args.concurrency,
        "repeats": args.repeats,
        "max_iterations": MAX_ITERATIONS,
        "llm_max_tokens": settings.llm_max_tokens,
        "prompt_cache_enabled": settings.prompt_cache_enabled,
        "prompt_cache_ttl": settings.prompt_cache_ttl,
        "tools": [t["function"]["name"] for t in ia_tools.get_tool_schemas()],
        "data_dir": str(_DATA_DIR),
        "python": sys.version.split()[0],
    }
    print(f"run {run_id}: model {meta['model']}, commit {commit}{' (dirty)' if base['git_dirty'] else ''}, out {out}")

    sem = asyncio.Semaphore(max(1, args.concurrency))
    with (out / "decisions.jsonl").open("w", encoding="utf-8") as fh:
        for size in sizes:
            roster = _prepare_size(fixtures, size)
            print(f"size {size}: roster {len(roster)}", flush=True)
            rows = await asyncio.gather(
                *(_run_case(c, size, roster, sem, {**base, "repeat": r}) for r in range(args.repeats) for c in cases)
            )
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()

    meta["finished_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (out / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    report = score.write_reports(out)
    print()
    print((out / "report.md").read_text(encoding="utf-8").split("## Misses")[0].rstrip())
    print(f"\nreports: {out / 'report.md'}  total cost ${report['total_cost']:.4f}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m evals.routing.run", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--fixtures", default=DEFAULT_FIXTURES)
        p.add_argument("--sizes", default=DEFAULT_SIZES, help="comma-separated roster sizes")
        p.add_argument("--cases", default=None, help="comma-separated case ids (default: all)")
        p.add_argument("--concurrency", type=int, default=5)
        p.add_argument("--out", default=None, help="output dir (default evals/routing/results/<UTC ts>)")

    p_val = sub.add_parser("validate", help="check fixtures against SPEC")
    common(p_val)
    p_val.set_defaults(func=cmd_validate)
    p_run = sub.add_parser("run", help="run the eval (or --dry-run for prompt sizes only)")
    common(p_run)
    p_run.add_argument("--dry-run", action="store_true", help="no LLM calls; print prompt sizes per roster size")
    p_run.add_argument("--repeats", type=int, default=1, help="independent runs of every case at every size")
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    _init_data_dir()
    try:
        return args.func(args)
    finally:
        if _DATA_DIR is not None and _DATA_DIR != SERVER_DATA:
            shutil.rmtree(_DATA_DIR, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
