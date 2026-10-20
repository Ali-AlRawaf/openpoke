"""Score a routing-eval run: results/<run>/decisions.jsonl -> report.md + report.json.

    python -m evals.routing.score results/<run> [--baseline results/<earlier run>]

Each expected delegation in a case gets one outcome:
  correct       sent to the gold agent (or, for gold NEW, to an agent created in this turn)
  wrong_reuse   sent to a different existing agent
  false_create  created a new agent although the gold agent exists (fragmentation)
  false_reuse   gold is NEW but it sent to an existing agent
  missed        nothing was sent for it
A decision passes when every expected delegation is correct.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

FIXTURES = Path(__file__).resolve().parent / "fixtures"
OUTCOMES = ["correct", "wrong_reuse", "false_create", "false_reuse", "missed"]


# --------------------------------------------------------------------------- outcomes


def outcomes(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Match the expected delegations to the agent's sends: exact gold names first, then NEW expectations to
    agents created in this turn, then whatever is left, in order."""
    expected, sends = row["expected"], row["delegations"]
    left = list(range(len(sends)))
    chosen: List[Optional[int]] = [None] * len(expected)

    def take(i: int, test) -> None:
        j = next((j for j in left if test(sends[j])), None)
        if j is not None:
            chosen[i] = j
            left.remove(j)

    for i, e in enumerate(expected):
        if e["gold"] != "NEW":
            take(i, lambda s, g=e["gold"]: s["agent_name"] == g)
    for i, e in enumerate(expected):
        if chosen[i] is None and e["gold"] == "NEW":
            take(i, lambda s: s["kind"] == "create")
    for i in range(len(expected)):
        if chosen[i] is None:
            take(i, lambda s: True)

    result = []
    for e, j in zip(expected, chosen):
        send = sends[j] if j is not None else None
        if send is None:
            outcome = "missed"
        elif e["gold"] == "NEW":
            outcome = "correct" if send["kind"] == "create" else "false_reuse"
        elif send["agent_name"] == e["gold"]:
            outcome = "correct"
        else:
            outcome = "false_create" if send["kind"] == "create" else "wrong_reuse"
        result.append({"task": e["task"], "gold": e["gold"], "outcome": outcome,
                       "chosen": send["agent_name"] if send else None,
                       "chose_trap": bool(send and send["agent_name"] in e["traps"])})
    return result


def provider_error(row: Dict[str, Any]) -> bool:
    """The model request itself failed (e.g. rate or credit limits): infrastructure, not a routing outcome."""
    return bool(row.get("error")) and "OpenRouter request failed" in row["error"]


def passes(row: Dict[str, Any]) -> bool:
    return all(o["outcome"] == "correct" for o in outcomes(row))


# --------------------------------------------------------------------------- report


def _pct(x: Optional[float]) -> str:
    return "-" if x is None else f"{100 * x:.0f}%"


def _rate(hits: int, total: int) -> Optional[float]:
    return hits / total if total else None


def _mean(values: List[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def score_run(run_dir: Path) -> Dict[str, Any]:
    meta = json.loads((run_dir / "run_meta.json").read_text(encoding="utf-8"))
    all_rows = [json.loads(line) for line in (run_dir / "decisions.jsonl").read_text(encoding="utf-8").splitlines() if line]
    rows = [r for r in all_rows if not provider_error(r)]  # decisions that crashed on the provider aren't scored
    min_size = {c["name"]: c["min_size"] for c in json.loads((FIXTURES / "roster.json").read_text(encoding="utf-8"))}
    sizes = sorted({r["size"] for r in rows})
    case_ids = [c for c in meta["cases"] if any(r["case_id"] == c for r in rows)]
    group_of = {r["case_id"]: r["group"] for r in rows}
    groups = list(dict.fromkeys(group_of[c] for c in case_ids))

    per_size = []
    failures = []
    trap_exposure: Dict[str, List[int]] = defaultdict(lambda: [0, 0])  # case@largest size -> [shown, searched]
    for size in sizes:
        at = [r for r in rows if r["size"] == size]
        counts: Counter = Counter()
        searched = gold_found = gold_searched = traps_shown = traps_searched = trap_picks = 0
        for r in at:
            returned = {n for s in r["searches"] for n in s["returned"]}
            if r["searches"]:
                searched += 1
            for e, o in zip(r["expected"], outcomes(r)):
                counts[o["outcome"]] += 1
                trap_picks += o["chose_trap"]
                if o["outcome"] != "correct":
                    failures.append({"case_id": r["case_id"], "size": size, "repeat": r["repeat"], **o,
                                     "queries": [s["query"] for s in r["searches"]], "error": r.get("error")})
                # which search served which task is unknowable in a multi-task message, so search coverage
                # counts single-task cases only
                if not r["searches"] or len(r["expected"]) > 1:
                    continue
                if e["gold"] != "NEW":
                    gold_searched += 1
                    gold_found += e["gold"] in returned
                present = [t for t in e["traps"] if min_size.get(t, 10**9) <= size]
                if present:
                    traps_searched += 1
                    shown = bool(returned & set(present))
                    traps_shown += shown
                    if size == sizes[-1]:
                        trap_exposure[r["case_id"]][0] += shown
                        trap_exposure[r["case_id"]][1] += 1
        total = sum(counts.values())
        per_size.append({
            "size": size, "decisions": len(at), "accuracy": _rate(counts["correct"], total),
            **{k: counts[k] for k in OUTCOMES[1:]},
            "trap_picks": trap_picks,
            "searched": _rate(searched, len(at)),
            "gold_in_results": _rate(gold_found, gold_searched),
            "traps_shown": _rate(traps_shown, traps_searched),
            "llm_calls": _mean([len(r["llm_calls"]) for r in at]),
            "cost": _mean([r["cost"] for r in at]),
            "latency_s": _mean([r["latency_s"] for r in at]),
            "errors": sum(1 for r in at if r.get("error")),
            "provider_errors": sum(1 for r in all_rows if r["size"] == size and provider_error(r)),
        })

    def pass_rate(selected: List[Dict[str, Any]]) -> Optional[float]:
        return _rate(sum(passes(r) for r in selected), len(selected))

    group_rates = {g: {s: pass_rate([r for r in rows if r["size"] == s and r["group"] == g]) for s in sizes}
                   for g in groups}
    matrix = {c: {s: [sum(passes(r) for r in rows if r["case_id"] == c and r["size"] == s),
                      sum(1 for r in rows if r["case_id"] == c and r["size"] == s)] for s in sizes} for c in case_ids}
    return {"meta": meta, "sizes": sizes, "per_size": per_size, "groups": group_rates, "matrix": matrix,
            "trap_exposure": {c: v for c, v in trap_exposure.items()}, "failures": failures,
            "decisions": len(rows), "provider_errors": len(all_rows) - len(rows),
            "total_cost": round(sum(r["cost"] for r in all_rows), 4),
            "pass_rate": pass_rate(rows)}


def compare(report: Dict[str, Any], baseline: Dict[str, Any]) -> Dict[str, Any]:
    shared = [s for s in report["sizes"] if s in baseline["sizes"]]
    acc = {p["size"]: p["accuracy"] for p in report["per_size"]}
    base_acc = {p["size"]: p["accuracy"] for p in baseline["per_size"]}
    return {"baseline": baseline["meta"]["name"], "sizes": shared,
            "accuracy": {s: [base_acc[s], acc[s]] for s in shared},
            "groups": {g: {s: [baseline["groups"].get(g, {}).get(s), rates.get(s)] for s in shared}
                       for g, rates in report["groups"].items()}}


def render(report: Dict[str, Any]) -> str:
    meta, sizes = report["meta"], report["sizes"]
    lines = [
        f"# Routing eval: {meta['name']}",
        "",
        f"{report['decisions']} decisions ({len(meta['cases'])} cases x sizes {sizes} x {meta['repeats']} repeats), "
        f"model `{meta['model']}`, commit `{meta['git_commit']}`{' (dirty)' if meta['git_dirty'] else ''}, "
        f"prompt `{meta['prompt_hash']}`, fixtures `{meta['fixtures_hash']}`. Total cost ${report['total_cost']:.2f}.",
        "",
        f"**Pass rate: {_pct(report['pass_rate'])}** (a decision passes when every expected delegation is correct).",
        "",
        *([f"**Warning:** {report['provider_errors']} decisions failed on model-provider errors even after retries "
           "and are left out of every number below.", ""] if report["provider_errors"] else []),
        "## By roster size",
        "",
        "| Size | Accuracy | Wrong reuse | False create | False reuse | Missed | Picked a trap | Searched | Gold in results | Traps shown | Calls | Cost | Latency |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for p in report["per_size"]:
        lines.append(
            f"| {p['size']} | {_pct(p['accuracy'])} | {p['wrong_reuse']} | {p['false_create']} | {p['false_reuse']} | "
            f"{p['missed']} | {p['trap_picks']} | {_pct(p['searched'])} | {_pct(p['gold_in_results'])} | "
            f"{_pct(p['traps_shown'])} | {p['llm_calls']:.1f} | ${p['cost']:.4f} | {p['latency_s']:.1f}s |")
    lines += [
        "",
        "*Searched*: decisions with at least one `search_agents` call. *Gold in results* and *traps shown*: of those "
        "(single-task cases only), how often the gold agent / at least one of the case's traps present at that size "
        "came back.",
        "",
        "## By case group (pass rate)",
        "",
        "| Group | " + " | ".join(str(s) for s in sizes) + " |",
        "|---|" + "---:|" * len(sizes),
    ]
    for group, rates in report["groups"].items():
        lines.append(f"| {group} | " + " | ".join(_pct(rates[s]) for s in sizes) + " |")
    largest = sizes[-1]
    lines += ["", "## By case (passes / runs)", "",
              "| Case | " + " | ".join(str(s) for s in sizes) + f" | Traps shown at {largest} |",
              "|---|" + "---:|" * (len(sizes) + 1)]
    for case, cells in report["matrix"].items():
        shown, searched = report["trap_exposure"].get(case, [0, 0])
        lines.append(f"| {case} | " + " | ".join(f"{p}/{n}" for p, n in (cells[s] for s in sizes))
                     + f" | {f'{shown}/{searched}' if searched else '-'} |")
    if "comparison" in report:
        cmp = report["comparison"]
        lines += ["", f"## Compared with {cmp['baseline']}", "",
                  "| | " + " | ".join(str(s) for s in cmp["sizes"]) + " |", "|---|" + "---:|" * len(cmp["sizes"]),
                  "| Accuracy | " + " | ".join(f"{_pct(a)} → {_pct(b)}" for a, b in (cmp["accuracy"][s] for s in cmp["sizes"])) + " |"]
        for group, rates in cmp["groups"].items():
            lines.append(f"| {group} | " + " | ".join(f"{_pct(a)} → {_pct(b)}" for a, b in (rates[s] for s in cmp["sizes"])) + " |")
    lines += ["", "## Failures", ""]
    if not report["failures"]:
        lines.append("None.")
    for f in report["failures"]:
        trap = " (a trap)" if f["chose_trap"] else ""
        lines.append(f"- **{f['case_id']}** size {f['size']} #{f['repeat']}: {f['outcome']}. Gold `{f['gold']}`, "
                     f"chose `{f['chosen']}`{trap}. Task: {f['task']}."
                     + (f" Queries: {'; '.join(f['queries'])}." if f["queries"] else " No search.")
                     + (f" Error: {f['error']}" if f["error"] else ""))
    return "\n".join(lines) + "\n"


def write_report(run_dir: Path, baseline_dir: Optional[Path] = None) -> Dict[str, Any]:
    report = score_run(run_dir)
    if baseline_dir:
        report["comparison"] = compare(report, score_run(baseline_dir))
    report["summary_line"] = (f"pass rate {_pct(report['pass_rate'])} over {report['decisions']} decisions; "
                              "accuracy by size: " + ", ".join(f"{p['size']}: {_pct(p['accuracy'])}" for p in report["per_size"]))
    (run_dir / "report.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    (run_dir / "report.md").write_text(render(report), encoding="utf-8")
    return report


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args(argv)
    print(write_report(args.run_dir, args.baseline)["summary_line"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
