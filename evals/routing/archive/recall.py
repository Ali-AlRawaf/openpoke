"""Offline retrieval check: does agent search put each case's gold agent in the top K? No IA calls.

    python -m evals.routing.recall                       # queries = the cases' raw user messages
    python -m evals.routing.recall --from-run <run_dir>  # queries = what the IA actually searched for

For every case with an existing-agent gold, at every roster size above the search cutoff, rank the
roster's cards against the query exactly as ``server/services/execution/agent_search.py`` does
(production ``card_texts``, embedding model, prebuilt vectors) and report recall@K and the gold's
rank. It also compares ways of turning an agent's per-text similarities into one score:

    max         best single text (production)
    max+bonus   best + 0.25 x second best (rewards a second matching text)
    top2 mean   mean of the best two
    soft max    tau * log(mean(exp(s / tau))), tau = 0.05 (normalised by text count)

Only the queries are embedded (a few cents at most); card vectors come from
fixtures/embeddings/agent_embeddings.npz (``python -m evals.routing.generate embeddings``).
"""

from __future__ import annotations

import os
import tempfile

os.environ.setdefault("OPENPOKE_DATA_DIR", tempfile.mkdtemp(prefix="openpoke-recall-"))

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from evals.routing.score import query_is_about
from server.config import get_settings
from server.services.execution.agent_search import EmbeddingStore, _embed, card_texts, search_agent_cards
from server.services.execution.roster import AgentCard

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "evals" / "routing" / "fixtures"
SIZES = (25, 50, 100, 200, 400, 800, 1600)
KS = (1, 2, 3, 5, 10, 20)
NEW = "NEW"


def _max(s: np.ndarray) -> float:
    return float(s.max())


def _max_bonus(s: np.ndarray) -> float:
    top = np.sort(s)[::-1]
    return float(top[0] + 0.25 * (top[1] if len(top) > 1 else 0.0))


def _top2_mean(s: np.ndarray) -> float:
    return float(np.sort(s)[::-1][:2].mean())


def _soft_max(s: np.ndarray, tau: float = 0.05) -> float:
    m = s.max()
    return float(m + tau * np.log(np.mean(np.exp((s - m) / tau))))


AGGREGATORS: Dict[str, Callable[[np.ndarray], float]] = {
    "max": _max,
    "max+bonus": _max_bonus,
    "top2 mean": _top2_mean,
    "soft max": _soft_max,
}


def _load_cards(size: int) -> List[AgentCard]:
    entries = json.loads((FIXTURES / "rosters" / f"roster_{size}.json").read_text(encoding="utf-8"))
    return [AgentCard.model_validate(e) for e in entries]


def _queries(cases: List[Dict[str, Any]], from_run: Optional[Path]) -> Dict[Tuple[str, int], List[Tuple[str, frozenset]]]:
    """(case id, size) -> [(query, golds it doesn't count for)]. Raw message by default; with --from-run,
    every ranked search the IA ran. A gold the IA sent to directly before searching (known from the
    conversation) wasn't searched for in that run, so that run's queries don't count for it (e.g. in a
    two-task message the search is for the other task)."""
    out: Dict[Tuple[str, int], List[Tuple[str, frozenset]]] = {}
    if from_run is None:
        for case in cases:
            for size in SIZES:
                out[(case["id"], size)] = [(case["message"], frozenset())]
        return out
    with (from_run / "decisions.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            direct = frozenset(d["agent_name"] for d in row.get("delegations") or [] if not d.get("searched_before"))
            for search in row.get("searches") or []:
                if search.get("mode") == "search" and search.get("query"):
                    out.setdefault((row["case_id"], row["size"]), []).append((search["query"], direct))
    return out


async def run(from_run: Optional[Path], top_k: int) -> Dict[str, Any]:
    store = EmbeddingStore(FIXTURES / "embeddings" / "agent_embeddings.npz")
    cases = json.loads((FIXTURES / "cases.json").read_text(encoding="utf-8"))["cases"]
    queries = _queries(cases, from_run)
    unique = sorted({q for qs in queries.values() for q, _ in qs})
    query_vectors = dict(zip(unique, await _embed(unique))) if unique else {}

    rows = []
    for size in SIZES:
        if size <= top_k:
            continue  # search_agents returns the whole roster: retrieval can't miss
        cards = _load_cards(size)
        texts_per_card = [card_texts(c) for c in cards]
        all_texts = [t for texts in texts_per_card for t in texts]
        missing = store.missing(all_texts)
        if missing:
            raise SystemExit(f"{len(missing)} card texts have no vector: run `python -m evals.routing.generate embeddings`")
        matrix = store.rows(all_texts)
        bounds = np.cumsum([0] + [len(t) for t in texts_per_card])
        names = [c.name for c in cards]
        for case in cases:
            for exp in case["expected"]:
                if exp["gold"] == NEW:
                    continue
                gold = names.index(exp["gold"])
                for query, skip in queries.get((case["id"], size), []):
                    if exp["gold"] in skip or not query_is_about(query, exp, case["expected"]):
                        continue
                    sims = matrix @ query_vectors[query]
                    ranks = {}
                    for label, agg in AGGREGATORS.items():
                        scores = np.array([agg(sims[bounds[i]:bounds[i + 1]]) for i in range(len(cards))])
                        ranks[label] = int((scores > scores[gold]).sum()) + 1
                    rows.append({"size": size, "case_id": case["id"], "gold": exp["gold"], "query": query, "ranks": ranks})

    # the production function must agree with the "max" column (same code path, same vectors)
    probe = next((r for r in rows if r["size"] == max(SIZES)), None)
    if probe is not None:
        _install_store(store)
        top = await search_agent_cards(probe["query"], _load_cards(probe["size"]), top_k)
        in_top = probe["gold"] in [c.name for c in top]
        if in_top != (probe["ranks"]["max"] <= top_k):
            raise SystemExit("recall.py's max scoring disagrees with agent_search.search_agent_cards")
    return {"rows": rows, "top_k": top_k, "query_source": str(from_run) if from_run else "case messages",
            "embedding_model": get_settings().embedding_model, "embedding_dimensions": get_settings().embedding_dimensions}


def _install_store(store: EmbeddingStore) -> None:
    import server.services.execution.agent_search as agent_search

    agent_search._STORE = store


def render(result: Dict[str, Any]) -> str:
    rows, top_k = result["rows"], result["top_k"]
    sizes = sorted({r["size"] for r in rows})
    out = ["# Agent search recall\n",
           f"- **Queries:** {result['query_source']}",
           f"- **Embeddings:** {result['embedding_model']} ({result['embedding_dimensions']} dims)",
           f"- **Search returns:** top {top_k} (rosters of {top_k} or fewer return every agent)\n"]

    out.append(f"## Recall@{top_k} by scoring method\n")
    out.append("| method | " + " | ".join(str(s) for s in sizes) + " | all |")
    out.append("|" + "---|" * (len(sizes) + 2))
    for label in AGGREGATORS:
        cells = []
        for size in sizes + [None]:
            sel = [r for r in rows if size is None or r["size"] == size]
            cells.append(f"{sum(r['ranks'][label] <= top_k for r in sel) / len(sel):.0%}" if sel else "-")
        out.append(f"| {label}{' (production)' if label == 'max' else ''} | " + " | ".join(cells) + " |")
    out.append("")

    out.append("## Recall@K by scoring method (choosing K)\n")
    for label in AGGREGATORS:
        out.append(f"**{label}**{' (production)' if label == 'max' else ''}\n")
        out.append("| K | " + " | ".join(str(s) for s in sizes) + " | all |")
        out.append("|" + "---|" * (len(sizes) + 2))
        for k in KS:
            cells = []
            for size in sizes + [None]:
                sel = [r for r in rows if size is None or r["size"] == size]
                cells.append(f"{sum(r['ranks'][label] <= k for r in sel) / len(sel):.0%}" if sel else "-")
            out.append(f"| {k} | " + " | ".join(cells) + " |")
        out.append("")
    out.append("## Worst gold rank per size (how deep search must go to find every gold)\n")
    out.append("| method | " + " | ".join(str(s) for s in sizes) + " |")
    out.append("|" + "---|" * (len(sizes) + 1))
    for label in AGGREGATORS:
        cells = [str(max((r["ranks"][label] for r in rows if r["size"] == size), default="-")) for size in sizes]
        out.append(f"| {label} | " + " | ".join(cells) + " |")
    out.append("")

    out.append("## Gold rank per case, production scoring (max)\n")
    out.append("| case | gold | " + " | ".join(str(s) for s in sizes) + " |")
    out.append("|" + "---|" * (len(sizes) + 2))
    keys = sorted({(r["case_id"], r["gold"]) for r in rows})
    for cid, gold in keys:
        cells = []
        for size in sizes:
            ranks = sorted(r["ranks"]["max"] for r in rows if r["case_id"] == cid and r["gold"] == gold and r["size"] == size)
            if not ranks:
                cells.append("-")
            else:
                worst = max(ranks)
                cell = str(ranks[0]) if len(ranks) == 1 else f"{ranks[len(ranks) // 2]} (worst {worst})"
                cells.append(f"**{cell}**" if worst > top_k else cell)
        out.append(f"| {cid} | {gold} | " + " | ".join(cells) + " |")
    out.append(f"\nBold: the gold fell outside the top {top_k} (for --from-run, the median rank across the IA's queries, "
               "and the worst).\n")
    return "\n".join(out)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--from-run", type=Path, default=None, help="use the IA's recorded search queries from this run dir")
    parser.add_argument("--out", type=Path, default=None, help="output dir (default evals/routing/results/recall_<UTC ts>)")
    args = parser.parse_args(argv)
    top_k = get_settings().agent_search_top_k
    result = asyncio.run(run(args.from_run, top_k))
    out = args.out or REPO_ROOT / "evals" / "routing" / "results" / f"recall_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "recall.json").write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    report = render(result)
    (out / "recall.md").write_text(report, encoding="utf-8")
    print(report)
    print(f"written to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
