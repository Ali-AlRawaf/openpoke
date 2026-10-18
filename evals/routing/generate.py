"""One-off LLM generation for the routing-eval fixtures. Outputs are FROZEN; evals never run this.

Stages (each writes JSON under fixtures/generated/, and later stages read earlier outputs):

    python -m evals.routing.generate names     # ~375 distractor agent names + briefs
    python -m evals.routing.generate logs      # distractor request content (compact specs)
    python -m evals.routing.generate filler    # older-window chit-chat + which distractor episodes appear
    python -m evals.routing.generate summary   # real summarizer path over entries 0-299 (3 passes)

After `logs` or `filler` changes, rerun `summary`, then `python -m evals.routing.build_fixtures --check`.
LLM: server.openrouter_client.request_chat_completion with the server's configured models.
Spend is accumulated in fixtures/generated/cost.json.
"""

from __future__ import annotations

import os
import tempfile

os.environ.setdefault("OPENPOKE_DATA_DIR", tempfile.mkdtemp(prefix="openpoke-generate-"))

import argparse
import asyncio
import json
import random
import re
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from evals.routing import build_fixtures as bf
from evals.routing.logfmt import agent_log_filename, format_line, parse_line
from server.config import get_settings
from server.openrouter_client import request_chat_completion
from server.services.conversation.summarization.prompt_builder import build_summarization_prompt
from server.services.conversation.summarization.state import LogEntry

GEN = bf.GENERATED
NAMES_PATH = GEN / "distractor_names.json"
DISTRACTORS_PATH = GEN / "distractors.json"
FILLER_PATH = GEN / "older_filler.json"
SUMMARY_PATH = GEN / "summary.json"
COST_PATH = GEN / "cost.json"
N_DISTRACTORS = 375

PERSONA = (
    "The user is Theo Marchetti (theo@northfoldstudio.ca), 34, co-founder and head of product at Northfold Studio, a 12-person product design "
    "studio in Toronto. He lives in Leslieville, Toronto with his fiance Jules, owns a house, plays rec soccer, runs, cooks, travels a bit. "
    "Timezone America/Toronto. He texts his assistant 'Poke' in lowercase, terse, casual ('u', 'pls', 'lol'). Poke (the interaction agent) delegates "
    "tasks to execution agents that have Gmail tools; agent names are short Title Case labels the interaction agent invents, e.g. "
    "'Email to Ali Japan Itinerary', 'Recent Email Lookup', 'Inbox Summary', 'Car Insurance Renewal Reminder', 'Email to Nadia Ski Trip', "
    "'Parking Ticket Appeal', 'Grocery Delivery Order Status'."
)

FICTION_RULES = (
    "All people, companies, shops and email domains must be INVENTED (no real brands, banks, airlines, retailers, apps or celebrities). "
    "Use plausible made-up businesses (e.g. 'Fenwick & Pyle Hardware', 'Bluejay Mobile', 'Orchard Lane Grocers') with made-up domains (.ca/.com/.net), "
    "and personal addresses at the made-up provider quaymail.net (e.g. dana.okafor@quaymail.net). Real cities and neighbourhoods are fine. "
    "Never use these names or anything about them: " + ", ".join(sorted({p['first'] + (' ' + p['last'] if p['last'] else '') for p in bf.CORE_PEOPLE if p['first']}))
    + "; organisations: " + ", ".join(sorted({p['org'] for p in bf.CORE_PEOPLE if p['org'] and p['org'] != 'Northfold Studio'}))
    + ". Never mention Pantrywise, Northline Courier, Larkspur Outfitters, Telvio, Maplecrest or Riverdale Library. Do not use the first names Priya, Marco, Marcus, Gabe, Dmitri, Wendell, Celeste, Hana, Elaine, Noor, Tomasz, Harold, Rosa, Sofia, Leena, Adaeze or Jules for anyone. "
    "Avoid these topics entirely: weddings/engagements/photographers/venues, mortgages/rates, kitchen or bathroom renovations/contractors, "
    "chimneys/fireplaces, piano or music lessons, car tires/mechanics/oil changes, product roadmaps/sprints/demos/offsites/agendas, "
    "dentists, physio, gyms, book clubs, recruiters, fences/neighbours, cottages, standing desks, Montreal trips, save-the-dates, the hydro/electric bill, "
    "Sunday or weekly rundowns/briefs, soccer leagues, Jules' birthday, Theo's mom."
)

CATEGORIES: List[Tuple[str, int, str]] = [
    ("email_person", 82, "emailing a specific friend, relative (not mom), acquaintance, landlord-of-a-friend, tutor, coach, club organiser, vendor contact, "
                         "or work contact outside Northfold about one concrete thing. Name style 'Email to <FirstName> <Topic>' or '<FirstName> <Topic> Follow-up'"),
    ("lookup", 45, "finding a specific email/receipt/confirmation/document in the inbox (e.g. 'Warranty Receipt Search', 'Lease Copy Lookup', 'Recent Email Lookup')"),
    ("reminder", 45, "recurring or one-off reminders set as triggers (bills other than hydro, plant watering, recycling day, renew documents, take meds, "
                     "call someone, stretch, pay a friend back, etc.). Name style '<Thing> Reminder' or '<Thing> Daily Nudge'"),
    ("research", 25, "comparing options or digging info out of emails/newsletters (internet plans, quotes, school options for a nephew, charity receipts, event info)"),
    ("purchase", 40, "orders, deliveries, returns, refunds, warranty claims, price adjustments with made-up shops"),
    ("subscription", 25, "streaming/meal-kit/software/magazine/membership subscriptions: cancel, pause, downgrade, renewal notices (invented services)"),
    ("travel", 30, "trips other than Montreal: flights (invented airlines), trains, hotels, car rentals, travel insurance, visas, itineraries"),
    ("finance", 30, "credit card disputes, bank letters, investment statements, tax slips, charity donations, splitting costs with friends, parking tickets"),
    ("family_home", 30, "nieces/nephews/siblings/in-laws, house stuff (not renos or fences): appliance repair, cleaner, lawn care, pest control, insurance, utilities other than hydro"),
    ("admin_generic", 8, "generic inbox housekeeping agents ('Inbox Summary', 'Unread Email Check', 'Newsletter Unsubscribe Sweep', 'Spam Folder Check')"),
    ("work_misc", 15, "Northfold Studio admin that is NOT roadmaps/demos/offsites/hiring: client invoices, coworking space, software licenses, conference tickets, "
                      "office supplies, a client's contract question. Contacts outside Northfold use invented company domains"),
]

SEEDS: List[Dict[str, str]] = [
    {"name": "Inbox Summary", "category": "admin_generic", "brief": "User asked for a summary of unread emails from the last two days.", "counterpart": ""},
    {"name": "Unread Email Check", "category": "admin_generic", "brief": "User asked whether anything urgent was sitting unread.", "counterpart": ""},
    {"name": "Recent Email Lookup", "category": "lookup", "brief": "User asked to find a recent email from a coworking space about a key fob.", "counterpart": "Junction Commons Coworking, desk@junctioncommons.ca"},
    {"name": "Security Deposit Refund", "category": "finance", "brief": "Chasing the security deposit refund from Theo's old apartment landlord company.", "counterpart": "Pinecrest Rentals, leasing@pinecrestrentals.ca"},
    {"name": "Passport Renewal Appointment", "category": "travel", "brief": "Booking and confirming a passport renewal appointment at an invented passport service office.", "counterpart": "Passport Services Toronto East, appointments@ppt-east-booking.ca"},
    {"name": "Copper Kettle Catering Quote", "category": "work_misc", "brief": "Quote for catering Northfold's December holiday party.", "counterpart": "Copper Kettle Catering, events@copperkettlecatering.ca"},
    {"name": "Hillcrest Cabin Booking", "category": "travel", "brief": "Booking a cabin at Hillcrest Pines for a February ski weekend with friends.", "counterpart": "Hillcrest Pines Cabins, stay@hillcrestpines.ca"},
    {"name": "Monthly Budget Digest", "category": "reminder", "brief": "Monthly trigger on the 1st at 8am summarizing card statements and subscriptions.", "counterpart": ""},
    {"name": "Email to Marisol Carpool", "category": "email_person", "brief": "Coordinating a carpool to a friend's housewarming in Hamilton with Marisol Reyes.", "counterpart": "Marisol Reyes, marisol.reyes@quaymail.net"},
]

PATTERNS: Dict[str, List[Tuple[List[str], int]]] = {
    "email_person": [(["draft", "send"], 40), (["draft", "send", "check_reply"], 25), (["compose_send"], 20), (["compose_send", "check_reply"], 15)],
    "lookup": [(["search"], 70), (["search", "forward"], 30)],
    "reminder": [(["trigger"], 70), (["search_trigger"], 30)],
    "research": [(["search"], 70), (["reply_draft", "send"], 30)],
    "purchase": [(["search"], 40), (["reply_draft", "send"], 30), (["search", "forward"], 15), (["draft", "send"], 15)],
    "subscription": [(["search"], 40), (["reply_draft", "send"], 35), (["search_trigger"], 25)],
    "travel": [(["search"], 40), (["draft", "send"], 30), (["search_trigger"], 15), (["draft", "send", "check_reply"], 15)],
    "finance": [(["search"], 50), (["search_trigger"], 25), (["reply_draft", "send"], 25)],
    "family_home": [(["draft", "send"], 30), (["compose_send"], 20), (["search"], 30), (["trigger"], 20)],
    "admin_generic": [(["search"], 60), (["search", "search"], 40)],
    "work_misc": [(["draft", "send"], 40), (["search"], 30), (["reply_draft", "send"], 30)],
}

WINDOW_START = bf.dt("2026-07-20 09:00:00")
WINDOW_END = bf.dt(bf.DISTRACTOR_END)

# ---------------------------------------------------------------------------------------------
# LLM plumbing
# ---------------------------------------------------------------------------------------------


def _load_cost() -> Dict[str, Any]:
    return bf.load_json(COST_PATH, {"total_usd": 0.0, "calls": 0, "by_stage": {}})


def _save_cost(cost: Dict[str, Any]) -> None:
    GEN.mkdir(parents=True, exist_ok=True)
    COST_PATH.write_text(json.dumps(cost, indent=2) + "\n", encoding="utf-8")


class Spend:
    def __init__(self, stage: str) -> None:
        self.stage = stage
        self.cost = _load_cost()

    def add(self, usage: Optional[Dict[str, Any]]) -> None:
        value = float((usage or {}).get("cost") or 0.0)
        self.cost["total_usd"] = round(self.cost["total_usd"] + value, 6)
        self.cost["calls"] += 1
        self.cost["by_stage"][self.stage] = round(self.cost["by_stage"].get(self.stage, 0.0) + value, 6)
        _save_cost(self.cost)


async def llm(spend: Spend, system: str, user: str, model: Optional[str] = None, max_tokens: int = 12000) -> str:
    settings = get_settings()
    response = await request_chat_completion(
        model=model or settings.execution_agent_model,
        messages=[{"role": "user", "content": user}],
        system=system,
        max_tokens=max_tokens,
    )
    spend.add(response.get("usage"))
    return ((response.get("choices") or [{}])[0].get("message") or {}).get("content") or ""


def parse_json(text: str) -> Any:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    start = min([i for i in (text.find("{"), text.find("[")) if i >= 0], default=0)
    return json.loads(text[start:])


async def llm_json(spend: Spend, system: str, user: str, validate, attempts: int = 3, **kw) -> Any:
    last: Optional[Exception] = None
    for attempt in range(attempts):
        try:
            data = parse_json(await llm(spend, system, user, **kw))
            return validate(data)
        except Exception as exc:  # malformed batch: retry
            last = exc
            print(f"  retry {attempt + 1}/{attempts}: {str(exc)[:160]}", file=sys.stderr)
    raise RuntimeError(f"LLM batch failed after {attempts} attempts: {last}")


# ---------------------------------------------------------------------------------------------
# Stage 1: names
# ---------------------------------------------------------------------------------------------

NAMES_SYSTEM = "You generate realistic test data for an email-assistant evaluation. Reply with strict JSON only."


async def stage_names() -> None:
    spend = Spend("names")
    taken_slugs = {agent_log_filename(a.name) for a in bf.CORE_AGENTS}
    out: List[Dict[str, Any]] = []
    for seed in SEEDS:
        assert not bf.distractor_violations(seed["name"], json.dumps(seed)), seed
        taken_slugs.add(agent_log_filename(seed["name"]))
        out.append(dict(seed, seed=True))
    for key, count, desc in CATEGORIES:
        have = [x for x in out if x["category"] == key]
        tries = 0
        while len(have) < count and tries < 6:
            tries += 1
            want = min(45, count - len(have) + 8)
            existing = ", ".join(x["name"] for x in have) or "(none yet)"
            prompt = (
                f"{PERSONA}\n\n{FICTION_RULES}\n\nGenerate {want} DISTINCT execution-agent names for this category: {desc}.\n"
                f"Each agent was created over the past three months for one concrete task. Vary the people, businesses and topics a lot; "
                f"some names can look similar to each other (e.g. two different 'Email to ...' names) but each must be about a different counterpart.\n"
                f"Already used in this category (do not repeat or near-duplicate): {existing}\n\n"
                'Return JSON: {"agents": [{"name": "...", "brief": "one sentence: what Theo asked for", '
                '"counterpart": "person or business name + invented email address, or empty string if none"}]}'
            )

            def validate(data: Any) -> List[Dict[str, Any]]:
                items = data["agents"]
                assert isinstance(items, list) and items
                return [{"name": str(i["name"]).strip(), "brief": str(i["brief"]).strip(), "counterpart": str(i.get("counterpart") or "").strip()} for i in items]

            items = await llm_json(spend, NAMES_SYSTEM, prompt, validate)
            for item in items:
                slug = agent_log_filename(item["name"])
                if slug in taken_slugs or not (2 <= len(item["name"].split()) <= 7):
                    continue
                if bf.distractor_violations(item["name"], json.dumps(item)):
                    continue
                taken_slugs.add(slug)
                item["category"] = key
                out.append(item)
                have.append(item)
                if len(have) >= count:
                    break
            print(f"names[{key}]: {len(have)}/{count}  (spend ${spend.cost['total_usd']:.4f})")
    out = out[:N_DISTRACTORS] if len(out) >= N_DISTRACTORS else out
    if len(out) < N_DISTRACTORS:
        raise SystemExit(f"only {len(out)} names; rerun")
    GEN.mkdir(parents=True, exist_ok=True)
    NAMES_PATH.write_text(json.dumps({"agents": out}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(out)} names")


EXTRA_CATEGORY_COUNTS = {
    "email_person": 262, "lookup": 144, "reminder": 144, "research": 80, "purchase": 128, "subscription": 80,
    "travel": 96, "finance": 96, "family_home": 96, "admin_generic": 10, "work_misc": 64,
}  # 1200 extra names: 400 join roster_800, 800 more join roster_1600


async def stage_names_more() -> None:
    """Append EXTRA names (tier_group 'extended') without touching the original 375, so rosters <= 400 stay identical."""
    spend = Spend("names_more")
    data = json.loads(NAMES_PATH.read_text(encoding="utf-8"))
    out: List[Dict[str, Any]] = data["agents"]
    taken_slugs = {agent_log_filename(a.name) for a in bf.CORE_AGENTS} | {agent_log_filename(x["name"]) for x in out}
    descs = {key: desc for key, _, desc in CATEGORIES}
    async def fill(key: str, extra: int) -> None:
        # categories run concurrently; asyncio is single-threaded, so the shared slug set stays consistent
        have_all = [x for x in out if x["category"] == key]
        added: List[Dict[str, Any]] = []
        tries = 0
        while len(added) < extra and tries < extra // 20 + 8:
            tries += 1
            want = min(45, extra - len(added) + 8)
            existing = ", ".join(x["name"] for x in have_all[-120:])
            prompt = (
                f"{PERSONA}\n\n{FICTION_RULES}\n\nGenerate {want} DISTINCT execution-agent names for this category: {descs[key]}.\n"
                f"Each agent was created over the past three months for one concrete task. Vary the people, businesses and topics a lot; "
                f"some names can look similar to each other (e.g. two different 'Email to ...' names) but each must be about a different counterpart.\n"
                f"Already used in this category (do not repeat or near-duplicate): {existing}\n\n"
                'Return JSON: {"agents": [{"name": "...", "brief": "one sentence: what Theo asked for", '
                '"counterpart": "person or business name + invented email address, or empty string if none"}]}'
            )

            def validate(payload: Any) -> List[Dict[str, Any]]:
                items = payload["agents"]
                assert isinstance(items, list) and items
                return [{"name": str(i["name"]).strip(), "brief": str(i["brief"]).strip(), "counterpart": str(i.get("counterpart") or "").strip()} for i in items]

            items = await llm_json(spend, NAMES_SYSTEM, prompt, validate)
            for item in items:
                slug = agent_log_filename(item["name"])
                if slug in taken_slugs or not (2 <= len(item["name"].split()) <= 7):
                    continue
                if bf.distractor_violations(item["name"], json.dumps(item)):
                    continue
                taken_slugs.add(slug)
                item.update(category=key, tier_group="extended")
                have_all.append(item)
                added.append(item)
                if len(added) >= extra:
                    break
            print(f"names_more[{key}]: {len(added)}/{extra}  (spend ${spend.cost['total_usd']:.4f})", flush=True)
        if len(added) < extra:
            raise SystemExit(f"only {len(added)}/{extra} extra names for {key}; rerun (progress is not saved)")
        results[key] = added

    results: Dict[str, List[Dict[str, Any]]] = {}
    await asyncio.gather(*(fill(key, extra) for key, extra in EXTRA_CATEGORY_COUNTS.items()))
    for key in EXTRA_CATEGORY_COUNTS:  # deterministic file order regardless of completion order
        out.extend(results[key])
    NAMES_PATH.write_text(json.dumps({"agents": out}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(out)} names ({sum(1 for x in out if x.get('tier_group') == 'extended')} extended)")


# ---------------------------------------------------------------------------------------------
# Stage 2: logs
# ---------------------------------------------------------------------------------------------


def _rng(*parts: Any) -> random.Random:
    return random.Random(bf._h("gen", *parts))


def plan_for(agent: Dict[str, Any]) -> List[Dict[str, str]]:
    rng = _rng("plan", agent["name"])
    if agent["name"] == "Monthly Budget Digest":
        kinds = ["trigger"]
    elif agent["category"] == "admin_generic" and agent["name"] in ("Inbox Summary", "Unread Email Check"):
        kinds = ["search", "search"]
    else:
        options = PATTERNS[agent["category"]]
        kinds = rng.choices([k for k, _ in options], weights=[w for _, w in options])[0]
    span = (WINDOW_END - WINDOW_START).total_seconds() - 3 * 86400
    while True:
        day = WINDOW_START + timedelta(seconds=rng.random() * span)
        hour = rng.choices(range(7, 24), weights=[2, 4, 5, 5, 5, 6, 5, 4, 4, 5, 6, 6, 7, 7, 6, 4, 2])[0]
        start = day.replace(hour=hour, minute=rng.randrange(60), second=rng.randrange(60))
        if WINDOW_START <= start <= WINDOW_END - timedelta(days=1):
            break
    plan = []
    t = start
    for i, kind in enumerate(kinds):
        if i:
            if kind == "send":
                t += timedelta(seconds=rng.randint(60, 240))
            elif kind == "forward":
                t += timedelta(seconds=rng.randint(60, 300))
            elif kind == "check_reply":
                t += timedelta(days=rng.randint(2, 9), hours=rng.randint(-3, 5), minutes=rng.randint(0, 59))
            else:
                t += timedelta(days=rng.randint(5, 25), minutes=rng.randint(0, 600))
            if t > WINDOW_END:
                t = min(WINDOW_END, plan[-1]["_t"] + timedelta(minutes=rng.randint(5, 50)))
        plan.append({"kind": kind, "_t": t})
    for p in plan:
        p["at"] = bf.ts(p.pop("_t"))
    return plan


KIND_SPEC = {
    "draft": 'Poke asks the agent to draft a NEW email (not sent). Fields: user, ack, instructions, to, subject, body, response (MUST contain the literal token {draft_block} where the draft details go), reply (Poke asking the user to confirm sending)',
    "send": "the user confirms the previous draft. Fields: user (short confirmation like 'send it'), ack, reply (Poke confirming it was sent)",
    "compose_send": "Poke wrote the email itself, the user approved, and the agent creates + sends it in one go. Fields: user (Theo's ORIGINAL request), to, subject, body, reply (Poke confirming it was sent)",
    "check_reply": "the user asks whether the counterpart replied to the earlier email. Fields: user, ack, instructions, gmail_query, query, results (0 or 1 email FROM the counterpart replying, dated between the earlier send and this request), response, reply",
    "search": "the agent searches the inbox. Fields: user, ack, instructions, gmail_query, query, results (1-3 emails dated before this request), response (agent's factual report with the details found), reply (Poke's short text to Theo)",
    "reply_draft": "the agent finds an email and drafts a reply in its thread (not sent). Fields: user, ack, instructions, gmail_query, query, results (exactly 1 email), subject, body, response (MUST contain {draft_block}), reply (Poke asking to confirm)",
    "forward": "the user asks to forward the email just found (approval given). Fields: user, ack, instructions, to, note, response (mention {sent_id}), reply",
    "trigger": "the agent creates a reminder trigger. Fields: user, ack, instructions, payload, rrule (iCalendar RRULE body like 'FREQ=MONTHLY;BYMONTHDAY=1' or null for one-off), start ('YYYY-MM-DDTHH:MM:SS' local time AFTER the request time), response (MUST mention trigger ID {trigger_id} and the schedule), reply",
    "search_trigger": "the agent looks up a due date in an email, then creates a reminder trigger for it. Fields: all search fields + payload, rrule, start, response (mention {trigger_id}), reply",
}

LOGS_SYSTEM = (
    "You write realistic fixture data for an AI email assistant. 'Poke' is the interaction agent texting with the user; it delegates to named "
    "execution agents with Gmail tools. Agent responses are factual, detailed reports to Poke (often with **bold** labels and bullet lists, "
    "IDs when relevant, and 'Nothing was sent.' when nothing was sent). Poke's replies to the user are terse, warm, lightly witty, lowercase-friendly. "
    "Instructions from Poke to the agent are explicit and complete (who, what, email addresses, dates, 'do not send'). Reply with strict JSON only."
)


def _email_ok(e: Any) -> bool:
    return isinstance(e, dict) and all(isinstance(e.get(k), str) and e.get(k) for k in ("from", "subject", "date", "text")) and "@" in e["from"]


def validate_agent(agent: Dict[str, Any], plan: List[Dict[str, str]], data: Dict[str, Any]) -> List[Dict[str, Any]]:
    reqs = data["requests"]
    assert isinstance(reqs, list) and len(reqs) == len(plan), f"{agent['name']}: expected {len(plan)} requests"
    out = []
    slug = agent_log_filename(agent["name"])
    thread = f"dx:{slug}"
    rng = _rng("fix", agent["name"])
    sent_at: Optional[datetime] = None
    for i, (p, r) in enumerate(zip(plan, reqs)):
        kind, at = p["kind"], bf.dt(p["at"])
        need = {"send": ["user", "ack", "reply"], "compose_send": ["user", "to", "subject", "body", "reply"]}.get(kind, ["user", "ack", "instructions", "response", "reply"])
        for k in need:
            assert isinstance(r.get(k), str) and r[k].strip(), f"{agent['name']} req {i} ({kind}) missing {k}"
        req: Dict[str, Any] = {"t": p["at"], "kind": kind, "user": r["user"].strip(), "ack": (r.get("ack") or "On it.").strip(), "reply": r["reply"].strip()}
        steps: List[Dict[str, Any]] = []

        def results(max_n: int, min_n: int = 1) -> List[Dict[str, Any]]:
            res = r.get("results") or []
            assert isinstance(res, list) and min_n <= len(res) <= max_n and all(_email_ok(e) for e in res), f"{agent['name']} req {i}: bad results"
            fixed = []
            for e in res:
                try:
                    when = datetime.strptime(e["date"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=bf.TZ)
                except ValueError:
                    when = datetime.strptime(e["date"][:16], "%Y-%m-%d %H:%M").replace(tzinfo=bf.TZ)
                lo = sent_at if (kind == "check_reply" and sent_at) else at - timedelta(days=20)
                if not (lo < when < at):
                    when = lo + (at - lo) * (0.3 + 0.6 * rng.random())
                fixed.append({"from": e["from"], "subject": e["subject"], "date": bf.ts(when), "text": e["text"], "thread": thread if kind in ("check_reply", "reply_draft") else None,
                              "labels": ["IMPORTANT", "CATEGORY_PERSONAL", "INBOX"] if kind == "check_reply" else ["CATEGORY_UPDATES", "INBOX"]})
            fixed.sort(key=lambda e: e["date"], reverse=True)
            return fixed

        if kind in ("search", "check_reply", "reply_draft", "search_trigger"):
            res = results(1 if kind == "reply_draft" else 3, 0 if kind == "check_reply" else 1)
            if kind == "search" and plan[min(i + 1, len(plan) - 1)]["kind"] == "forward" and res:
                res[0]["key"] = f"{thread}:fw"
            steps.append({"tool": "task_email_search", "query": str(r.get("query") or r["instructions"])[:300], "gq": str(r.get("gmail_query") or "in:inbox newer_than:30d"), "results": res})
        if kind == "reply_draft":
            sender = steps[0]["results"][0]["from"]
            to = re.search(r"<([^>]+)>", sender).group(1) if "<" in sender else sender
            steps.append({"tool": "gmail_create_draft", "to": to, "subject": r["subject"], "body": r["body"], "thread": thread})
        if kind == "draft":
            assert "@" in r.get("to", ""), "draft needs to"
            steps.append({"tool": "gmail_create_draft", "to": r["to"].strip(), "subject": r["subject"], "body": r["body"], "thread": thread})
        if kind == "compose_send":
            steps.append({"tool": "gmail_create_draft", "to": r["to"].strip(), "subject": r["subject"], "body": r["body"], "thread": thread})
            steps.append({"tool": "gmail_execute_draft"})
            sent_at = at
        if kind == "send":
            assert any(st["tool"] == "gmail_create_draft" for prev in out for st in prev["steps"]), "send without a draft"
            steps.append({"tool": "gmail_execute_draft"})
            sent_at = at
        if kind == "forward":
            assert out and any(e.get("key") for st in out[-1]["steps"] if st["tool"] == "task_email_search" for e in st["results"]), "forward needs a prior search"
            assert "@" in r.get("to", ""), "forward needs to"
            steps.append({"tool": "gmail_forward_email", "email_key": f"{thread}:fw", "to": r["to"].strip(), "note": str(r.get("note") or "")})
        if kind in ("trigger", "search_trigger"):
            rrule = r.get("rrule")
            if isinstance(rrule, str):
                rrule = rrule.strip().removeprefix("RRULE:") or None
                assert rrule is None or rrule.startswith("FREQ="), f"bad rrule {rrule}"
            else:
                rrule = None
            start = datetime.fromisoformat(str(r["start"])[:19]).replace(tzinfo=bf.TZ)
            while start <= at:
                start += timedelta(days=1)
            steps.append({"tool": "createTrigger", "payload": r["payload"], "rrule": rrule, "start": start.strftime("%Y-%m-%dT%H:%M:%S")})
        req["steps"] = steps
        if kind == "send":
            req["instructions"] = bf._SEND_INSTR[bf._h(slug, i) % len(bf._SEND_INSTR)]
            req["response"] = None
        elif kind == "compose_send":
            req["ack"] = "Sending."
            req["instructions"] = ("The user reviewed and approved this email. Create it and send it exactly as written, with no changes:\n\n"
                                   f"To: {r['to'].strip()}\nSubject: {r['subject']}\n\nBody:\n{r['body']}\n\n"
                                   "After sending, reply with confirmation including the recipient, subject, and sent message ID.")
            req["response"] = None
        else:
            req["instructions"] = r["instructions"].strip()
            resp = r["response"].strip()
            if kind in ("draft", "reply_draft") and "{draft_block}" not in resp:
                resp += "\n\n{draft_block}\n\nWaiting for the user's confirmation before sending."
            if kind in ("trigger", "search_trigger") and "{trigger_id}" not in resp:
                resp += " (trigger ID {trigger_id})"
            req["response"] = resp
        req["draft_view"] = kind in ("draft", "reply_draft")
        if rng.random() < 0.25 and kind not in ("send",):
            req["wait"] = "Waiting for the execution agent's result before replying to the user."
        out.append(req)
    problems = bf.distractor_violations(agent["name"], json.dumps(out, ensure_ascii=False))
    assert not problems, f"{agent['name']}: {problems[:3]}"
    return out


async def stage_logs(batch_size: int = 6, concurrency: int = 6, only_missing: bool = True) -> None:
    spend = Spend("logs")
    names = bf.load_json(NAMES_PATH, None)
    if not names:
        raise SystemExit("run `generate names` first")
    agents = names["agents"]
    existing = {a["name"]: a for a in bf.load_json(DISTRACTORS_PATH, {"agents": []})["agents"]} if only_missing else {}
    todo = [a for a in agents if a["name"] not in existing]
    plans = {a["name"]: plan_for(a) for a in agents}
    batches = [todo[i:i + batch_size] for i in range(0, len(todo), batch_size)]
    sem = asyncio.Semaphore(concurrency)
    results: Dict[str, List[Dict[str, Any]]] = {}
    failed: List[str] = []

    async def run(batch: List[Dict[str, Any]]) -> None:
        async with sem:
            spec = []
            for a in batch:
                spec.append({"name": a["name"], "what_theo_wanted": a["brief"], "counterpart": a.get("counterpart", ""),
                             "requests": [{"kind": p["kind"], "at": p["at"]} for p in plans[a["name"]]]})
            kinds = sorted({p["kind"] for a in batch for p in plans[a["name"]]})
            prompt = (
                f"{PERSONA}\n\n{FICTION_RULES}\n\nWrite the history of these execution agents. Each request happened at the given local time "
                "(America/Toronto); keep dates consistent with it (emails found are dated before the request; reminders start after it). "
                "Use concrete invented details (order numbers, amounts in CAD, dates, addresses at invented domains). The counterpart's email must be "
                "consistent across requests of the same agent. Emails Theo sends are signed 'Theo'.\n\n"
                "Request kinds and their JSON fields:\n" + "\n".join(f"- {k}: {KIND_SPEC[k]}" for k in kinds) + "\n\n"
                "Email objects in results: {\"from\": \"Name <addr>\", \"subject\": ..., \"date\": \"YYYY-MM-DD HH:MM:SS\", \"text\": \"1-3 sentences\"}.\n"
                "'query' is the natural-language search the agent ran; 'gmail_query' is the Gmail search string (e.g. 'from:x@y.ca after:2026/08/01').\n\n"
                f"AGENTS:\n{json.dumps(spec, indent=1, ensure_ascii=False)}\n\n"
                'Return JSON: {"agents": [{"name": "<exact name>", "requests": [ {<fields for request 1>}, ... ]}, ...]} with the agents and requests in the given order.'
            )

            def validate(data: Any) -> Dict[str, List[Dict[str, Any]]]:
                got = {a["name"]: a for a in data["agents"]}
                out = {}
                for a in batch:
                    assert a["name"] in got, f"missing agent {a['name']}"
                    out[a["name"]] = validate_agent(a, plans[a["name"]], got[a["name"]])
                return out

            try:
                res = await llm_json(spend, LOGS_SYSTEM, prompt, validate)
                results.update(res)
            except Exception as exc:
                print(f"batch failed: {exc}", file=sys.stderr)
                failed.extend(a["name"] for a in batch)
            print(f"logs: {len(results) + len(existing)}/{len(agents)} (spend ${spend.cost['total_usd']:.4f})")

    await asyncio.gather(*(run(b) for b in batches))
    # retry failures one agent at a time
    for name in list(failed):
        a = next(x for x in agents if x["name"] == name)
        try:
            await run([a])
            failed.remove(name)
        except Exception:
            pass
    merged = dict(existing)
    for a in agents:
        if a["name"] in results:
            merged[a["name"]] = {"name": a["name"], "category": a["category"], "brief": a["brief"], "requests": results[a["name"]]}
    final = [merged[a["name"]] for a in agents if a["name"] in merged]
    _assign_tiers(final)
    DISTRACTORS_PATH.write_text(json.dumps({"agents": final}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(final)} distractors ({len(agents) - len(final)} missing)")


def _assign_tiers(final: List[Dict[str, Any]]) -> None:
    order = sorted(final, key=lambda a: bf._h("tier", a["name"]))
    seeds = [a for a in order if any(s["name"] == a["name"] for s in SEEDS)]
    rest = [a for a in order if a not in seeds]
    order = seeds + rest  # seeded hard negatives join at the smallest sizes
    cursor = 0
    for size, count in bf.TIER_COUNTS.items():
        for a in order[cursor:cursor + count]:
            a["tier"] = size
        cursor += count
    for a in order[cursor:]:
        a["tier"] = 400


# ---------------------------------------------------------------------------------------------
# Stage 3: older-window filler
# ---------------------------------------------------------------------------------------------

FILLER_SYSTEM = "You write realistic casual text-message exchanges between a user and his AI assistant. Reply with strict JSON only."


async def stage_filler(n_chats: int = 24) -> None:
    spend = Spend("filler")
    prompt = (
        f"{PERSONA}\n\n{FICTION_RULES}\n\nWrite {n_chats} short standalone chats between Theo and Poke where Poke answers DIRECTLY without "
        "any email/task delegation: quick facts, cooking questions, banter, conversions, word definitions, gift ideas, small talk, jokes. "
        "No scheduling, no emailing anyone, no reminders, no real brands. Poke is witty but terse, never says 'let me know if you need anything'. "
        "Theo writes lowercase. Mix lengths: about a third have 2 messages (theo, poke), a third have 3 (theo, poke, theo short ack like 'lol' or 'ty' "
        "with no reply), a third have 4 (theo, poke, theo, poke). Tag each with season 'summer' (Jul-Aug), 'fall' (Sep-Oct) or 'any'.\n\n"
        'Return JSON: {"chats": [{"season": "summer|fall|any", "messages": ["theo text", "poke text", ...]}]}'
    )

    def validate(data: Any) -> List[Dict[str, Any]]:
        chats = data["chats"]
        assert len(chats) >= n_chats - 4
        out = []
        for c in chats:
            msgs = c["messages"]
            assert 2 <= len(msgs) <= 4 and all(isinstance(m, str) and m.strip() for m in msgs)
            if bf.distractor_violations("chat", json.dumps(msgs)):
                continue
            out.append({"season": c.get("season", "any"), "messages": [m.strip() for m in msgs]})
        return out

    chats = await llm_json(spend, FILLER_SYSTEM, prompt, validate)

    built = bf.build(include_generated=False)
    busy = sorted(e.when for e in built.convo_core)
    distractors = bf.load_json(DISTRACTORS_PATH, {"agents": []})["agents"]
    # Distractor episodes that also appear in the older conversation: single search/trigger requests from the
    # smallest tier, clear of every core episode by 30 minutes.
    picks: List[str] = []
    for spec in sorted(distractors, key=lambda a: a["requests"][0]["t"]):
        if spec["tier"] != 50 or len(spec["requests"]) != 1 or spec["requests"][0]["kind"] not in ("search", "trigger"):
            continue
        t = bf.dt(spec["requests"][0]["t"])
        if all(abs((t - b).total_seconds()) > 1800 for b in busy) and all(abs((t - bf.dt(next(a for a in distractors if a["name"] == p)["requests"][0]["t"])).total_seconds()) > 10 * 86400 for p in picks):
            picks.append(spec["name"])
            busy.append(t)
        if len(picks) == 3:
            break
    # assign chat times in free slots
    rng = _rng("filler-slots")
    placed = []
    for k, chat in enumerate(chats):
        for _ in range(500):
            lo, hi = (bf.dt("2026-07-21 08:00:00"), bf.dt("2026-08-31 23:00:00")) if chat["season"] == "summer" else \
                     (bf.dt("2026-09-01 08:00:00"), bf.dt("2026-10-13 22:00:00")) if chat["season"] == "fall" else \
                     (bf.dt("2026-07-21 08:00:00"), bf.dt("2026-10-13 22:00:00"))
            t = lo + timedelta(seconds=rng.random() * (hi - lo).total_seconds())
            t = t.replace(hour=rng.choice([8, 9, 12, 13, 17, 19, 20, 21, 22]), minute=rng.randrange(60), second=rng.randrange(60))
            if all(abs((t - b).total_seconds()) > 1800 for b in busy):
                busy.append(t)
                break
        entries = [{"tag": "user_message" if j % 2 == 0 else "poke_reply", "text": m} for j, m in enumerate(chat["messages"])]
        placed.append({"t": bf.ts(t), "season": chat["season"], "entries": entries})
    FILLER_PATH.write_text(json.dumps({"distractor_episodes": picks, "chats": placed}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(placed)} chats, distractor episodes {picks}")


# ---------------------------------------------------------------------------------------------
# Stage 4: summary (real summarizer path)
# ---------------------------------------------------------------------------------------------


async def stage_summary() -> None:
    spend = Spend("summary")
    settings = get_settings()
    built = bf.build()
    lines = bf.conversation_lines(built)
    if len(lines) != bf.N_ENTRIES:
        raise SystemExit(f"conversation has {len(lines)} entries; fix filler first")
    entries = []
    for index, line in enumerate(lines):
        tag, timestamp, payload = parse_line(line)  # exactly what ConversationLog.iter_entries yields
        entries.append(LogEntry(tag=tag, payload=payload, index=index, timestamp=timestamp or None))
    summary = ""
    passes = []
    for lo in (0, 100, 200):
        batch = entries[lo:lo + 100]
        prompt = build_summarization_prompt(summary, batch)
        text = ""
        for attempt in range(2):  # same retry policy as summarizer._call_openrouter
            response = await request_chat_completion(model=settings.summarizer_model, messages=prompt.messages, system=prompt.system_prompt,
                                                     api_key=settings.openrouter_api_key)
            spend.add(response.get("usage"))
            text = (((response.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
            if text:
                break
        summary = text if text else summary
        passes.append({"batch": [lo, lo + 99], "cost": (response.get("usage") or {}).get("cost"), "chars": len(summary)})
        print(f"summary pass {lo}-{lo + 99}: {len(summary)} chars")
    # the third pass fires when entry 309 is appended (110 unsummarized), a few seconds later
    t309 = built.conversation[309].when
    updated = (t309 + timedelta(seconds=7, microseconds=512331)).astimezone(timezone.utc)
    SUMMARY_PATH.write_text(json.dumps({
        "summary": summary,
        "updated_at": updated.isoformat(),
        "entries_sha256": bf.older_digest(built),
        "model": settings.summarizer_model,
        "passes": passes,
    }, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    low = summary.lower()
    for term in ("wendell", "mortgage", "lumen", "dmitri", "harrow"):
        print(f"  summary mentions {term!r}: {term in low}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("stage", choices=["names", "names_more", "logs", "filler", "summary"])
    parser.add_argument("--fresh", action="store_true", help="logs: regenerate all agents instead of only missing ones")
    args = parser.parse_args(argv)
    if args.stage == "names":
        asyncio.run(stage_names())
    elif args.stage == "names_more":
        asyncio.run(stage_names_more())
    elif args.stage == "logs":
        asyncio.run(stage_logs(only_missing=not args.fresh))
    elif args.stage == "filler":
        asyncio.run(stage_filler())
    else:
        asyncio.run(stage_summary())
    print(f"total LLM spend so far: ${_load_cost()['total_usd']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
