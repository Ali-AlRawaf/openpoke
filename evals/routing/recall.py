"""Offline retrieval eval: where does agent search rank each case's gold agent and its traps? No IA calls.

    python -m evals.routing.recall                         # queries = the cases' raw user messages
    python -m evals.routing.recall --from-run results/<run>  # queries = what the IA actually searched for

For every task in every case, at every roster size, each query's agents are ranked exactly as
server/services/execution/agent_search.py ranks them (an agent scores its best-matching card text), and the
report shows:
  - recall@K of the gold agent, for a few K (is the production top-10 enough, and with how much margin?)
  - the worst gold rank per size
  - per case: the gold's rank, and how many of the case's traps reach the top 10 (are the traps real tests?)
Only the queries and any uncached card texts are embedded (a fraction of a cent).
"""

from __future__ import annotations

import os
import tempfile

os.environ.setdefault("OPENPOKE_DATA_DIR", tempfile.mkdtemp(prefix="openpoke-recall-"))

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

import server.services.execution.agent_search as agent_search
from server.config import get_settings
from server.services.execution.agent_search import EmbeddingStore, _embed, card_texts
from server.services.execution.roster import AgentCard

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
SIZES = (25, 50, 100, 200, 400, 800, 1600)
KS = (1, 3, 5, 10, 20)
CARD_FIELDS = ("name", "summary", "artifacts", "created_at", "last_active_at")

# --------------------------------------------------------------------------- which task a query is for

_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "about", "ask", "asking", "email", "draft", "send", "tell",
    "theo", "marchetti", "reply", "new", "not", "can", "will", "whether", "their", "his", "her", "she", "him",
    "they", "them", "you", "your", "into", "before", "after", "also", "any", "are", "was", "has", "have",
}


def _words(text: str) -> set:
    return {w for w in "".join(ch if ch.isalnum() else " " for ch in text.lower()).split()
            if len(w) > 2 and w not in _STOPWORDS}


def query_is_about(query: str, task: Dict[str, Any], expected: List[Dict[str, Any]]) -> bool:
    """In a multi-task case a query counts only for the task it shares the most words with: the IA searches per
    task, and 'Halcyon Chimney sweep booking' is not a search for Gabe's agent."""
    if len(expected) == 1:
        return True
    words = _words(query)
    overlap = [len(words & _words(f"{e['task']} {e['gold'] if e['gold'] != 'NEW' else ''}")) for e in expected]
    return overlap[expected.index(task)] == max(overlap) > 0


def _queries(cases: List[Dict[str, Any]], from_run: Optional[Path]) -> Dict[tuple, List[str]]:
    """(case id, size) -> queries: the raw message at every size, or every ranked search the IA ran in a run."""
    if from_run is None:
        return {(c["id"], s): [c["message"]] for c in cases for s in SIZES}
    out: Dict[tuple, List[str]] = {}
    for line in (from_run / "decisions.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        for search in row["searches"]:
            if search["mode"] == "search" and search["query"]:
                out.setdefault((row["case_id"], row["size"]), []).append(search["query"])
    return out


# --------------------------------------------------------------------------- ranking


def _ranks(cards: List[AgentCard], store: EmbeddingStore, query_vectors: np.ndarray) -> np.ndarray:
    """agents x queries matrix of ranks (1 = best), scoring each agent by its best card text, as production does."""
    texts = [card_texts(c) for c in cards]
    sims = store.rows([t for ts in texts for t in ts]) @ query_vectors.T  # card texts x queries
    starts = np.cumsum([0] + [len(ts) for ts in texts[:-1]])
    scores = np.maximum.reduceat(sims, starts, axis=0)  # agents x queries
    order = np.argsort(-scores, axis=0, kind="stable")
    ranks = np.empty_like(order)
    np.put_along_axis(ranks, order, np.arange(1, len(cards) + 1)[:, None], axis=0)
    return ranks


async def run(from_run: Optional[Path]) -> Dict[str, Any]:
    roster = json.loads((FIXTURES / "roster.json").read_text(encoding="utf-8"))
    cases = json.loads((FIXTURES / "cases.json").read_text(encoding="utf-8"))
    top_k = get_settings().agent_search_top_k
    queries = _queries(cases, from_run)
    unique = sorted({q for qs in queries.values() for q in qs})
    if not unique:
        raise SystemExit("no searches to rank")

    # the production store, on the fixtures cache; embeds (and caches) any card text it lacks
    store = EmbeddingStore(FIXTURES / "embeddings.npz")
    all_cards = [AgentCard(**{k: c[k] for k in CARD_FIELDS}) for c in roster]
    all_texts = [t for c in all_cards for t in card_texts(c)]
    missing = store.missing(all_texts)
    if missing:
        store.add(missing, await _embed(missing))
        store.save(keep=all_texts)
    query_vectors = np.concatenate([await _embed(unique[i:i + 256]) for i in range(0, len(unique), 256)])
    qindex = {q: i for i, q in enumerate(unique)}

    rows = []
    for size in SIZES:
        if size <= top_k:
            continue  # search_agents returns the whole roster: retrieval can't miss
        members = [i for i, c in enumerate(roster) if c["min_size"] <= size]
        cards = [all_cards[i] for i in members]
        position = {c.name: i for i, c in enumerate(cards)}
        ranks = _ranks(cards, store, query_vectors)
        for case in cases:
            for task in case["expected"]:
                traps = [t for t in task["traps"] if t in position]
                for query in queries.get((case["id"], size), []):
                    if not query_is_about(query, task, case["expected"]):
                        continue
                    column = ranks[:, qindex[query]]
                    rows.append({
                        "size": size, "case_id": case["id"], "gold": task["gold"], "query": query,
                        "gold_rank": int(column[position[task["gold"]]]) if task["gold"] in position else None,
                        "trap_ranks": {t: int(column[position[t]]) for t in traps},
                    })

    # this ranking must agree with the production search function (same vectors, same scoring)
    probe = next(r for r in reversed(rows) if r["gold_rank"] is not None)
    agent_search._STORE = store
    cards = [all_cards[i] for i, c in enumerate(roster) if c["min_size"] <= probe["size"]]
    top = [c.name for c in await agent_search.search_agent_cards(probe["query"], cards, top_k)]
    if (probe["gold"] in top) != (probe["gold_rank"] <= top_k):
        raise SystemExit("recall.py's ranking disagrees with agent_search.search_agent_cards")
    return {"query_source": str(from_run) if from_run else "case messages", "top_k": top_k,
            "embedding_model": get_settings().embedding_model, "rows": rows}


# --------------------------------------------------------------------------- report


def render(result: Dict[str, Any]) -> str:
    rows, top_k = result["rows"], result["top_k"]
    sizes = sorted({r["size"] for r in rows})
    gold_rows = [r for r in rows if r["gold_rank"] is not None]
    pct = lambda hits, n: f"{hits / n:.0%}" if n else "-"

    out = [
        "# Agent search recall",
        "",
        f"Queries: {result['query_source']}. Embeddings: {result['embedding_model']}. "
        f"Production search returns the top {top_k}. {len(rows)} query x task rankings.",
        "",
        "## Gold recall@K",
        "",
        "| K | " + " | ".join(str(s) for s in sizes) + " | all |",
        "|---:|" + "---:|" * (len(sizes) + 1),
    ]
    for k in KS:
        cells = [pct(sum(r["gold_rank"] <= k for r in gold_rows if r["size"] == s),
                     sum(1 for r in gold_rows if r["size"] == s)) for s in sizes]
        cells.append(pct(sum(r["gold_rank"] <= k for r in gold_rows), len(gold_rows)))
        out.append(f"| {k}{' (production)' if k == top_k else ''} | " + " | ".join(cells) + " |")
    out += ["", "Worst gold rank: " + ", ".join(
        f"{s}: {max((r['gold_rank'] for r in gold_rows if r['size'] == s), default='-')}" for s in sizes) + ".", ""]

    out += [
        "## By case",
        "",
        f"Each cell: the gold's median rank (worst in brackets when the queries disagree), then how many of the "
        f"task's traps present at that size reached the top {top_k} for at least one query. **Bold**: the gold "
        f"missed the top {top_k}. -: no ranked search for that case at that size (the IA sent to a known agent "
        f"directly, or the decision crashed).",
        "",
        "| Case | Gold | " + " | ".join(str(s) for s in sizes) + " |",
        "|---|---|" + "---|" * len(sizes),
    ]
    for key in sorted({(r["case_id"], r["gold"]) for r in rows}):
        cells = []
        for size in sizes:
            sel = [r for r in rows if (r["case_id"], r["gold"]) == key and r["size"] == size]
            if not sel:
                cells.append("-")
                continue
            traps = sel[0]["trap_ranks"].keys()
            shown = sum(any(r["trap_ranks"][t] <= top_k for r in sel) for t in traps)
            trap_cell = f"traps {shown}/{len(traps)}" if traps else "no traps"
            if key[1] == "NEW":
                cells.append(trap_cell)
                continue
            ranks = sorted(r["gold_rank"] for r in sel)
            gold = str(ranks[len(ranks) // 2]) + (f" ({ranks[-1]})" if ranks[-1] != ranks[len(ranks) // 2] else "")
            cells.append(f"{'**' + gold + '**' if ranks[-1] > top_k else gold} · {trap_cell}")
        out.append(f"| {key[0]} | {key[1]} | " + " | ".join(cells) + " |")
    return "\n".join(out) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--from-run", type=Path, help="rank the queries the IA wrote in this results dir")
    parser.add_argument("--name", help="results/<name>; default recall_<timestamp>")
    args = parser.parse_args(argv)
    result = asyncio.run(run(args.from_run))
    out_dir = ROOT / "results" / (args.name or f"recall_{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    out_dir.mkdir(parents=True, exist_ok=False)
    (out_dir / "recall.json").write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    report = render(result)
    (out_dir / "recall.md").write_text(report, encoding="utf-8")
    print(report)
    print(f"written to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
