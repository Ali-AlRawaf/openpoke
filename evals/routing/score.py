"""Score routing-eval decisions and write report.md + report.json.

Importable (``match_case``, ``score_run``) and runnable:

    python -m evals.routing.score evals/routing/results/<run_id>

Stdlib only; never imports ``server`` (classification is recorded per delegation by run.py
as ``kind`` = "reuse" | "create", i.e. exact match against roster_N or not).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple

NEW = "NEW"
OUTCOMES = ["correct", "wrong_reuse", "false_create", "false_reuse", "missed", "error"]
CHECK = "\u2713"


# --------------------------------------------------------------------------- matching


def match_case(
    expected: List[Dict[str, Any]], delegations: List[Dict[str, Any]], error: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Match expected entries to delegations.

    Returns (outcomes, extra_delegations). ``outcomes`` has one dict per expected entry, in
    order: {task, gold, outcome, chosen, chosen_kind, instructions}.
    """
    remaining = list(range(len(delegations)))
    assigned: Dict[int, Tuple[str, Optional[int]]] = {}

    if error and not delegations:
        outcomes = [
            _outcome(e, "error", None) for e in expected
        ]
        return outcomes, []

    # 1. exact-name matches for existing-gold entries (unambiguous)
    for i, exp in enumerate(expected):
        if exp["gold"] != NEW:
            for pos, idx in enumerate(remaining):
                if delegations[idx].get("agent_name") == exp["gold"]:
                    remaining.pop(pos)
                    assigned[i] = ("correct", idx)
                    break

    # 2. pair the rest by content (which delegation is about which task), not by order: in a
    #    two-task case where both delegations created agents, order would mismatch them
    open_tasks = [i for i in range(len(expected)) if i not in assigned]
    pairs = sorted(
        ((_overlap(expected[i], delegations[idx]), -i, -idx, i, idx) for i in open_tasks for idx in remaining),
        reverse=True,
    )
    for _, _, _, i, idx in pairs:
        if i in assigned or idx not in remaining:
            continue
        remaining.remove(idx)
        assigned[i] = (_code(expected[i]["gold"], delegations[idx].get("kind")), idx)
    for i in open_tasks:
        assigned.setdefault(i, ("missed", None))

    outcomes = []
    for i, exp in enumerate(expected):
        code, idx = assigned[i]
        outcomes.append(_outcome(exp, code, delegations[idx] if idx is not None else None))
    extras = [delegations[idx] for idx in remaining]
    return outcomes, extras


def _code(gold: str, kind: Optional[str]) -> str:
    """Outcome for a delegation paired with an expected task whose gold it doesn't name exactly."""
    if gold == NEW:
        return "correct" if kind == "create" else "false_reuse"
    return "wrong_reuse" if kind == "reuse" else "false_create"


_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "about", "ask", "asking", "email", "draft", "send", "tell",
    "theo", "marchetti", "reply", "new", "not", "can", "will", "whether", "their", "his", "her", "she", "him",
    "they", "them", "you", "your", "into", "before", "after", "also", "any", "are", "was", "has", "have",
}


def _words(text: str) -> set:
    return {w for w in "".join(ch if ch.isalnum() else " " for ch in text.lower()).split() if len(w) > 2 and w not in _STOPWORDS}


def _overlap(exp: Dict[str, Any], deleg: Dict[str, Any]) -> int:
    """Content words shared by an expected task (+ gold name) and a delegation (name + instructions)."""
    gold = exp["gold"] if exp["gold"] != NEW else ""
    task_words = _words(f"{exp.get('task') or ''} {gold}")
    return len(task_words & _words(f"{deleg.get('agent_name') or ''} {deleg.get('instructions') or ''}"))


def _outcome(exp: Dict[str, Any], code: str, deleg: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "task": exp.get("task"),
        "gold": exp["gold"],
        "outcome": code,
        "chosen": deleg.get("agent_name") if deleg else None,
        "chosen_kind": deleg.get("kind") if deleg else None,
        "instructions": deleg.get("instructions") if deleg else None,
    }


# --------------------------------------------------------------------------- aggregation


def load_run(run_dir: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    meta_path = run_dir / "run_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    rows = []
    with (run_dir / "decisions.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return meta, rows


def _mean(values: List[float]) -> Optional[float]:
    vals = [v for v in values if v is not None]
    return round(mean(vals), 1) if vals else None


def _usage_field(call: Dict[str, Any], key: str) -> Optional[float]:
    value = call.get(key)
    return value if isinstance(value, (int, float)) else None


def score_run(meta: Dict[str, Any], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Recompute outcomes from recorded delegations and aggregate."""
    for row in rows:
        outcomes, extras = match_case(row.get("expected") or [], row.get("delegations") or [], row.get("error"))
        row["outcomes"] = outcomes
        row["extra_delegations"] = extras

    sizes = sorted({row["size"] for row in rows})
    case_ids: List[str] = []
    for row in rows:
        if row["case_id"] not in case_ids:
            case_ids.append(row["case_id"])

    per_size = []
    for size in sizes:
        srows = [r for r in rows if r["size"] == size]
        counts = Counter(o["outcome"] for r in srows for o in r["outcomes"])
        n_expected = sum(len(r["outcomes"]) for r in srows)
        calls = [c for r in srows for c in (r.get("usage") or [])]
        per_size.append(
            {
                "size": size,
                "cases": len(srows),
                "expected_entries": n_expected,
                "accuracy": round(counts["correct"] / n_expected, 3) if n_expected else None,
                "outcomes": {k: counts.get(k, 0) for k in OUTCOMES},
                "extra_delegations": sum(len(r["extra_delegations"]) for r in srows),
                "errors": sum(1 for r in srows if r.get("error")),
                "llm_calls": len(calls),
                "mean_prompt_tokens": _mean([_usage_field(c, "prompt_tokens") for c in calls]),
                "mean_cached_tokens": _mean([_usage_field(c, "cached_tokens") for c in calls]),
                "mean_completion_tokens": _mean([_usage_field(c, "completion_tokens") for c in calls]),
                "mean_reasoning_tokens": _mean([_usage_field(c, "reasoning_tokens") for c in calls]),
                "mean_prompt_chars": _mean([r.get("prompt_chars") for r in srows]),
                "total_cost": round(sum(r.get("total_cost") or 0.0 for r in srows), 6),
                "mean_latency_s": _mean([r.get("latency_s") for r in srows]),
            }
        )

    by_key: Dict[Tuple[str, int], List[Dict[str, Any]]] = {}
    for r in rows:
        by_key.setdefault((r["case_id"], r["size"]), []).append(r)
    matrix = []
    for cid in case_ids:
        cells = {}
        passes = []
        rates = {}
        for size in sizes:
            reps = by_key.get((cid, size)) or []
            if not reps:
                cells[str(size)] = None
                passes.append(None)
                continue
            ok_count = 0
            failures: Counter = Counter()
            for row in reps:
                codes = [o["outcome"] for o in row["outcomes"]]
                if all(c == "correct" for c in codes) and not row["extra_delegations"]:
                    ok_count += 1
                failures.update(c for c in codes if c != "correct")
                if row["extra_delegations"]:
                    failures["extra"] += len(row["extra_delegations"])
            if len(reps) == 1:
                row = reps[0]
                cell = "+".join(CHECK if o["outcome"] == "correct" else o["outcome"] for o in row["outcomes"])
                if row["extra_delegations"]:
                    cell += f" (+{len(row['extra_delegations'])} extra)"
            else:
                cell = f"{ok_count}/{len(reps)}"
                if failures:
                    cell += " (" + ", ".join(f"{code}×{n}" for code, n in failures.most_common()) + ")"
            cells[str(size)] = cell
            rates[str(size)] = round(ok_count / len(reps), 3)
            passes.append(ok_count / len(reps) > 0.5)  # majority pass
        category = next((r.get("category") for r in rows if r["case_id"] == cid), None)
        matrix.append({"case_id": cid, "category": category, "cells": cells, "pass_rates": rates, "pattern": _pattern(passes)})

    misses = []
    for row in sorted(rows, key=lambda r: (case_ids.index(r["case_id"]), r["size"], r.get("repeat", 0))):
        for o in row["outcomes"]:
            if o["outcome"] != "correct":
                misses.append(
                    {
                        "case_id": row["case_id"],
                        "size": row["size"],
                        "repeat": row.get("repeat", 0),
                        "outcome": o["outcome"],
                        "task": o["task"],
                        "gold": o["gold"],
                        "chosen": o["chosen"],
                        "instructions": o["instructions"],
                        "all_delegations": [d.get("agent_name") for d in row.get("delegations") or []],
                        "case_pairing": [
                            {"task": x["task"], "gold": x["gold"], "outcome": x["outcome"], "chosen": x["chosen"]}
                            for x in row["outcomes"]
                        ],
                        "error": row.get("error"),
                    }
                )
        for d in row["extra_delegations"]:
            misses.append(
                {
                    "case_id": row["case_id"],
                    "size": row["size"],
                    "repeat": row.get("repeat", 0),
                    "outcome": "extra_delegation",
                    "task": None,
                    "gold": None,
                    "chosen": d.get("agent_name"),
                    "instructions": d.get("instructions"),
                    "all_delegations": [x.get("agent_name") for x in row.get("delegations") or []],
                    "error": row.get("error"),
                }
            )

    total_cost = round(sum(r.get("total_cost") or 0.0 for r in rows), 6)
    return {
        "meta": meta,
        "sizes": sizes,
        "total_cost": total_cost,
        "per_size": per_size,
        "matrix": matrix,
        "misses": misses,
        "rows": [
            {k: r.get(k) for k in ("size", "repeat", "case_id", "category", "outcomes", "extra_delegations", "error")}
            for r in rows
        ],
    }


def _pattern(passes: List[Optional[bool]]) -> str:
    known = [p for p in passes if p is not None]
    if not known:
        return "no data"
    if all(known):
        return "pass at every size"
    if not any(known):
        return "fails at every size (starvation?)"
    first_fail = known.index(False)
    if all(known[:first_fail]) and not any(known[first_fail:]):
        return "passes small, fails large (overload?)"
    return "mixed"


# --------------------------------------------------------------------------- rendering


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.3f}" if value < 1 else f"{value:,.1f}"
    return str(value)


def _md_cell(text: Any) -> str:
    return str(text if text is not None else "-").replace("|", "\\|").replace("\n", " ")


def render_markdown(report: Dict[str, Any]) -> str:
    meta = report["meta"]
    out: List[str] = []
    out.append(f"# Routing eval report: {meta.get('run_id', '?')}\n")
    commit = meta.get("git_commit", "?") + (" (dirty)" if meta.get("git_dirty") else "")
    out.append(f"- **Model:** {meta.get('model', '?')}")
    out.append(f"- **Commit:** {commit}")
    out.append(f"- **Sizes:** {', '.join(str(s) for s in report['sizes'])}")
    out.append(f"- **Cases:** {len(report['matrix'])}")
    out.append(f"- **Fixtures:** {meta.get('fixtures', '?')}")
    out.append(f"- **Total cost:** ${report['total_cost']:.4f}")
    if meta.get("started_at"):
        out.append(f"- **Started:** {meta['started_at']}  **Finished:** {meta.get('finished_at', '?')}")
    out.append("")

    out.append("## Per size\n")
    header = [
        "size", "accuracy", "correct", "wrong_reuse", "false_create", "false_reuse", "missed",
        "error", "extra", "calls", "mean prompt tok", "mean cached tok", "mean completion tok",
        "mean reasoning tok", "cost $", "mean latency s",
    ]
    out.append("| " + " | ".join(header) + " |")
    out.append("|" + "---|" * len(header))
    for s in report["per_size"]:
        o = s["outcomes"]
        acc = f"{s['accuracy']:.0%} ({o['correct']}/{s['expected_entries']})" if s["accuracy"] is not None else "-"
        cells = [
            s["size"], acc, o["correct"], o["wrong_reuse"], o["false_create"], o["false_reuse"],
            o["missed"], o["error"], s["extra_delegations"], s["llm_calls"],
            _fmt(s["mean_prompt_tokens"]), _fmt(s["mean_cached_tokens"]),
            _fmt(s["mean_completion_tokens"]), _fmt(s["mean_reasoning_tokens"]),
            f"{s['total_cost']:.4f}", _fmt(s["mean_latency_s"]),
        ]
        out.append("| " + " | ".join(_md_cell(c) for c in cells) + " |")
    out.append("\nAccuracy pools every repeat. Token columns are means per LLM call; latency is per case run.\n")

    out.append("## Case x size\n")
    sizes = [str(s) for s in report["sizes"]]
    out.append("| case | category | " + " | ".join(sizes) + " | pattern |")
    out.append("|" + "---|" * (len(sizes) + 3))
    for m in report["matrix"]:
        cells = [m["cells"].get(s) or "-" for s in sizes]
        out.append(
            f"| {_md_cell(m['case_id'])} | {_md_cell(m['category'])} | "
            + " | ".join(_md_cell(c) for c in cells)
            + f" | {_md_cell(m['pattern'])} |"
        )
    out.append("")

    out.append("## Misses\n")
    if not report["misses"]:
        out.append("None.\n")
    for miss in report["misses"]:
        out.append(f"### {miss['case_id']} @ {miss['size']} #{miss.get('repeat', 0)}: `{miss['outcome']}`\n")
        if miss["task"]:
            out.append(f"- **Task:** {miss['task']}")
        if miss["gold"] is not None:
            out.append(f"- **Gold:** `{miss['gold']}`")
        out.append(f"- **Chosen:** `{miss['chosen']}`" if miss["chosen"] else "- **Chosen:** (none)")
        out.append(f"- **All delegations:** {', '.join(f'`{n}`' for n in miss['all_delegations']) or '(none)'}")
        if len(miss.get("case_pairing") or []) > 1:
            out.append("- **Every task in this case:**")
            for x in miss["case_pairing"]:
                chosen = f"`{x['chosen']}`" if x["chosen"] else "(none)"
                out.append(f"  - {x['task']}: gold `{x['gold']}`, chosen {chosen} → `{x['outcome']}`")
        if miss.get("error"):
            out.append(f"- **Error:** {miss['error']}")
        if miss["instructions"]:
            quoted = "\n".join("> " + line for line in str(miss["instructions"]).splitlines())
            out.append(f"- **Instructions:**\n\n{quoted}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def write_reports(run_dir: Path) -> Dict[str, Any]:
    meta, rows = load_run(run_dir)
    report = score_run(meta, rows)
    (run_dir / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (run_dir / "report.md").write_text(render_markdown(report), encoding="utf-8")
    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Score a routing-eval run directory.")
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args(argv)
    if not (args.run_dir / "decisions.jsonl").exists():
        print(f"error: {args.run_dir}/decisions.jsonl not found", file=sys.stderr)
        return 2
    write_reports(args.run_dir)
    print((args.run_dir / "report.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
