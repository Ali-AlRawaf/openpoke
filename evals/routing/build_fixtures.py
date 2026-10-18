"""Build the routing-eval fixtures (core agents, recent conversation, rosters, cases, state/).

Deterministic and re-runnable. The hand-designed core (25 agents and their logs, plus the
recent 80 conversation entries) lives in this file as structured Python data. The LLM-generated
parts (distractor agents, older-conversation filler, the summary) are frozen JSON under
``fixtures/generated/``, written once by ``generate.py`` and only read here.

    python -m evals.routing.build_fixtures            # write state/, rosters/, cases.json
    python -m evals.routing.build_fixtures --check    # write, then run the self-check
    python -m evals.routing.build_fixtures --check-only

Every log line goes through ``logfmt.format_line`` (the server's own encoder).
"""

from __future__ import annotations

import os
import tempfile

# logfmt imports server modules, which create directories under the data dir at import time,
# so point the data dir at a throwaway location before anything from `server` is imported.
os.environ.setdefault("OPENPOKE_DATA_DIR", tempfile.mkdtemp(prefix="openpoke-fixtures-"))

import argparse
import hashlib
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from zoneinfo import ZoneInfo

from evals.routing.logfmt import agent_log_filename, format_line, parse_line

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
STATE = FIXTURES / "state"
ROSTERS = FIXTURES / "rosters"
GENERATED = FIXTURES / "generated"
CASES_PATH = FIXTURES / "cases.json"

TZ = ZoneInfo("America/Toronto")
UTC = timezone.utc
USER_NAME = "Theo Marchetti"
USER_EMAIL = "theo@northfoldstudio.ca"
USER_FROM = f"{USER_NAME} <{USER_EMAIL}>"
ROSTER_SIZES = (25, 50, 100, 200, 400, 800, 1600)
TIER_COUNTS = {50: 25, 100: 50, 200: 100, 400: 200, 800: 400, 1600: 800}  # distractors added at each size
N_ENTRIES = 380
LAST_INDEX = 299
RECENT_START = "2026-10-14 00:00:00"  # entries 300-379 live in [RECENT_START, now]
DISTRACTOR_END = "2026-10-13 22:30:00"  # distractor activity must end before the recent window

# ---------------------------------------------------------------------------------------------
# World data (machine-readable subset of fixtures/world.md), used for distractor checks.
# ---------------------------------------------------------------------------------------------

CORE_PEOPLE: List[Dict[str, str]] = [
    {"first": "Celeste", "last": "Moreau", "email": "celeste@harrowhillestate.ca", "org": "Harrow Hill Estate", "domain": "harrowhillestate.ca"},
    {"first": "Priya", "last": "Natarajan", "email": "priya@northfoldstudio.ca", "org": "Northfold Studio", "domain": ""},
    {"first": "Dmitri", "last": "Volkov", "email": "dmitri@ironbarkreno.ca", "org": "Ironbark Renovations", "domain": "ironbarkreno.ca"},
    {"first": "Hana", "last": "Ishikawa", "email": "hana.ishikawa@copperleafdata.com", "org": "Copperleaf Data", "domain": "copperleafdata.com"},
    {"first": "Wendell", "last": "Achebe", "email": "wendell.achebe@brightmoorcu.ca", "org": "Brightmoor Credit Union", "domain": "brightmoorcu.ca"},
    {"first": "Priya", "last": "Sandhu", "email": "priya@lumenandlinen.ca", "org": "Lumen & Linen Photography", "domain": "lumenandlinen.ca"},
    {"first": "Marco", "last": "Bellandi", "email": "marco@riverdalerecsoccer.ca", "org": "Riverdale Rec Soccer League", "domain": "riverdalerecsoccer.ca"},
    {"first": "Gabe", "last": "Lindqvist", "email": "gabe@northfoldstudio.ca", "org": "Northfold Studio", "domain": ""},
    {"first": "Marcus", "last": "Oyelaran", "email": "marcus@fernwaytalent.com", "org": "Fernway Talent", "domain": "fernwaytalent.com"},
    {"first": "", "last": "", "email": "billing@lakeporthydro.ca", "org": "Lakeport Hydro", "domain": "lakeporthydro.ca"},
    {"first": "", "last": "", "email": "frontdesk@tidewaterdental.ca", "org": "Tidewater Dental", "domain": "tidewaterdental.ca"},
    {"first": "Rosa", "last": "Marchetti", "email": "rosa.marchetti@quaymail.net", "org": "", "domain": ""},
    {"first": "Tomasz", "last": "Wierzbicki", "email": "tomasz.wierzbicki@quaymail.net", "org": "", "domain": ""},
    {"first": "Adaeze", "last": "Nwosu", "email": "cfp@prairieuxconf.org", "org": "Prairie UX", "domain": "prairieuxconf.org"},
    {"first": "", "last": "", "email": "reservations@osteriavaldina.ca", "org": "Osteria Valdina", "domain": "osteriavaldina.ca"},
    {"first": "", "last": "", "email": "orders@oakhurstfurniture.ca", "org": "Oakhurst Furniture", "domain": "oakhurstfurniture.ca"},
    {"first": "Leena", "last": "Haddad", "email": "leena@corktownphysio.ca", "org": "Corktown Physio", "domain": "corktownphysio.ca"},
    {"first": "", "last": "", "email": "reservations@hotelverriere.ca", "org": "Verrière", "domain": "hotelverriere.ca"},
    {"first": "Elaine", "last": "Fairbanks", "email": "elaine@ledgerlinepartners.ca", "org": "Ledgerline Partners", "domain": "ledgerlinepartners.ca"},
    {"first": "Noor", "last": "Hassan", "email": "noor@inkwellandvine.ca", "org": "Inkwell & Vine", "domain": "inkwellandvine.ca"},
    {"first": "", "last": "", "email": "members@ironwoodathletic.ca", "org": "Ironwood Athletic", "domain": "ironwoodathletic.ca"},
    {"first": "Harold", "last": "Pemberton", "email": "harold.pemberton@quaymail.net", "org": "", "domain": ""},
    {"first": "Sofia", "last": "Brandt", "email": "sofia.brandt@quaymail.net", "org": "", "domain": ""},
    # counterparts that only exist in cases (they must have no owner anywhere)
    {"first": "Marco", "last": "Ferrante", "email": "marco@keyhavenmusic.ca", "org": "Keyhaven Music", "domain": "keyhavenmusic.ca"},
    {"first": "", "last": "", "email": "service@halcyonchimney.ca", "org": "Halcyon Chimney", "domain": "halcyonchimney.ca"},
    {"first": "", "last": "", "email": "service@bramblewoodauto.ca", "org": "Bramblewood Auto", "domain": "bramblewoodauto.ca"},
]

# Terms that may not appear ANYWHERE in a distractor (name or log text), case-insensitive, word-bounded.
DISTRACTOR_BANNED_ANYWHERE: List[str] = sorted(
    {p["first"] for p in CORE_PEOPLE if p["first"]}
    | {p["last"] for p in CORE_PEOPLE if p["last"] and p["last"] != "Marchetti"}
    | {p["email"] for p in CORE_PEOPLE}
    | {p["domain"] for p in CORE_PEOPLE if p["domain"]}
    | {p["org"] for p in CORE_PEOPLE if p["org"] and p["org"] != "Northfold Studio"}
    | {"Rosa Marchetti", "Harrow Hill", "Lumen", "Ironbark", "Copperleaf", "Brightmoor", "Riverdale Rec",
       "Fernway", "Lakeport", "Tidewater", "Keyhaven", "Halcyon", "Bramblewood", "Cedar Hollow",
       "Oakhurst", "Corktown Physio", "Ledgerline", "Inkwell", "Ironwood", "Valdina", "Verriere",
       "Prairie UX", "Gabriel", "Dimitri", "Priyanka",
       # one-off senders that appear in core agents' logs (Sunday brief / inbox scan)
       "Pantrywise", "Northline Courier", "Larkspur", "Telvio", "Maplecrest", "Riverdale Library", "Leslieville Residents",
       "Humber Bay"}
)
# Substrings that may not appear anywhere (catch nicknames / variants).
DISTRACTOR_BANNED_SUBSTRINGS: List[str] = ["priya", "dmitr", "wendell", "marco", "gabe ", "gabe,", "celeste", "copperleaf", "brightmoor", "ironbark", "mortgage"]
# Topics that may not appear in a distractor NAME (keeps every case free of topic-vs-person conflicts).
DISTRACTOR_BANNED_NAME_TOPICS: List[str] = [
    r"wedding", r"venue", r"engagement", r"photo", r"proofs?", r"mortgage", r"refinanc", r"rate lock", r"pre-?approval",
    r"kitchen", r"reno(vation)?s?", r"bathroom", r"contractor", r"cabinet", r"roadmap", r"sprint", r"demo",
    r"offsite", r"off-site", r"agenda", r"chimney", r"fireplace", r"piano", r"music lesson", r"tires?", r"tyres?",
    r"mechanic", r"oil change", r"auto service", r"car service", r"sunday", r"rundown", r"week ahead", r"brief",
    r"hydro", r"dentist", r"dental", r"physio", r"gym", r"book club", r"save the date", r"invitation", r"stationery",
    r"recruit", r"designer search", r"jules", r"mom", r"thanksgiving", r"fence", r"neighbou?r", r"cottage",
    r"standing desk", r"montreal", r"talk proposal", r"q3", r"soccer", r"league", r"vendor renewal", r"analytics",
    r"inbox catch", r"catch-up scan",
]
# Real brands we never want in fixtures (spot check; the LLM is told to invent names).
REAL_BRAND_BLOCKLIST: List[str] = [
    "amazon", "google calendar", "apple", "netflix", "uber", "airbnb", "costco", "ikea", "walmart", "spotify",
    "air canada", "westjet", "shoppers drug", "loblaws", "rogers", "bell canada", "telus", "td bank", "rbc",
    "scotiabank", "cibc", "bmo", "paypal", "venmo", "interac", "visa ", "mastercard", "expedia", "booking.com",
    "doordash", "skip the dishes", "instacart", "home depot", "canadian tire", "best buy", "starbucks", "tim hortons",
    "chipotle", "presto", "aeroplan", "turbotax", "wealthsimple", "questrade", "hulu", "disney", "youtube",
    "linkedin", "facebook", "instagram", "whatsapp", "zoom", "slack", "notion", "figma", "dropbox", "etsy", "ebay",
]

# ---------------------------------------------------------------------------------------------
# Deterministic id helpers
# ---------------------------------------------------------------------------------------------


def _h(*parts: Any) -> int:
    digest = hashlib.sha256("\x1f".join(str(p) for p in parts).encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def dt(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=TZ)


def ts(moment: datetime) -> str:
    return moment.astimezone(TZ).strftime("%Y-%m-%d %H:%M:%S")


def gmail_id(moment: datetime, salt: str) -> str:
    ms = int(moment.timestamp() * 1000)
    return f"{(ms << 20) | (_h('gid', salt) & 0xFFFFF):x}"


def draft_id_for(salt: str) -> str:
    return "r" + str(1_000_000_000_000_000_000 + _h("draft", salt) % 8_999_999_999_999_999_999)[:19]


_LOG_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-"


def log_id_for(salt: str) -> str:
    n = _h("log", salt)
    chars = []
    for _ in range(12):
        n, r = divmod(n, len(_LOG_ALPHABET))
        chars.append(_LOG_ALPHABET[r])
        if n == 0:
            n = _h("log2", salt, len(chars))
    return "log_" + "".join(chars)


def utc_z(moment: datetime) -> str:
    return moment.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def jitter(salt: str, lo: int, hi: int) -> int:
    return lo + _h("j", salt) % (hi - lo + 1)


def indent_body(body: str) -> str:
    return "\n".join(("  " + line) if line.strip() else "" for line in body.split("\n"))


_PLACEHOLDER = re.compile(r"\{(\w+)\}")


def fill(text: str, values: Dict[str, str]) -> str:
    return _PLACEHOLDER.sub(lambda m: values.get(m.group(1), m.group(0)), text)


# ---------------------------------------------------------------------------------------------
# DSL: conversation entries, tool steps, requests, trigger fires, agents
# ---------------------------------------------------------------------------------------------


@dataclass
class U:  # user_message
    text: str
    gap: Optional[int] = None


@dataclass
class P:  # poke_reply
    text: str
    gap: Optional[int] = None


@dataclass
class W:  # wait
    text: str
    gap: Optional[int] = None


@dataclass
class Email:
    sender: str
    subject: str
    when: str
    text: str
    thread: Optional[str] = None
    to: str = USER_FROM
    labels: Tuple[str, ...] = ("IMPORTANT", "CATEGORY_PERSONAL", "INBOX")
    key: Optional[str] = None
    attachments: Tuple[str, ...] = ()


@dataclass
class Draft:
    to: str
    subject: str
    body: str
    thread: Optional[str] = None
    key: Optional[str] = None


@dataclass
class Send:
    key: Optional[str] = None


@dataclass
class Search:
    query: str
    gq: str
    emails: List[Email] = field(default_factory=list)


@dataclass
class People:
    query: str
    results: List[Tuple[str, str]]


@dataclass
class Forward:
    email_key: str
    to: str
    text: str


@dataclass
class Trig:
    payload: str
    rrule: Optional[str]
    start: str  # local ISO, e.g. "2026-08-09T19:00:00"


@dataclass
class DraftView:  # post marker: poke shows the latest draft via send_draft, then asks
    ask: str


@dataclass
class Req:
    t: str
    pre: List[Any]
    instr: str
    steps: List[Any]
    resp: Optional[str] = None
    post: Optional[List[Any]] = None
    wait: Optional[str] = None


@dataclass
class Fire:  # trigger fire: no agent_request line (the scheduler calls the runtime directly)
    t: str
    steps: List[Any]
    resp: str
    post: List[Any]


@dataclass
class Agent:
    name: str
    items: List[Any]  # Req | Fire
    core: bool = True
    tier: int = 25


@dataclass
class Entry:
    tag: str
    payload: str
    when: datetime
    episode: str


class World:
    """Global registries shared by every agent while rendering."""

    def __init__(self) -> None:
        self.threads: Dict[str, str] = {}
        self.emails: Dict[str, str] = {}
        self.trigger_ids: Dict[Tuple[str, int, int], int] = {}

    def thread_for(self, key: Optional[str], first_message_id: str) -> str:
        """Thread id for `key`; a new thread takes the id of its first message (as in Gmail)."""
        if key is None:
            return first_message_id
        self.threads.setdefault(key, first_message_id)
        return self.threads[key]


def assign_trigger_ids(world: World, agents: Sequence[Agent]) -> None:
    events = []
    for agent in agents:
        for i, item in enumerate(agent.items):
            if isinstance(item, Req):
                for j, step in enumerate(item.steps):
                    if isinstance(step, Trig):
                        events.append((dt(item.t), agent.name, i, j))
    events.sort()
    for n, (_, name, i, j) in enumerate(events, start=1):
        world.trigger_ids[(name, i, j)] = n


# ---- step rendering -----------------------------------------------------------------------------

def _call(tool: str, args: Dict[str, Any]) -> str:
    return f"Calling {tool} with: {json.dumps(args, default=str)[:200]}"


def _result(tool: str, result: Any) -> str:
    return f"{tool}: {json.dumps(result, default=str)[:500]}"


def _composio(data: Any, salt: str) -> Dict[str, Any]:
    return {"data": data, "error": None, "log_id": log_id_for(salt), "session_info": None, "successful": True}


def _draft_block(d: Dict[str, str], with_id: bool = True) -> str:
    lines = [f"- **To:** {d['to']}", f"- **Subject:** {d['subject']}", "- **Body:**", indent_body(d["body"])]
    out = "\n".join(lines)
    if with_id:
        out += f"\n\n- **Draft ID:** {d['draft_id']}"
    return out


class AgentRender:
    def __init__(self, world: World, agent: Agent) -> None:
        self.world = world
        self.agent = agent
        self.drafts: Dict[str, Dict[str, str]] = {}
        self.last_draft: Optional[str] = None
        self.found: List[Dict[str, Any]] = []
        self.lines: List[Tuple[str, str, datetime]] = []  # (tag, payload, when)
        self.vars: Dict[str, str] = {}
        self.kinds: List[str] = []

    def log(self, tag: str, payload: str, when: datetime) -> None:
        self.lines.append((tag, payload, when))

    def run_steps(self, steps: Sequence[Any], start: datetime, salt: str, item_index: int) -> datetime:
        now = start
        self.kinds = []
        for j, step in enumerate(steps):
            s = f"{salt}:{j}"
            if isinstance(step, Search):
                now += timedelta(seconds=jitter(s, 7, 14))
                results = []
                for k, em in enumerate(step.emails):
                    when = dt(em.when)
                    mid = gmail_id(when, f"email:{em.sender}:{em.subject}:{em.when}")
                    tid = self.world.thread_for(em.thread, mid)
                    if em.key:
                        self.world.emails[em.key] = mid
                    results.append({
                        "id": mid,
                        "thread_id": tid,
                        "query": step.gq,
                        "subject": em.subject,
                        "sender": em.sender,
                        "recipient": em.to,
                        "timestamp": str(when),
                        "label_ids": list(em.labels),
                        "clean_text": em.text,
                        "has_attachments": bool(em.attachments),
                        "attachment_count": len(em.attachments),
                        "attachment_filenames": list(em.attachments),
                    })
                    self.found.append({"id": mid, "thread_id": tid})
                self.log("agent_action", _call("task_email_search", {"search_query": step.query}), now)
                self.log("tool_response", _result("task_email_search", results), now)
                if results:
                    self.vars["thread_id"] = results[0]["thread_id"]
                    self.vars["message_id"] = results[0]["id"]
                self.kinds.append("search")
            elif isinstance(step, People):
                now += timedelta(seconds=jitter(s, 2, 4))
                args = {"query": step.query, "person_fields": "names,emailAddresses"}
                res = _composio({"results": [
                    {"person": {"etag": f"%Eg{_h('etag', s, n) % 10**8:08d}",
                                "resourceName": f"people/c{_h('people', name) % 10**19}",
                                "names": [{"displayName": name}],
                                "emailAddresses": [{"value": email}]}}
                    for n, (name, email) in enumerate(step.results)]}, s)
                self.log("agent_action", _call("gmail_search_people", args), now)
                self.log("tool_response", _result("gmail_search_people", res), now)
                self.kinds.append("people")
            elif isinstance(step, Draft):
                now += timedelta(seconds=jitter(s, 2, 5))
                key = step.key or f"d{item_index}.{j}"
                did = draft_id_for(f"{self.agent.name}:{key}:{ts(now)}")
                mid = gmail_id(now, f"draftmsg:{self.agent.name}:{key}")
                if step.thread == "@found":
                    tid = self.found[-1]["thread_id"]
                elif step.thread:
                    tid = self.world.thread_for(step.thread, mid)
                else:
                    tid = mid
                args: Dict[str, Any] = {"recipient_email": step.to, "subject": step.subject, "body": step.body, "is_html": False}
                if step.thread:
                    args["thread_id"] = tid
                url = f"https://mail.google.com/mail/u/0/#drafts/{did}"
                res = _composio({"display_url": url, "id": did, "message": {"display_url": url, "id": mid, "labelIds": ["DRAFT"], "threadId": tid}}, s)
                self.log("agent_action", _call("gmail_create_draft", args), now)
                self.log("tool_response", _result("gmail_create_draft", res), now)
                info = {"to": step.to, "subject": step.subject, "body": step.body, "draft_id": did, "thread_id": tid}
                self.drafts[key] = info
                self.last_draft = key
                self.vars.update(draft_id=did, thread_id=tid, to=step.to, subject=step.subject, draft_block=_draft_block(info))
                self.kinds.append("draft")
            elif isinstance(step, Send):
                now += timedelta(seconds=jitter(s, 2, 4))
                info = self.drafts[step.key or self.last_draft]
                sent = gmail_id(now, f"sent:{info['draft_id']}")
                res = _composio({"display_url": f"https://mail.google.com/mail/u/0/#inbox/{info['thread_id']}", "id": sent, "labelIds": ["SENT"], "threadId": info["thread_id"]}, s)
                self.log("agent_action", _call("gmail_execute_draft", {"draft_id": info["draft_id"]}), now)
                self.log("tool_response", _result("gmail_execute_draft", res), now)
                self.vars.update(sent_id=sent, draft_id=info["draft_id"], thread_id=info["thread_id"], to=info["to"], subject=info["subject"],
                                 draft_block=_draft_block(info))
                self.kinds.append("send")
            elif isinstance(step, Forward):
                now += timedelta(seconds=jitter(s, 2, 4))
                mid = self.world.emails[step.email_key]
                new = gmail_id(now, f"fwd:{mid}:{step.to}")
                args = {"message_id": mid, "recipient_email": step.to, "additional_text": step.text}
                res = _composio({"id": new, "labelIds": ["SENT"], "threadId": new}, s)
                self.log("agent_action", _call("gmail_forward_email", args), now)
                self.log("tool_response", _result("gmail_forward_email", res), now)
                self.vars.update(sent_id=new)
                self.kinds.append("forward")
            elif isinstance(step, Trig):
                now += timedelta(seconds=jitter(s, 2, 5))
                tid = self.world.trigger_ids[(self.agent.name, item_index, j)]
                start = datetime.fromisoformat(step.start).replace(tzinfo=TZ)
                args = {"payload": step.payload}
                if step.rrule:
                    args["recurrence_rule"] = step.rrule
                args["start_time"] = start.isoformat()
                rec = None
                if step.rrule:
                    rec = f"DTSTART;TZID=America/Toronto:{start.strftime('%Y%m%dT%H%M%S')}\nRRULE:{step.rrule}"
                res = {"trigger_id": tid, "status": "active", "next_trigger": utc_z(start), "start_time": utc_z(start),
                       "timezone": "America/Toronto", "recurrence_rule": rec}
                self.log("agent_action", f"createTrigger succeeded | trigger_id={tid}", now)
                self.log("agent_action", _call("createTrigger", args), now)
                self.log("tool_response", _result("createTrigger", res), now)
                self.vars.update(trigger_id=str(tid))
                self.kinds.append("trigger")
            else:  # pragma: no cover - authoring error
                raise TypeError(f"unknown step {step!r}")
        return now


_DRAFT_RESP = [
    "Draft created. It has not been sent.\n\n{draft_block}\n\nWaiting for the user's explicit confirmation before sending.",
    "The draft was created successfully and has not been sent.\n\n**Draft details:**\n{draft_block}\n\nPlease have the user review this draft and confirm before I send it.",
    "Draft is ready (not sent).\n\n{draft_block}\n\nI'll send it only after the user confirms.",
]
_SEND_RESP = [
    "The email was sent successfully.\n\n- **To:** {to}\n- **Subject:** {subject}\n- **Draft ID sent:** {draft_id}\n- **Sent message ID:** {sent_id} (thread {thread_id}), labeled SENT\n\nNo new draft was created.",
    "The draft was sent successfully.\n\n- **Draft ID sent:** {draft_id}\n- **Sent message ID:** {sent_id}\n- **Thread ID:** {thread_id}\n- **To:** {to}\n- **Subject:** {subject}\n- **Label:** SENT",
]
_COMPOSE_SEND_RESP = (
    "The email was sent successfully. I created the draft with the exact approved text and sent it right away.\n\n"
    "- **To:** {to}\n- **Subject:** {subject}\n- **Draft ID:** {draft_id}\n- **Sent message ID:** {sent_id} (thread {thread_id}), labeled SENT"
)
_SEND_INSTR = [
    'The user confirmed. Send the existing draft (Draft ID {draft_id}) to {to} with subject "{subject}" exactly as written. Do not create a new draft. Report back the sent message ID, or the error if it fails.',
    'User approved the draft. Send Draft ID {draft_id} (to {to}, subject "{subject}") as is, without changes, and confirm once it has gone out.',
    'The user said to send it. Please send the existing draft {draft_id} to {to} exactly as written; do not edit the body or create another draft. Report the sent message ID.',
]
_ASKS = [
    "Send it as is, or want changes?",
    "Look ok to send?",
    "Want me to send it?",
    "Good to go, or tweak anything?",
]


def default_resp(kinds: List[str], salt: str) -> str:
    if kinds and kinds[-1] == "send" and "draft" in kinds:
        return _COMPOSE_SEND_RESP
    if kinds and kinds[-1] == "send":
        return _SEND_RESP[_h(salt, "s") % len(_SEND_RESP)]
    if kinds and kinds[-1] == "draft":
        return _DRAFT_RESP[_h(salt, "d") % len(_DRAFT_RESP)]
    raise ValueError(f"no default response for {kinds} ({salt})")


def render_agent(world: World, agent: Agent) -> Tuple[List[Tuple[str, str, datetime]], List[Entry]]:
    """Render one agent: its log lines and the conversation entries its episodes produce."""
    r = AgentRender(world, agent)
    convo: List[Entry] = []
    for i, item in enumerate(agent.items):
        salt = f"{agent.name}:{i}"
        episode = salt
        if isinstance(item, Req):
            now = dt(item.t)
            first = True
            for e in item.pre:
                if not first:
                    gap = e.gap if e.gap is not None else (jitter(f"{salt}:{len(convo)}", 15, 40) if isinstance(e, U) else jitter(f"{salt}:{len(convo)}", 2, 4))
                    now += timedelta(seconds=gap)
                first = False
                convo.append(Entry(_TAG[type(e)], e.text, now, episode))
            dispatch = now
            instr = fill(item.instr, _instr_vars(r, item))
            r.log("agent_request", instr, dispatch)
            cursor = dispatch
            if item.wait:
                cursor = dispatch + timedelta(seconds=jitter(salt + "w", 1, 2))
                convo.append(Entry("wait", item.wait, cursor, episode))
            end = r.run_steps(item.steps, cursor, salt, i)
            resp_t = end + timedelta(seconds=jitter(salt + "r", 1, 3))
            resp = fill(item.resp if item.resp is not None else default_resp(r.kinds, salt), r.vars)
            r.log("agent_response", resp, resp_t)
            convo.append(Entry("agent_message", f"[SUCCESS] {agent.name}: {resp.strip()}", resp_t, episode))
            _post(convo, item.post, r, resp_t, salt, episode)
        elif isinstance(item, Fire):
            start = dt(item.t)
            end = r.run_steps(item.steps, start, salt, i)
            resp_t = end + timedelta(seconds=jitter(salt + "r", 1, 3))
            resp = fill(item.resp, r.vars)
            r.log("agent_response", resp, resp_t)
            convo.append(Entry("agent_message", f"[SUCCESS] {agent.name}: {resp.strip()}", resp_t, episode))
            _post(convo, item.post, r, resp_t, salt, episode)
        else:  # pragma: no cover
            raise TypeError(item)
    return r.lines, convo


def _instr_vars(r: AgentRender, item: Req) -> Dict[str, str]:
    values = dict(r.vars)
    if r.last_draft:
        d = r.drafts[r.last_draft]
        values.update(draft_id=d["draft_id"], to=d["to"], subject=d["subject"], thread_id=d["thread_id"])
    return values


def _post(convo: List[Entry], post: Optional[List[Any]], r: AgentRender, resp_t: datetime, salt: str, episode: str) -> None:
    if post is None:
        raise ValueError(f"missing post for {salt}")
    now = resp_t
    for k, e in enumerate(post):
        if isinstance(e, DraftView):
            now += timedelta(seconds=jitter(f"{salt}:pv{k}", 3, 6))
            d = r.drafts[r.last_draft]
            convo.append(Entry("poke_reply", f"To: {d['to']}\nSubject: {d['subject']}\n\n{d['body']}", now, episode))
            convo.append(Entry("poke_reply", e.ask, now, episode))
            continue
        default = jitter(f"{salt}:p{k}", 15, 45) if isinstance(e, U) else jitter(f"{salt}:p{k}", 2, 4)
        now += timedelta(seconds=e.gap if e.gap is not None else default)
        convo.append(Entry(_TAG[type(e)], e.text, now, episode))


_TAG = {U: "user_message", P: "poke_reply", W: "wait"}


def send_req(t: str, user: str, ack: str, done: str, variant: int = 0, wait: Optional[str] = None) -> Req:
    """Shorthand: the user confirms the agent's pending draft and the same agent sends it."""
    return Req(t, [U(user), P(ack)], _SEND_INSTR[variant % len(_SEND_INSTR)], [Send()], post=[P(done)], wait=wait)


def compose_send(t: str, pre: List[Any], to: str, subject: str, body: str, done: str, thread: Optional[str] = None,
                 note: str = "", wait: Optional[str] = None) -> Req:
    """Shorthand: Poke composed the draft itself, the user approved, the agent creates + sends it."""
    instr = ("The user reviewed and approved this email. Create it and send it exactly as written, with no changes:\n\n"
             f"To: {to}\nSubject: {subject}\n\nBody:\n{body}\n\n")
    if note:
        instr += note + "\n\n"
    instr += "After sending, reply with confirmation including the recipient, subject, and sent message ID."
    return Req(t, pre, instr, [Draft(to, subject, body, thread=thread), Send()], post=[P(done)], wait=wait)


def composed_pre(user: str, to: str, subject: str, body: str, ask: str, confirm: str, ack: str, confirm_gap: int = 40) -> List[Any]:
    return [U(user), P(f"To: {to}\nSubject: {subject}\n\n{body}", gap=6), P(ask, gap=0), U(confirm, gap=confirm_gap), P(ack)]


# =============================================================================================
# CORE AGENTS (25). Owner of each counterpart; see world.md.
# =============================================================================================

CELESTE = "Celeste Moreau <celeste@harrowhillestate.ca>"
PRIYA_N = "Priya Natarajan <priya@northfoldstudio.ca>"
PRIYA_S = "Priya Sandhu <priya@lumenandlinen.ca>"
DMITRI = "Dmitri Volkov <dmitri@ironbarkreno.ca>"
HANA = "Hana Ishikawa <hana.ishikawa@copperleafdata.com>"
WENDELL = "Wendell Achebe <wendell.achebe@brightmoorcu.ca>"
GABE = "Gabe Lindqvist <gabe@northfoldstudio.ca>"

HH_INQ_BODY = ("Hi there,\n\nMy partner Jules and I are planning our wedding for June 2027 and Harrow Hill is at the top of our list. "
               "Do you have any Saturdays available that month? We're expecting around 110 guests.\n\n"
               "We'd also love to book a tour in the next few weeks if possible.\n\nThanks so much,\nTheo Marchetti")
HH_JUNE12_BODY = ("Hi Celeste,\n\nThanks again for the tour, we loved it. We'd like to book Saturday, June 12, 2027 and can sign the contract this week.\n\n"
                  "Could you send over the deposit schedule so we can plan for it?\n\nBest,\nTheo")
HH_DEP_BODY = ("Hi Celeste,\n\nJust a heads-up that I sent the $4,000 second deposit for our June 12, 2027 wedding by e-transfer this morning.\n\n"
               "Could you confirm once it comes through?\n\nThanks!\nTheo")

A_HARROW = Agent("Harrow Hill Venue Deposit", [
    compose_send("2026-07-21 10:12:05",
                 composed_pre("can you email harrow hill estate and ask if they have any saturdays open in june 2027? jules and i are touring venues. events@harrowhillestate.ca",
                              "events@harrowhillestate.ca", "June 2027 wedding availability", HH_INQ_BODY, "Here's the inquiry. Send it as is?", "yes send", "Sending.", confirm_gap=50),
                 "events@harrowhillestate.ca", "June 2027 wedding availability", HH_INQ_BODY, "Sent to Harrow Hill. Fingers crossed for a June Saturday.", thread="hh",
                 wait="Waiting for the venue inquiry to be sent before confirming to the user."),
    Req("2026-08-19 19:20:10",
        [U("celeste from harrow hill got back to us a while ago w dates. reply and tell her we want saturday june 12 and we can sign the contract this week. also ask what the deposit schedule is"),
         P("Love that. Finding her email and drafting the reply.")],
        "Find the reply from Celeste Moreau (events coordinator at Harrow Hill Estate, celeste@harrowhillestate.ca) in the thread about June 2027 wedding "
        "availability. Then draft (do not send) a reply in that thread telling her Theo and Jules would like to book Saturday, June 12, 2027, that they can "
        "sign the contract this week, and asking what the deposit schedule looks like. Report the draft verbatim plus a one-line summary of what Celeste said.",
        [Search("Emails from celeste@harrowhillestate.ca about June 2027 wedding dates", "from:celeste@harrowhillestate.ca after:2026/07/21",
                [Email(CELESTE, "Re: June 2027 wedding availability", "2026-07-27 15:42:10",
                       "Hi Theo,\n\nThanks for reaching out! For June 2027 we currently have Saturday June 12 and Saturday June 26 open. Our garden ceremony + barn reception package fits up to 140 guests.\n\nI'd be happy to show you both around. Would Saturday Aug 8 at 11am work for a tour?\n\nWarmly,\nCeleste Moreau\nEvents Coordinator, Harrow Hill Estate",
                       thread="hh")]),
         Draft("celeste@harrowhillestate.ca", "Re: June 2027 wedding availability", HH_JUNE12_BODY, thread="hh")],
        resp="Found Celeste's reply (Jul 27, 3:42 PM): June 12 and June 26, 2027 were open, the garden ceremony + barn reception package fits up to 140 guests, "
             "and she offered a tour on Aug 8 at 11am.\n\nDraft reply created in the same thread (not sent):\n\n{draft_block}\n- **Thread ID:** {thread_id}\n\n"
             "Waiting for the user's confirmation before sending.",
        post=[DraftView("Draft's in her thread. Send?")]),
    send_req("2026-08-19 19:23:30", "send it", "Sending now.", "Sent. June 12 is officially in motion.", 1),
    Req("2026-10-15 08:05:12",
        [U("i just e-transferred harrow hill the $4k second deposit. can you let celeste know so she watches for it"),
         P("Nice. Drafting a quick note to Celeste.")],
        "Draft (do not send) a short email to Celeste Moreau at Harrow Hill Estate (celeste@harrowhillestate.ca), in the existing wedding thread, letting her "
        "know Theo sent the $4,000 second deposit for the June 12, 2027 wedding by e-transfer this morning (October 15, 2026), and asking her to confirm once "
        "it's received. Report the exact draft.",
        [Draft("celeste@harrowhillestate.ca", "Second deposit sent - June 12, 2027", HH_DEP_BODY, thread="hh")],
        post=[DraftView("Here's the note for Celeste. Good to send?")],
        wait="Waiting for the deposit note draft from the execution agent."),
    send_req("2026-10-15 08:07:01", "yep send", "Sending.", "Sent. Celeste knows the $4k is on its way.", 2),
])

PR_REVIEW_BODY = ("Hi Priya,\n\nCan we lock in the Q4 roadmap review for the week of Aug 24? Happy to work around your team's schedule.\n\n"
                  "Before then, what does eng need from product? I'm thinking prioritized epics and rough sizing asks, but tell me what would actually help.\n\nThanks,\nTheo")
PR_NUDGE_BODY = ("Hi Priya,\n\nQuick nudge on the Q4 roadmap doc. Any chance I can see a draft before Wednesday? Even a rough version helps.\n\nThanks!\nTheo")

A_PRIYA_N = Agent("Priya Roadmap Sync", [
    Req("2026-07-31 09:20:30",
        [U("email priya and set up the q4 roadmap review for the week of aug 24. ask what eng needs from product before then"),
         P("Got it. Drafting it for Priya.")],
        "Draft (do not send) an email from Theo to Priya Natarajan, Northfold's engineering lead (look up her address in contacts), proposing the Q4 "
        "roadmap review for the week of August 24, 2026 and asking what engineering needs from product before then. Keep it short and collegial. "
        "Report back the exact draft.",
        [People("Priya Natarajan", [("Priya Natarajan", "priya@northfoldstudio.ca")]),
         Draft("priya@northfoldstudio.ca", "Q4 roadmap review - week of Aug 24", PR_REVIEW_BODY, thread="pr_q4")],
        post=[DraftView("Draft for Priya. Send?")]),
    send_req("2026-07-31 09:23:55", "ya send", "Sending.", "Sent to Priya.", 1),
    Req("2026-08-14 16:02:40",
        [U("did priya reply about the roadmap review?"), P("Checking.")],
        "Check whether Priya Natarajan (priya@northfoldstudio.ca) replied to Theo's email \"Q4 roadmap review - week of Aug 24\" (sent July 31). Summarize "
        "her reply: proposed time and anything she asked for. Do not send anything.",
        [Search("Replies from priya@northfoldstudio.ca to 'Q4 roadmap review - week of Aug 24'", "from:priya@northfoldstudio.ca subject:(Q4 roadmap review) after:2026/07/31",
                [Email(PRIYA_N, "Re: Q4 roadmap review - week of Aug 24", "2026-08-13 18:20:05",
                       "Hey Theo, Tues Aug 25 at 10 works, I'll book the big room. From product we need: ranked epics for Q4, any client deadlines that are hard, and a call on whether the Copperleaf dashboard migration is in or out. Eng estimates will be ready by the 21st. P",
                       thread="pr_q4", labels=("IMPORTANT", "CATEGORY_PERSONAL", "INBOX"))])],
        resp="Yes. Priya Natarajan replied on Aug 13 at 6:20 PM.\n\n- **Proposed time:** Tuesday, Aug 25 at 10:00 AM (she'll book the big room)\n"
             "- **She needs from product:** ranked Q4 epics, hard client deadlines, and a decision on whether the dashboard migration is in or out of Q4\n"
             "- **Eng estimates:** ready by Aug 21\n\nThread ID: {thread_id}. Nothing was sent.",
        post=[P("She did. Review is Tue Aug 25 at 10, big room. She wants ranked epics, hard client deadlines, and an in/out call on the dashboard migration. Eng estimates land the 21st.")]),
    Req("2026-10-14 09:12:20",
        [U("can you nudge priya about the q4 roadmap doc? i need to see it before wednesday"), P("Yep, drafting a nudge.")],
        "Draft (do not send) a short, friendly nudge from Theo to Priya Natarajan (priya@northfoldstudio.ca) asking for the Q4 roadmap doc, ideally a draft "
        "before Wednesday, October 21, 2026. Keep it to two or three sentences. Reply with the exact draft.",
        [Draft("priya@northfoldstudio.ca", "Q4 roadmap doc", PR_NUDGE_BODY)],
        post=[DraftView("Short and sweet. Send?")],
        wait="Waiting for the roadmap nudge draft before replying to the user."),
    send_req("2026-10-14 09:13:40", "send", "Sending.", "Sent. Priya's been nudged.", 2),
    Req("2026-10-16 17:10:05",
        [U("did priya get back to me about the roadmap doc"), P("Looking.")],
        "Check whether Priya Natarajan (priya@northfoldstudio.ca) replied to Theo's Oct 14 email \"Q4 roadmap doc\". Report what she said, including any date she "
        "committed to. Do not draft or send anything.",
        [Search("Reply from priya@northfoldstudio.ca to 'Q4 roadmap doc' since Oct 14", "from:priya@northfoldstudio.ca after:2026/10/14",
                [Email(PRIYA_N, "Re: Q4 roadmap doc", "2026-10-16 11:48:31",
                       "Hey! It'll be ready Monday (19th) EOD, sorry it slipped. I added the two hiring asks we talked about and a section on the client portal rebuild. Will drop the link in our thread. P",
                       labels=("IMPORTANT", "CATEGORY_PERSONAL", "INBOX"))])],
        resp="Priya Natarajan replied today (Oct 16, 11:48 AM):\n\n- The Q4 roadmap doc will be ready **Monday, Oct 19, end of day** (it slipped a bit).\n"
             "- She added the two hiring asks and a section on the client portal rebuild.\n- She'll share the link in the existing thread.\n\nNothing was sent.",
        post=[P("She did. Doc lands Monday EOD. She added the two hiring asks and a client portal rebuild section.")]),
])

DM_QUOTE_BODY = ("Hi Dmitri,\n\nWe're looking to do a full kitchen renovation (new cabinets, counters, flooring, and moving the sink to the island) at our place in Leslieville. "
                 "Could you put together a quote? When would you be able to come by to measure?\n\nThanks,\nTheo Marchetti")
DM_COUNTER_BODY = ("Hi Dmitri,\n\nThanks for the detailed quote. We'd like to go ahead with Ironbark. Would you be able to do it for $36,000 if we supply the backsplash tile ourselves?\n\n"
                   "Let me know and we can lock in dates.\n\nBest,\nTheo")
DM_ACCEPT_BODY = ("Hi Dmitri,\n\n$36,800 works for us. Let's lock in a November 9 start. Send over the contract and deposit details whenever you're ready.\n\nThanks,\nTheo")
DM_CAB_BODY = ("Hi Dmitri,\n\nQuick check: did the cabinet order go in? Want to make sure we're still on track for the Nov 9 start.\n\nThanks,\nTheo")

A_KITCHEN = Agent("Kitchen Reno Quote Follow-up", [
    compose_send("2026-08-06 13:15:22",
                 composed_pre("can you email dmitri at ironbark renovations (dmitri@ironbarkreno.ca)? we want a quote for a full kitchen reno, ask when he can come measure",
                              "dmitri@ironbarkreno.ca", "Kitchen renovation quote", DM_QUOTE_BODY, "Here's what I'd send. Good?", "perfect send it", "Sending."),
                 "dmitri@ironbarkreno.ca", "Kitchen renovation quote", DM_QUOTE_BODY, "Sent to Dmitri. Measuring tape incoming.", thread="dm"),
    Req("2026-08-27 20:41:15",
        [U("did dmitri send the quote? if he did, draft a reply asking if he can do 36k if we supply the backsplash tile"),
         P("Checking for Dmitri's quote.")],
        "Look for a quote from Dmitri Volkov at Ironbark Renovations (dmitri@ironbarkreno.ca) for the kitchen renovation. Summarize the total, timeline, and "
        "payment terms. Then draft (do not send) a reply in that thread saying Theo and Jules want to go ahead and asking whether he can do $36,000 if they "
        "supply the backsplash tile themselves. Report the summary and the exact draft.",
        [Search("Kitchen renovation quote from dmitri@ironbarkreno.ca", "from:dmitri@ironbarkreno.ca after:2026/08/06",
                [Email(DMITRI, "Re: Kitchen renovation quote", "2026-08-25 17:05:44",
                       "Hi Theo, thanks for having me over Saturday. Quote attached: $38,500 + HST all in (demo, cabinets, quartz counters, LVP flooring, plumbing to move the sink to the island, electrical). Roughly 7 weeks on site. 30% deposit to book, 40% at cabinet install, balance on completion. Earliest start is the second week of November. Dmitri",
                       thread="dm", attachments=("Ironbark_Quote_Marchetti_Kitchen.pdf",))]),
         Draft("dmitri@ironbarkreno.ca", "Re: Kitchen renovation quote", DM_COUNTER_BODY, thread="dm")],
        resp="Dmitri Volkov (Ironbark Renovations) sent the quote on Aug 25:\n\n- **Total:** $38,500 + HST (demo, cabinets, quartz counters, LVP flooring, moving the sink to the island, electrical)\n"
             "- **Timeline:** about 7 weeks on site, earliest start second week of November\n- **Payment:** 30% deposit to book, 40% at cabinet install, balance on completion\n"
             "- Quote PDF attached: Ironbark_Quote_Marchetti_Kitchen.pdf\n\nDraft reply in the same thread (not sent):\n\n{draft_block}\n\nWaiting for confirmation before sending.",
        post=[P("Quote's in: $38.5k + HST, ~7 weeks, earliest start 2nd week of Nov. 30% to book."), DraftView("Here's the counter at $36k with your tile. Send?")]),
    send_req("2026-08-27 20:44:02", "send it", "Sending.", "Sent. Ball's in Dmitri's court.", 0),
    compose_send("2026-09-09 12:33:10",
                 composed_pre("dmitri came back at 36.8k + hst w our tile and can hold a nov 9 start. tell him we're in", "dmitri@ironbarkreno.ca",
                              "Re: Kitchen renovation quote", DM_ACCEPT_BODY, "Here's the yes. Send?", "yes", "Sending.", confirm_gap=25),
                 "dmitri@ironbarkreno.ca", "Re: Kitchen renovation quote", DM_ACCEPT_BODY, "Sent. Kitchen starts Nov 9.", thread="dm",
                 note="Send it as a reply in the existing \"Kitchen renovation quote\" thread with Dmitri."),
    compose_send("2026-10-16 10:30:18",
                 composed_pre("can u ask dmitri if the cabinet order went in? want to make sure nov 9 is still happening",
                              "dmitri@ironbarkreno.ca", "Re: Kitchen renovation quote", DM_CAB_BODY, "Quick one for Dmitri. Send?", "ya", "Sending.", confirm_gap=30),
                 "dmitri@ironbarkreno.ca", "Re: Kitchen renovation quote", DM_CAB_BODY, "Sent to Dmitri. I'll flag it when he answers.", thread="dm",
                 note="Send it as a reply in the existing kitchen renovation thread with Dmitri Volkov at Ironbark Renovations.",
                 wait="Waiting for the execution agent to send the cabinet-order check to Dmitri."),
])

A_INBOX = Agent("Inbox Catch-Up Scan", [
    Req("2026-10-17 11:20:33",
        [U("ive been ignoring my inbox all week lol. anything i actually need to deal with?"), P("Scanning it now.")],
        "Scan Theo's inbox for the past week (since October 10, 2026) and list only the emails that need action from him: replies requested, bookings to "
        "confirm, bills, deadlines. Skip newsletters and promotions. For each item give sender, subject, date, what's needed, and any deadline.",
        [Search("Emails from the last 7 days that need a reply or action from Theo (bookings, confirmations, bills, deadlines); exclude newsletters and promotions",
                "in:inbox after:2026/10/10 -category:promotions -category:social",
                [Email("Bramblewood Auto Service <service@bramblewoodauto.ca>", "Time to book your winter tire changeover", "2026-10-14 09:31:07",
                       "Hi Theo, it's that time of year! We have your winter tires in storage. Reply to this email to book your changeover. Available: Sat Oct 24 at 9:00 AM or Tue Oct 27 at 4:30 PM. Changeover + balancing is $89.95 + tax. - Kev, Bramblewood Auto Service",
                       thread="bramblewood", labels=("UNREAD", "CATEGORY_UPDATES", "INBOX")),
                 Email("Riverdale Library <holds@riverdalelibrary.ca>", "2 items ready for pickup", "2026-10-15 07:02:44",
                       "Your holds are ready: 'The Mushroom at the End of the World', 'Slow Productivity'. Pick up by Oct 22.",
                       labels=("UNREAD", "CATEGORY_UPDATES", "INBOX")),
                 Email("Maplecrest Card Services <statements@maplecrestcard.ca>", "Your October statement is ready", "2026-10-16 05:14:20",
                       "Statement balance $1,284.16. Minimum payment $35.00 due Nov 2, 2026.", labels=("UNREAD", "CATEGORY_UPDATES", "INBOX"))])],
        resp="Three emails from the past week need action. Everything else is newsletters or promos.\n\n"
             "1. **Bramblewood Auto Service** (service@bramblewoodauto.ca): \"Time to book your winter tire changeover\" (Oct 14). They're storing Theo's winter "
             "tires and want a reply to book the changeover. Slots: **Sat Oct 24 at 9:00 AM** or **Tue Oct 27 at 4:30 PM**. $89.95 + tax. Reply to that email to book. Thread ID: {thread_id}\n"
             "2. **Riverdale Library**: 2 holds ready, pick up by **Oct 22**. No reply needed.\n"
             "3. **Maplecrest Card Services**: October statement $1,284.16, minimum $35.00 due **Nov 2**.\n\nNothing was sent or drafted.",
        post=[P("Three things:\n1. Bramblewood Auto wants you to book your winter tire changeover. Sat Oct 24 at 9am or Tue Oct 27 at 4:30. Just needs a reply.\n"
                "2. Two library holds, pick up by Oct 22.\n3. Maplecrest statement: $1,284.16, min $35 due Nov 2.\n\nRest is noise."),
              U("ugh ok ill deal w the tire thing later"),
              P("It'll keep. The tires aren't going anywhere.")],
        wait="Waiting for the inbox scan results before replying."),
])

CL_ASK_BODY = ("Hi Hana,\n\nThanks for the renewal notice. Before we decide, could you send our usage report for the last 12 months (seats, dashboard views, API calls)? "
               "A 12% increase is a big jump for us, so we want to see where the value is landing.\n\nThanks,\nTheo")
CL_REPLY_BODY = ("Hi Hana,\n\nThanks for sending the usage report. We'd like to stay with Copperleaf, and we're happy to commit to a two-year term if you can hold "
                 "last year's price of $18,400/year. If that works on your end, send over the paperwork and we'll sign before the Nov 30 renewal date.\n\nBest,\nTheo")

A_COPPERLEAF = Agent("Copperleaf Renewal Thread", [
    Req("2026-09-15 14:05:50",
        [U("hana from copperleaf sent something about our renewal. what's the damage"), P("Finding it.")],
        "Find the recent email from Hana Ishikawa at Copperleaf Data (hana.ishikawa@copperleafdata.com) about Northfold's renewal. Summarize the new price, "
        "the percentage change, the renewal date, and any deadline to respond. Do not reply.",
        [Search("Renewal notice from hana.ishikawa@copperleafdata.com", "from:hana.ishikawa@copperleafdata.com after:2026/09/01",
                [Email(HANA, "Your Copperleaf renewal - Northfold Studio", "2026-09-14 11:22:09",
                       "Hi Theo, your Copperleaf Team plan renews on Nov 30, 2026. New annual price is $20,608 (up 12% from $18,400) reflecting the new forecasting module. Multi-year terms are available. Let me know if you'd like to discuss before Oct 31. Best, Hana Ishikawa, Account Manager, Copperleaf Data",
                       thread="cl", labels=("IMPORTANT", "CATEGORY_UPDATES", "INBOX"))])],
        resp="Found it. Hana Ishikawa (Copperleaf Data) emailed on Sep 14:\n\n- **Renewal date:** Nov 30, 2026 (Team plan)\n- **New price:** $20,608/year, up **12%** "
             "from $18,400\n- **Reason given:** the new forecasting module\n- **Options:** multi-year terms available\n- **Respond by:** Oct 31 if Theo wants to discuss\n\nThread ID: {thread_id}. Nothing was sent.",
        post=[P("Renews Nov 30 at $20,608/yr. That's +12% from $18,400, blamed on a new forecasting module. Multi-year terms are on the table. She wants to talk before Oct 31.")]),
    Req("2026-10-01 10:44:12",
        [U("ask hana for our usage report for the last 12 months before we decide anything"), P("Drafting it.")],
        "Draft (do not send) a reply to Hana Ishikawa (hana.ishikawa@copperleafdata.com) in the Copperleaf renewal thread asking for Northfold's usage report "
        "for the last 12 months (seats, dashboard views, API calls) before deciding on the renewal, and noting the 12% increase is a big jump. Report the exact draft.",
        [Draft("hana.ishikawa@copperleafdata.com", "Re: Your Copperleaf renewal - Northfold Studio", CL_ASK_BODY, thread="cl")],
        post=[DraftView("Here's the ask. Send?")]),
    send_req("2026-10-01 10:46:20", "send", "Sending.", "Sent. Let's see what the numbers say.", 1),
    Req("2026-10-19 19:38:45",
        [U("hana sent the usage report i think. draft a reply saying we'll sign for 2 years if they keep last year's price"),
         P("On it. Pulling up her email and drafting the reply.")],
        "Find Hana Ishikawa's latest email in the Copperleaf renewal thread (hana.ishikawa@copperleafdata.com), which should include the usage report. Briefly "
        "summarize it. Then draft (do not send) a reply in that thread saying Northfold will commit to a two-year term if Copperleaf holds last year's price of "
        "$18,400/year, and that they'd sign before the Nov 30 renewal date. Report the summary and the exact draft so the user can review it.",
        [Search("Latest email from hana.ishikawa@copperleafdata.com with the usage report", "from:hana.ishikawa@copperleafdata.com after:2026/10/01",
                [Email(HANA, "Re: Your Copperleaf renewal - Northfold Studio", "2026-10-19 16:12:40",
                       "Hi Theo, attached is your usage for Oct 2025 - Sep 2026: 14 of 15 seats active, 9,812 dashboard views, 1.2M API calls (up 40% YoY). Happy to talk options. Hana",
                       thread="cl", labels=("UNREAD", "IMPORTANT", "CATEGORY_UPDATES", "INBOX"), attachments=("Northfold_Usage_Oct25-Sep26.pdf",))]),
         Draft("hana.ishikawa@copperleafdata.com", "Re: Your Copperleaf renewal - Northfold Studio", CL_REPLY_BODY, thread="cl")],
        resp="Hana Ishikawa sent the usage report today (Oct 19, 4:12 PM): 14 of 15 seats active, 9,812 dashboard views, 1.2M API calls (up 40% year over year). "
             "PDF attached: Northfold_Usage_Oct25-Sep26.pdf.\n\nDraft reply in the renewal thread (not sent):\n\n{draft_block}\n- **Thread ID:** {thread_id}\n\n"
             "Waiting for the user's explicit confirmation before sending.",
        post=[P("Usage report's in: 14 of 15 seats active, 9.8k dashboard views, API calls up 40%. So you're definitely using it."),
              DraftView("Here's the 2-year-at-last-year's-price reply. Send it, or tweak?")],
        wait="Waiting for the Copperleaf reply draft before showing the user anything."),
])


def _brief_fire(t: str, week: str, items: List[Tuple[str, str, str, str]], resp_lines: List[str], poke: str) -> Fire:
    emails = [Email(s, subj, when, text, labels=("UNREAD", "CATEGORY_UPDATES", "INBOX")) for (s, subj, when, text) in items]
    day = dt(t)
    q = f"Emails about anything due or happening {week}: bills, deliveries, appointments, RSVPs, renewals"
    gq = f"in:inbox after:{(day - timedelta(days=7)).strftime('%Y/%m/%d')} -category:promotions"
    resp = f"Week-ahead rundown ({week}):\n\n" + "\n".join(f"- {line}" for line in resp_lines) + "\n\nNothing needs a reply right now."
    return Fire(t, [Search(q, gq, emails)], resp, [P(poke)])


A_BRIEF = Agent("Sunday Week Ahead Brief", [
    Req("2026-09-09 21:10:14",
        [U("every sunday at 7pm can you give me a rundown of what's coming up that week from my inbox? bills, deliveries, appointments, rsvps, that kind of thing"),
         P("Easy. Setting up a Sunday 7pm rundown.")],
        "Set up a recurring reminder for Theo: every Sunday at 7:00 PM (America/Toronto), scan his inbox for anything due or happening in the coming week "
        "(bills, deliveries, appointments, RSVPs, renewals) and send him a short week-ahead rundown. First run this Sunday, September 13, 2026. Confirm the schedule and trigger ID.",
        [Trig("Scan Theo's inbox for anything due or happening in the coming week (bills, deliveries, appointments, RSVPs, renewals) and send a short week-ahead rundown.",
              "FREQ=WEEKLY;BYDAY=SU", "2026-09-13T19:00:00")],
        resp="Done. Created a recurring trigger (trigger ID {trigger_id}) that runs every Sunday at 7:00 PM America/Toronto, starting Sunday, September 13, 2026. "
             "Each run scans the inbox for bills, deliveries, appointments, RSVPs, and renewals coming up that week and sends a short rundown.",
        post=[P("Done. Every Sunday at 7pm you'll get the week-ahead rundown, starting this Sunday.")]),
    _brief_fire("2026-09-13 19:00:02", "Sep 14-20", [
        ("Larkspur Outfitters <orders@larkspuroutfitters.ca>", "Return received", "2026-09-11 15:40:00", "Refund of $64.99 will post in 3-5 business days."),
        ("Telvio Mobile <billing@telviomobile.ca>", "Your bill is ready", "2026-09-07 06:00:00", "Amount due $74.60 on Sep 14. Autopay is on.")],
        ["Mon Sep 14: Telvio bill $74.60 (autopay on)", "This week: Larkspur refund $64.99 should post"],
        "Light week: Telvio $74.60 Monday (autopay), and your Larkspur refund should show up."),
    _brief_fire("2026-09-20 19:00:04", "Sep 21-27", [
        ("Pantrywise <hello@pantrywise.ca>", "Price update", "2026-09-18 09:00:00", "Boxes go to $79.99 starting Oct 1."),
        ("Leslieville Residents Assoc. <hello@leslievilleresidents.ca>", "Tree planting Sat Sep 26", "2026-09-17 12:00:00", "Volunteers needed Sat Sep 26, 10am.")],
        ["Sat Sep 26: Leslieville tree planting, 10am (volunteers wanted)", "Oct 1: Pantrywise price goes to $79.99/box"],
        "This week: tree planting Sat 10am if you're feeling civic. Pantrywise goes up to $79.99 Oct 1."),
    _brief_fire("2026-09-27 19:00:02", "Sep 28-Oct 4", [
        ("Maplecrest Card Services <statements@maplecrestcard.ca>", "Payment reminder", "2026-09-25 05:10:00", "Minimum payment $35.00 due Sep 28."),
        ("Northline Courier <tracking@northlinecourier.ca>", "Delivery scheduled", "2026-09-26 19:01:00", "Package from Larkspur Outfitters arriving Thu Oct 1.")],
        ["Mon Sep 28: Maplecrest card payment due (balance $1,106.90)", "Thu Oct 1: Larkspur Outfitters delivery"],
        "Maplecrest is due tomorrow ($1,106.90). Larkspur package Thursday."),
    _brief_fire("2026-10-04 19:00:03", "Oct 5-11", [
        ("Telvio Mobile <billing@telviomobile.ca>", "Your bill is ready", "2026-10-02 06:00:00", "Amount due $74.60 on Oct 14. Autopay is on."),
        ("Riverdale Library <holds@riverdalelibrary.ca>", "Library closed Oct 12", "2026-10-03 07:00:00", "All branches closed Monday Oct 12 for Thanksgiving.")],
        ["Mon Oct 12: library closed for Thanksgiving", "Oct 14: Telvio bill $74.60 (autopay on)"],
        "Week ahead: library's closed Thanksgiving Monday, Telvio $74.60 on the 14th. Otherwise clear."),
    _brief_fire("2026-10-11 19:00:02", "Oct 12-18", [
        ("Pantrywise <hello@pantrywise.ca>", "Your next box ships Oct 15", "2026-10-09 08:30:00", "Skip by Oct 13 if you don't want this week's box."),
        ("Maplecrest Card Services <statements@maplecrestcard.ca>", "New statement coming", "2026-10-10 05:00:00", "Your October statement will be ready Oct 16.")],
        ["Tue Oct 13: last day to skip the Pantrywise box", "Fri Oct 16: Maplecrest October statement posts"],
        "Week ahead: skip Pantrywise by Tuesday if you're still drowning in Thanksgiving leftovers. Maplecrest statement lands Friday."),
    _brief_fire("2026-10-18 19:00:03", "Oct 19-25", [
        ("Riverdale Library <holds@riverdalelibrary.ca>", "Reminder: holds expire Oct 22", "2026-10-17 07:00:00", "2 items waiting. Pick up by Oct 22."),
        ("Telvio Mobile <billing@telviomobile.ca>", "Data usage alert", "2026-10-16 21:14:00", "You've used 80% of your 50GB.")],
        ["Thu Oct 22: last day to pick up 2 library holds", "Telvio: 80% of the 50GB data plan used"],
        "Week ahead: library holds expire Thursday, and you've burned 80% of your Telvio data. Easy on the hotspot."),
])

WD_START_BODY = ("Hi Wendell,\n\nOur mortgage term with Brightmoor comes up for renewal on December 1. What do you need from us to get the renewal started, "
                 "and when should we expect an offer?\n\nThanks,\nTheo Marchetti")

A_MORTGAGE = Agent("Mortgage Renewal Paperwork", [
    Req("2026-08-25 21:02:30",
        [U("our mortgage term at brightmoor is up dec 1. email wendell achebe (wendell.achebe@brightmoorcu.ca) and ask what he needs from us to start the renewal"),
         P("On it. Drafting the note to Wendell.")],
        "Draft (do not send) an email from Theo to Wendell Achebe, mortgage advisor at Brightmoor Credit Union (wendell.achebe@brightmoorcu.ca), saying the "
        "Marchetti/Arden mortgage term renews December 1, 2026, and asking what documents he needs to start the renewal and when to expect an offer. Report the exact draft.",
        [Draft("wendell.achebe@brightmoorcu.ca", "Mortgage renewal - Dec 1 term end", WD_START_BODY, thread="wd")],
        post=[DraftView("Draft for Wendell. Send?")]),
    send_req("2026-08-25 21:04:12", "yes pls", "Sending.", "Sent to Wendell.", 0),
    Req("2026-09-03 18:15:45",
        [U("did wendell get back to me about the mortgage stuff"), P("Checking.")],
        "Check for a reply from Wendell Achebe at Brightmoor Credit Union (wendell.achebe@brightmoorcu.ca) to Theo's email \"Mortgage renewal - Dec 1 term end\". "
        "List exactly which documents he needs, any deadlines, and anything he said about rates or timing. Do not send anything.",
        [Search("Reply from wendell.achebe@brightmoorcu.ca about the mortgage renewal", "from:wendell.achebe@brightmoorcu.ca after:2026/08/25",
                [Email(WENDELL, "Re: Mortgage renewal - Dec 1 term end", "2026-09-02 16:40:18",
                       "Hi Theo, happy to help. To prepare the renewal I need: (1) a recent pay stub for you and Jules, (2) your 2026 property tax bill, (3) your 2025 T4s. Once I have those I'll send a renewal offer by Oct 30. We can hold a rate up to 120 days before maturity, so it's worth deciding whether to lock before the Nov 4 rate announcement. Best, Wendell Achebe, Mortgage Advisor, Brightmoor Credit Union",
                       thread="wd")])],
        resp="Wendell Achebe replied on Sep 2 at 4:40 PM. He needs:\n\n1. A recent pay stub for Theo and Jules\n2. The 2026 property tax bill\n3. 2025 T4s\n\n"
             "Once he has them he'll send a **renewal offer by Oct 30**. Brightmoor can hold a rate up to 120 days before maturity, and he suggests deciding "
             "whether to lock **before the Nov 4 rate announcement**. Thread ID: {thread_id}. Nothing was sent.",
        post=[P("He wants pay stubs for you and Jules, the 2026 property tax bill, and your 2025 T4s. Offer by Oct 30. He also says decide on locking a rate before the Nov 4 announcement.")]),
    Req("2026-09-10 20:48:05",
        [U("ok send wendell my latest pay stub and the property tax bill, both should be in my email. jules will send hers + the t4s herself"),
         P("Finding them and forwarding to Wendell.")],
        "Find Theo's most recent pay stub email and the 2026 property tax bill email, then forward both to Wendell Achebe (wendell.achebe@brightmoorcu.ca) for "
        "the mortgage renewal, with a one-line note that Jules will send her pay stub and the 2025 T4s separately. The user has approved forwarding these. "
        "Report what was forwarded with message IDs.",
        [Search("Most recent Northfold pay stub email and the 2026 property tax bill", "(subject:(pay stub) OR subject:(property tax)) after:2026/06/01",
                [Email("Northfold Payroll <payroll@northfoldstudio.ca>", "Your pay stub for Aug 16-31, 2026", "2026-09-01 08:00:00",
                       "Your pay stub for the period Aug 16-31, 2026 is attached.", labels=("CATEGORY_UPDATES", "INBOX"), key="paystub",
                       attachments=("PayStub_2026-08-31_TMarchetti.pdf",)),
                 Email("City Revenue Services <taxbilling@torontorevenue-notices.ca>", "2026 Final Property Tax Bill", "2026-06-12 09:15:00",
                       "Your 2026 final property tax bill is attached. Installments due Jul 2, Aug 4, Sep 1.", labels=("CATEGORY_UPDATES", "INBOX"), key="proptax",
                       attachments=("2026_Final_Tax_Bill.pdf",))]),
         Forward("paystub", "wendell.achebe@brightmoorcu.ca", "Hi Wendell, my latest pay stub for the renewal. Jules will send hers and our 2025 T4s separately. Theo"),
         Forward("proptax", "wendell.achebe@brightmoorcu.ca", "And here's our 2026 property tax bill. Thanks, Theo")],
        resp="Forwarded both to Wendell Achebe (wendell.achebe@brightmoorcu.ca):\n\n1. **Pay stub** (Aug 16-31, 2026, from Northfold Payroll) with the note that Jules "
             "will send her pay stub and the 2025 T4s separately\n2. **2026 Final Property Tax Bill**\n\nLast forwarded message ID: {sent_id}. Still outstanding: Jules' pay "
             "stub and the 2025 T4s. Wendell said he'd send the renewal offer by Oct 30, with a rate-lock decision ideally before the Nov 4 announcement.",
        post=[P("Done. Your pay stub and the property tax bill are with Wendell. Still need Jules' stub + T4s from her. Offer by Oct 30, and the lock-or-wait call before Nov 4.")]),
])

PS_INQ_BODY = ("Hi Priya,\n\nMy fiancé Jules and I are getting married in June 2027 and we love your work. Do you do engagement shoots, and what packages do you offer? "
               "We'd be looking at early October.\n\nThanks!\nTheo")
PS_BOOK_BODY = ("Hi Priya,\n\nWe'd love to book Saturday, October 10 for the golden-hour engagement shoot at Humber Bay Park (the 90-minute package). "
                "Happy to send the $300 retainer. What's the best way to pay?\n\nThanks,\nTheo")

A_ENGAGE = Agent("Engagement Shoot Booking", [
    Req("2026-07-27 12:30:14",
        [U("can you email priya sandhu at lumen & linen photography (priya@lumenandlinen.ca)? ask about engagement shoot packages, we're thinking early october"),
         P("Drafting it now.")],
        "Draft (do not send) an email from Theo to Priya Sandhu, photographer at Lumen & Linen Photography (priya@lumenandlinen.ca), asking about her engagement "
        "shoot packages and pricing for early October 2026. Mention Theo and his fiancé Jules are getting married in June 2027. Report the exact draft.",
        [Draft("priya@lumenandlinen.ca", "Engagement shoot inquiry", PS_INQ_BODY, thread="ps")],
        post=[DraftView("Here's the inquiry for Priya at Lumen & Linen. Send?")]),
    send_req("2026-07-27 12:33:02", "send it", "Sending.", "Sent to Lumen & Linen.", 2),
    compose_send("2026-08-12 12:14:20",
                 composed_pre("priya at lumen & linen got back: $650 for 90 min, oct 3 or oct 10. book sat oct 10 golden hour at humber bay park and ask how to pay the $300 retainer",
                              "priya@lumenandlinen.ca", "Re: Engagement shoot inquiry", PS_BOOK_BODY, "Booking reply for Priya. Send?", "yup", "Sending.", confirm_gap=30),
                 "priya@lumenandlinen.ca", "Re: Engagement shoot inquiry", PS_BOOK_BODY, "Sent. Oct 10 golden hour, Humber Bay. Practice your candid laugh.", thread="ps",
                 note="Send it as a reply in the existing \"Engagement shoot inquiry\" thread with Priya Sandhu at Lumen & Linen Photography."),
    Req("2026-10-15 12:40:22",
        [U("jules wants to know when the engagement photos are coming. did priya say?"),
         P("Checking with the photographer's emails.")],
        "Check Theo's emails from Priya Sandhu at Lumen & Linen Photography (priya@lumenandlinen.ca) since the October 10 engagement shoot for any date she "
        "gave for delivering the proofs or gallery. Report what she said. Do not send anything.",
        [Search("Emails from priya@lumenandlinen.ca since Oct 10 about proofs or the gallery", "from:priya@lumenandlinen.ca after:2026/10/10",
                [Email(PRIYA_S, "Thank you + what's next", "2026-10-12 09:30:17",
                       "Theo & Jules, Saturday was magic, the light at the pier was unreal. You'll get an online proofing gallery by Fri Oct 23. Pick your favourites there and I'll deliver final edits two weeks after. Priya",
                       thread="ps")])],
        resp="Priya Sandhu (Lumen & Linen) emailed on Oct 12: the **online proofing gallery** will arrive **by Friday, Oct 23**. Theo and Jules pick favourites "
             "there, and final edits come two weeks after that. Thread ID: {thread_id}. Nothing was sent.",
        post=[P("Proofs gallery by Fri Oct 23, per Priya at Lumen & Linen. You pick favourites, then finals two weeks later. Tell Jules to hold tight.")],
        wait="Waiting for the photographer email check before replying."),
])

MB_SIGNUP_BODY = ("Hi Marco,\n\nI'd like to sign up for the fall Sunday league, full season. Same team as spring (Leslieville Lions) if there's a spot.\n\n"
                  "Let me know how to pay.\n\nThanks,\nTheo Marchetti")
MB_OUT_BODY = ("Hi Marco,\n\nBad news. My knee isn't cooperating, so I'm going to sit out the rest of the fall season. Sorry for the late notice. "
               "Could you let the Lions know? I'll be back in the spring.\n\nThanks,\nTheo")

A_MARCO = Agent("Email to Marco Soccer League", [
    compose_send("2026-08-11 08:50:40",
                 composed_pre("email marco at riverdale rec soccer (marco@riverdalerecsoccer.ca) and sign me up for the fall sunday league, full season, same team as spring",
                              "marco@riverdalerecsoccer.ca", "Fall Sunday league sign-up", MB_SIGNUP_BODY, "Sign-up for Marco. Send?", "send", "Sending.", confirm_gap=25),
                 "marco@riverdalerecsoccer.ca", "Fall Sunday league sign-up", MB_SIGNUP_BODY, "Sent. Lions, assemble.", thread="mb"),
    compose_send("2026-10-13 18:20:12",
                 composed_pre("can you tell marco im out for the rest of the season? knee's still bad", "marco@riverdalerecsoccer.ca",
                              "Re: Fall Sunday league sign-up", MB_OUT_BODY, "Here's the note. Send?", "yeah", "Sending.", confirm_gap=35),
                 "marco@riverdalerecsoccer.ca", "Re: Fall Sunday league sign-up", MB_OUT_BODY, "Sent. Sorry, the knee wins this round.", thread="mb",
                 note="Send it in the existing fall league sign-up thread with Marco Bellandi."),
])

GB_AGENDA_BODY = ("Hi Gabe,\n\nHere's a first pass at the Cedar Hollow offsite agenda (Oct 21-22):\n\nDay 1 (Wed)\n- 10:00 Kickoff + coffee\n- 10:30 2026 retro: what worked, what didn't\n"
                  "- 13:00 Lunch\n- 14:00 2027 planning: revenue targets + service lines\n- 17:00 Free time / sauna\n\nDay 2 (Thu)\n- 09:30 Hiring plan (senior designer, 2 engineers)\n"
                  "- 12:00 Lunch\n- 13:00 Client roadmap review\n- 15:00 Wrap + action items\n\nHappy to adjust.\nTheo")
GB_FINAL_BODY = ("Hi Gabe,\n\nFinal agenda for Cedar Hollow (Oct 21-22). Changes from the draft: added a 30-min client roadmap slot right after lunch on Day 2 and moved wrap-up to 15:30.\n\n"
                 "Day 1 (Wed): 10:00 kickoff, 10:30 retro, 13:00 lunch, 14:00 2027 planning, 17:00 free time\nDay 2 (Thu): 09:30 hiring plan, 12:00 lunch, 13:00 client roadmap (30 min), "
                 "13:30 portal rebuild deep-dive, 15:30 wrap + action items\n\nSee you Wednesday.\nTheo")

A_GABE = Agent("Email to Gabe Offsite Agenda", [
    Req("2026-09-28 11:05:30",
        [U("gabe wants a draft agenda for the oct 21-22 offsite at cedar hollow lodge. day 1 retro + 2027 planning, day 2 hiring + client roadmap. draft him something"),
         P("Drafting an agenda for Gabe.")],
        "Draft (do not send) an email from Theo to Gabe Lindqvist, Northfold's co-founder/CEO (gabe@northfoldstudio.ca), with a proposed agenda for the team offsite "
        "at Cedar Hollow Lodge on October 21-22, 2026: Day 1 kickoff, 2026 retro, and 2027 planning; Day 2 hiring plan and client roadmap review. Include rough "
        "times. Report the exact draft.",
        [Draft("gabe@northfoldstudio.ca", "Offsite agenda - Cedar Hollow, Oct 21-22", GB_AGENDA_BODY, thread="gb")],
        post=[DraftView("Agenda draft for Gabe. Send?")],
        wait="Waiting for the agenda draft from the execution agent."),
    send_req("2026-09-28 11:08:44", "looks good send", "Sending.", "Sent to Gabe.", 0),
    Req("2026-10-15 16:20:18",
        [U("send gabe the final agenda. add a 30 min client roadmap slot right after lunch on day 2 and push wrap to 3:30"),
         P("Updating it and drafting the final for Gabe.")],
        "Draft (do not send) a reply to Gabe Lindqvist (gabe@northfoldstudio.ca) in the offsite agenda thread with the final agenda for Cedar Hollow (Oct 21-22). "
        "Changes from the earlier draft: add a 30-minute client roadmap slot right after lunch on Day 2, and move wrap-up to 3:30 PM. Report the exact draft.",
        [Draft("gabe@northfoldstudio.ca", "Re: Offsite agenda - Cedar Hollow, Oct 21-22", GB_FINAL_BODY, thread="gb")],
        post=[DraftView("Final agenda for Gabe. Send?")]),
    send_req("2026-10-15 16:22:30", "send", "Sending.", "Sent. Gabe has the final agenda.", 2),
])

FW_BODY = ("Hi Marcus,\n\nThanks for reaching out. Yes, we're interested in help with the senior product designer search. Could we do a call Thursday at 2pm?\n\nBest,\nTheo")

A_FERNWAY = Agent("Fernway Designer Search", [
    Req("2026-08-13 10:30:45",
        [U("marcus from fernway talent emailed about helping with the senior designer search. reply that we're interested and can do a call thurs 2pm"),
         P("Finding his email and drafting a reply.")],
        "Find the recent email from Marcus Oyelaran at Fernway Talent (marcus@fernwaytalent.com) about Northfold's senior designer search. Draft (do not send) a "
        "reply in that thread saying Northfold is interested and proposing a call Thursday, August 20 at 2:00 PM. Report the exact draft.",
        [Search("Email from marcus@fernwaytalent.com about senior designer search", "from:marcus@fernwaytalent.com after:2026/08/01",
                [Email("Marcus Oyelaran <marcus@fernwaytalent.com>", "Senior product designer search - Northfold", "2026-08-12 15:10:00",
                       "Hi Theo, saw Northfold is hiring a senior product designer. We placed two designers at studios your size this year. 20% fee, 90-day guarantee. Open to a quick call? Marcus Oyelaran, Fernway Talent",
                       thread="fw")]),
         Draft("marcus@fernwaytalent.com", "Re: Senior product designer search - Northfold", FW_BODY, thread="fw")],
        resp="Found Marcus Oyelaran's email (Aug 12): Fernway Talent offers a 20% fee and a 90-day guarantee, and has placed two designers at similar-sized studios this year.\n\n"
             "Draft reply (not sent):\n\n{draft_block}\n\nWaiting for confirmation.",
        post=[DraftView("Reply to Marcus. Send?")]),
    send_req("2026-08-13 10:32:20", "ya", "Sending.", "Sent. Call request is with Marcus.", 1),
])

A_HYDRO = Agent("Hydro Bill Reminder", [
    Req("2026-07-24 08:40:10",
        [U("remind me on the 20th of every month to check the hydro bill before it's due"), P("Will do. Setting it up.")],
        "Create a monthly reminder for Theo on the 20th of every month at 9:00 AM (America/Toronto) to review and pay the Lakeport Hydro bill before it's due. "
        "When it fires, check his inbox for the latest Lakeport Hydro bill and include the amount and due date. Start August 20, 2026. Confirm with the trigger ID.",
        [Trig("Remind Theo to review and pay his Lakeport Hydro bill. Check the inbox for the latest Lakeport Hydro bill email and include the amount and due date.",
              "FREQ=MONTHLY;BYMONTHDAY=20", "2026-08-20T09:00:00")],
        resp="Created a monthly reminder (trigger ID {trigger_id}) for the 20th of every month at 9:00 AM America/Toronto, starting August 20, 2026. Each time it fires "
             "I'll look up the latest Lakeport Hydro bill and include the amount and due date.",
        post=[P("Set. On the 20th of every month at 9am I'll nudge you with the hydro amount and due date.")]),
    Fire("2026-08-20 09:00:02",
         [Search("Latest Lakeport Hydro bill", "from:billing@lakeporthydro.ca after:2026/08/01",
                 [Email("Lakeport Hydro <billing@lakeporthydro.ca>", "Your Lakeport Hydro bill is ready", "2026-08-12 06:05:00",
                        "Account ending 4471. Amount due: $142.87. Due date: Aug 28, 2026.", labels=("CATEGORY_UPDATES", "INBOX"))])],
         "Reminder: Lakeport Hydro bill (account ending 4471) is **$142.87**, due **Aug 28, 2026**.",
         [P("Hydro reminder: $142.87 due Aug 28. AC season strikes again.")]),
    Fire("2026-09-20 09:00:03",
         [Search("Latest Lakeport Hydro bill", "from:billing@lakeporthydro.ca after:2026/09/01",
                 [Email("Lakeport Hydro <billing@lakeporthydro.ca>", "Your Lakeport Hydro bill is ready", "2026-09-11 06:05:00",
                        "Account ending 4471. Amount due: $118.40. Due date: Sep 28, 2026.", labels=("CATEGORY_UPDATES", "INBOX"))])],
         "Reminder: Lakeport Hydro bill (account ending 4471) is **$118.40**, due **Sep 28, 2026**.",
         [P("Hydro reminder: $118.40, due Sep 28.")]),
])

TD_BODY = ("Hi,\n\nI have a cleaning booked for Tuesday, Oct 6. Could we move it to a late-afternoon slot the following week instead?\n\nThanks,\nTheo Marchetti")

A_DENTIST = Agent("Dentist Cleaning Reschedule", [
    compose_send("2026-09-29 13:02:44",
                 composed_pre("tidewater dental has me down for a cleaning oct 6, can you ask them to move it to a late afternoon the week after? frontdesk@tidewaterdental.ca",
                              "frontdesk@tidewaterdental.ca", "Rescheduling my Oct 6 cleaning", TD_BODY, "This work?", "yes send", "Sending.", confirm_gap=30),
                 "frontdesk@tidewaterdental.ca", "Rescheduling my Oct 6 cleaning", TD_BODY, "Sent to Tidewater Dental."),
])

ROSA_BODY = ("Hi Mom,\n\nWhat time does your flight land on Oct 9? I'll pick you up at the airport.\n\nLove,\nTheo")

A_MOM = Agent("Mom Thanksgiving Visit", [
    compose_send("2026-09-14 19:40:05",
                 composed_pre("email my mom (rosa.marchetti@quaymail.net) and ask what time her flight lands oct 9, ill pick her up",
                              "rosa.marchetti@quaymail.net", "Your flight on Oct 9", ROSA_BODY, "Send this to your mom?", "yes", "Sending.", confirm_gap=20),
                 "rosa.marchetti@quaymail.net", "Your flight on Oct 9", ROSA_BODY, "Sent to your mom."),
    Req("2026-10-08 21:30:15",
        [U("mom lands tomorrow at 3:40, pearson t1. remind me an hour before so i leave on time"), P("Setting a reminder for 2:40.")],
        "Create a one-time reminder for Theo on Friday, October 9, 2026 at 2:40 PM (America/Toronto), one hour before his mom Rosa lands at Pearson Terminal 1 "
        "(flight 1180 from Halifax, arriving 3:40 PM), telling him to leave for the airport. Confirm the trigger ID.",
        [Trig("Remind Theo to leave for Pearson Terminal 1 now: his mom Rosa's flight 1180 from Halifax lands at 3:40 PM.", None, "2026-10-09T14:40:00")],
        resp="Created a one-time reminder (trigger ID {trigger_id}) for Friday, Oct 9, 2026 at 2:40 PM America/Toronto: leave for Pearson T1, Rosa's flight 1180 lands at 3:40 PM.",
        post=[P("Set for 2:40 tomorrow.")]),
    Fire("2026-10-09 14:40:02", [], "Reminder: time to leave for Pearson Terminal 1. Rosa's flight 1180 from Halifax lands at 3:40 PM.",
         [P("Time to head out. Your mom lands at 3:40, T1.")]),
])

TW_BODY = ("Hi Tomasz,\n\nI'm happy to host book club on Thursday, Sept 17 at our place in Leslieville, 7pm. Could you let me know roughly how many people are coming?\n\nThanks,\nTheo")

A_TOMASZ = Agent("Email to Tomasz Book Club", [
    compose_send("2026-08-26 20:15:30",
                 composed_pre("email tomasz (tomasz.wierzbicki@quaymail.net) and tell him i'll host book club sept 17. ask how many are coming",
                              "tomasz.wierzbicki@quaymail.net", "Book club Sept 17 at our place", TW_BODY, "Good?", "yep", "Sending.", confirm_gap=20),
                 "tomasz.wierzbicki@quaymail.net", "Book club Sept 17 at our place", TW_BODY, "Sent to Tomasz."),
])

PX_BODY = ("Hi Prairie UX program committee,\n\nI'd like to propose a talk: \"Designing for Forecasts People Actually Trust\". It covers how we redesigned uncertainty displays "
           "for three fintech clients, what tested well, and the patterns we threw out.\n\n25-minute format. Speaker: Theo Marchetti, co-founder, Northfold Studio.\n\nThanks,\nTheo")

A_PRAIRIE = Agent("Prairie UX Talk Proposal", [
    Req("2026-09-15 21:10:30",
        [U("there's a cfp email from prairie ux conference. draft my submission as a reply: 'designing for forecasts people actually trust', 25 min, about the uncertainty display redesigns we did for the fintech clients"),
         P("Finding the CFP and drafting your submission.")],
        "Find the call-for-proposals email from the Prairie UX Conference and report the deadline and format. Then draft (do not send) a reply in that thread "
        "submitting a 25-minute talk titled \"Designing for Forecasts People Actually Trust\", with a short abstract about redesigning uncertainty displays for "
        "three fintech clients. Speaker: Theo Marchetti, co-founder, Northfold Studio. Report the CFP details and the exact draft.",
        [Search("Prairie UX Conference call for proposals", "from:cfp@prairieuxconf.org OR subject:(call for proposals) prairie ux after:2026/07/01",
                [Email("Adaeze Nwosu <cfp@prairieuxconf.org>", "Prairie UX 2026 - Call for Proposals closes Sep 18", "2026-08-28 09:00:00",
                       "Prairie UX returns to Winnipeg Nov 18-20. Submit a title + 150-word abstract by replying to this email by Sept 18. Formats: 25-min talk or 90-min workshop. Adaeze Nwosu, Program Chair",
                       thread="px", labels=("CATEGORY_UPDATES", "INBOX"))]),
         Draft("cfp@prairieuxconf.org", "Re: Prairie UX 2026 - Call for Proposals closes Sep 18", PX_BODY, thread="px")],
        resp="Prairie UX CFP (program chair Adaeze Nwosu, cfp@prairieuxconf.org, Aug 28): deadline **Sept 18**, reply with a title + 150-word abstract, 25-min talk "
             "or 90-min workshop, conference in Winnipeg Nov 18-20.\n\nDraft submission (not sent):\n\n{draft_block}\n\nWaiting for confirmation before sending.",
        post=[P("Deadline's Sept 18, you're fine. Conference is Nov 18-20 in Winnipeg."), DraftView("Here's the submission. Send?")]),
    send_req("2026-09-15 21:14:02", "send it", "Sending.", "Submitted. Three days to spare.", 0),
    Req("2026-10-02 08:55:47",
        [U("any word from prairie ux on my talk?"), P("Checking.")],
        "Check for a response from the Prairie UX Conference (cfp@prairieuxconf.org) about Theo's talk submission. Report the decision and any next steps or dates. Do not send anything.",
        [Search("Decision email from cfp@prairieuxconf.org about talk submission", "from:cfp@prairieuxconf.org after:2026/09/15",
                [Email("Adaeze Nwosu <cfp@prairieuxconf.org>", "Accepted: Designing for Forecasts People Actually Trust", "2026-10-01 13:30:00",
                       "Congratulations! Your talk is accepted. You're scheduled Thu Nov 19, 11:00, Main Hall. Please confirm by Oct 9 and send slides by Nov 12. Travel stipend up to $600. Adaeze", thread="px")])],
        resp="Accepted! Prairie UX (Adaeze Nwosu) emailed Oct 1:\n\n- **Slot:** Thu, Nov 19 at 11:00, Main Hall (Winnipeg)\n- **Confirm by:** Oct 9\n- **Slides due:** Nov 12\n"
             "- **Travel stipend:** up to $600\n\nNothing was sent.",
        post=[P("You're in! Thu Nov 19, 11am, Main Hall. Confirm by Oct 9, slides due Nov 12, $600 travel stipend.")]),
])

OV_BODY = ("Hi,\n\nI'd like to book a table for 2 on Saturday, November 14 at 7:30 PM. It's my partner's birthday. If the corner table by the window is available, we'd love it.\n\nThanks,\nTheo Marchetti")

A_OSTERIA = Agent("Jules Birthday Dinner", [
    compose_send("2026-10-05 12:18:30",
                 composed_pre("book osteria valdina for jules' birthday, nov 14 at 7:30 for 2. ask for the corner table if they can. reservations@osteriavaldina.ca",
                              "reservations@osteriavaldina.ca", "Reservation request - Nov 14, 7:30 PM, 2 people", OV_BODY, "Reservation request. Send?", "send", "Sending.", confirm_gap=25),
                 "reservations@osteriavaldina.ca", "Reservation request - Nov 14, 7:30 PM, 2 people", OV_BODY, "Sent to Osteria Valdina."),
    Req("2026-10-07 18:02:11",
        [U("did osteria valdina confirm"), P("Checking.")],
        "Check whether Osteria Valdina (reservations@osteriavaldina.ca) confirmed Theo's reservation request for Nov 14 at 7:30 PM. Report details. Do not send anything.",
        [Search("Reply from reservations@osteriavaldina.ca", "from:reservations@osteriavaldina.ca after:2026/10/05",
                [Email("Osteria Valdina <reservations@osteriavaldina.ca>", "Re: Reservation request - Nov 14, 7:30 PM, 2 people", "2026-10-06 16:40:00",
                       "Buonasera Theo, you're confirmed for 2 on Sat Nov 14 at 7:30 PM, corner window table. We'll bring a little something for the birthday. Grazie, Osteria Valdina")])],
        resp="Confirmed. Osteria Valdina replied Oct 6: table for 2 on **Saturday, Nov 14 at 7:30 PM**, **corner window table**, and they'll bring something for the birthday. Nothing was sent.",
        post=[P("Confirmed: Sat Nov 14, 7:30, corner window table. They're even doing a birthday surprise.")]),
])

A_DESK = Agent("Standing Desk Receipt Lookup", [
    Req("2026-08-03 11:02:18",
        [U("find my receipt for the standing desk from oakhurst, need it for expenses"), P("Looking for it.")],
        "Find Theo's receipt or order confirmation for a standing desk from Oakhurst Furniture. Report the order number, date, amount (with tax), and the message ID. Do not send anything.",
        [Search("Oakhurst Furniture standing desk receipt or order confirmation", "from:orders@oakhurstfurniture.ca (receipt OR order) standing desk",
                [Email("Oakhurst Furniture <orders@oakhurstfurniture.ca>", "Order confirmation #OK-58213", "2026-06-14 13:22:05",
                       "Thanks for your order! Halden Sit-Stand Desk, 60\" walnut. Subtotal $751.33, HST $97.67, Total $849.00. Delivered Jun 19.",
                       labels=("CATEGORY_UPDATES", "INBOX"), key="desk")])],
        resp="Found it. **Oakhurst Furniture, order #OK-58213** (Jun 14, 2026): Halden Sit-Stand Desk, 60\" walnut. Subtotal $751.33 + HST $97.67 = **$849.00**. "
             "Message ID: {message_id}. Nothing was sent.",
        post=[P("Got it: Oakhurst order #OK-58213, Jun 14, $849.00 with HST.")]),
])

LH_BODY = ("Hi Dr. Haddad,\n\nI hurt my left knee playing soccer last weekend. It's swollen and sore on stairs. Could I book an assessment sometime next week? Early mornings work best.\n\nThanks,\nTheo Marchetti")

A_PHYSIO = Agent("Physio Knee Appointment", [
    compose_send("2026-08-18 07:55:10",
                 composed_pre("can you book me a physio assessment at corktown physio? leena@corktownphysio.ca. knee's been bad since sunday's game. mornings are best",
                              "leena@corktownphysio.ca", "Knee assessment", LH_BODY, "Send this?", "send", "Sending.", confirm_gap=25),
                 "leena@corktownphysio.ca", "Knee assessment", LH_BODY, "Sent to Corktown Physio."),
    Req("2026-08-21 12:20:05",
        [U("did corktown physio get back to me"), P("Checking.")],
        "Check for a reply from Dr. Leena Haddad at Corktown Physio (leena@corktownphysio.ca) about Theo's knee assessment. Report the appointment details. Do not send anything.",
        [Search("Reply from leena@corktownphysio.ca", "from:leena@corktownphysio.ca after:2026/08/18",
                [Email("Leena Haddad <leena@corktownphysio.ca>", "Re: Knee assessment", "2026-08-20 17:02:00",
                       "Hi Theo, sorry to hear it. I have Tuesday Aug 25 at 8:00 AM. Wear shorts. 60-min assessment, $120, direct billing available. Leena")])],
        resp="Dr. Leena Haddad (Corktown Physio) replied Aug 20: assessment **Tuesday, Aug 25 at 8:00 AM**, 60 minutes, $120, direct billing available. Wear shorts. Nothing was sent.",
        post=[P("Tue Aug 25 at 8am with Dr. Haddad. 60 min, $120. Wear shorts.")]),
])

HV_BODY = ("Bonjour,\n\nDo you have a king room available for Friday, November 6 to Sunday, November 8 (2 nights)? It's for my partner and me. What's the rate?\n\nMerci,\nTheo Marchetti")
HV_BOOK_BODY = ("Bonjour,\n\nPerfect, please book the king room for Nov 6-8 at $289/night under Theo Marchetti. Late check-in around 9pm on Friday.\n\nMerci!\nTheo")

A_HOTEL = Agent("Montreal Weekend Hotel", [
    compose_send("2026-09-25 13:40:12",
                 composed_pre("email hotel verriere in montreal (reservations@hotelverriere.ca) and ask if they have a king room nov 6-8",
                              "reservations@hotelverriere.ca", "King room Nov 6-8?", HV_BODY, "Send?", "yes", "Sending.", confirm_gap=20),
                 "reservations@hotelverriere.ca", "King room Nov 6-8?", HV_BODY, "Sent to H\u00f4tel Verri\u00e8re.", thread="hv"),
    compose_send("2026-09-29 09:12:50",
                 composed_pre("the montreal hotel has a king for 289/night w breakfast. book it, we'll get in late friday around 9", "reservations@hotelverriere.ca", "Re: King room Nov 6-8?", HV_BOOK_BODY,
                              "Here's the confirmation. Send?", "yes", "Sending.", confirm_gap=20),
                 "reservations@hotelverriere.ca", "Re: King room Nov 6-8?", HV_BOOK_BODY, "Booked. Montréal, Nov 6-8.", thread="hv"),
])

EF_BODY = ("Hi Elaine,\n\nWhen do you expect the Q3 close package to be ready? We'd like numbers for the board meeting at the end of October.\n\nThanks,\nTheo")

A_ELAINE = Agent("Q3 Financials Elaine", [
    compose_send("2026-09-22 10:05:15",
                 composed_pre("email elaine at ledgerline (elaine@ledgerlinepartners.ca) and ask when the q3 close package will be ready, need it for the board meeting end of oct",
                              "elaine@ledgerlinepartners.ca", "Q3 close timing", EF_BODY, "Send?", "ya", "Sending.", confirm_gap=20),
                 "elaine@ledgerlinepartners.ca", "Q3 close timing", EF_BODY, "Sent to Elaine."),
    Req("2026-10-08 09:40:30",
        [U("did elaine reply about q3"), P("Checking.")],
        "Check for a reply from Elaine Fairbanks at Ledgerline Partners (elaine@ledgerlinepartners.ca) about the Q3 close package timing. Report the date and anything she needs. Do not send anything.",
        [Search("Reply from elaine@ledgerlinepartners.ca about Q3 close", "from:elaine@ledgerlinepartners.ca after:2026/09/22",
                [Email("Elaine Fairbanks <elaine@ledgerlinepartners.ca>", "Re: Q3 close timing", "2026-10-07 15:20:00",
                       "Hi Theo, Q3 package (P&L, balance sheet, cash runway) will be ready Fri Oct 16. I still need the September Amex-equivalent card export and two client invoices marked paid. Elaine")])],
        resp="Elaine Fairbanks replied Oct 7: the Q3 package (P&L, balance sheet, cash runway) will be ready **Friday, Oct 16**. She still needs the September corporate card export and two client invoices marked as paid. Nothing was sent.",
        post=[P("Q3 package by Fri Oct 16. She still needs the September card export and two client invoices marked paid.")]),
])

NH_BODY = ("Hi Noor,\n\nWe're getting married June 12, 2027 and would love a quote for 120 letterpress save-the-dates (A6, one colour, with envelopes). "
           "What's the turnaround?\n\nThanks!\nTheo")

A_STATIONERY = Agent("Save the Date Printing", [
    compose_send("2026-09-24 19:45:22",
                 composed_pre("email noor at inkwell & vine (noor@inkwellandvine.ca) for a quote on 120 letterpress save the dates",
                              "noor@inkwellandvine.ca", "Quote: 120 letterpress save-the-dates", NH_BODY, "Send to Noor?", "send", "Sending.", confirm_gap=20),
                 "noor@inkwellandvine.ca", "Quote: 120 letterpress save-the-dates", NH_BODY, "Sent to Inkwell & Vine.", thread="nh"),
    Req("2026-10-06 13:15:05",
        [U("did noor send the save the date quote"), P("Checking.")],
        "Check for a reply from Noor Hassan at Inkwell & Vine Stationery (noor@inkwellandvine.ca) with the save-the-date quote. Report price, turnaround, and next steps. Do not send anything.",
        [Search("Quote from noor@inkwellandvine.ca", "from:noor@inkwellandvine.ca after:2026/09/24",
                [Email("Noor Hassan <noor@inkwellandvine.ca>", "Re: Quote: 120 letterpress save-the-dates", "2026-10-05 11:00:00",
                       "Hi Theo! 120 A6 letterpress, one colour, with kraft envelopes: $780 + tax. Digital proof within 5 business days of deposit (50%), printing 2 weeks after proof approval. Noor", thread="nh")])],
        resp="Noor Hassan (Inkwell & Vine) replied Oct 5: **$780 + tax** for 120 A6 letterpress save-the-dates, one colour, kraft envelopes. 50% deposit, digital proof within 5 business days, printing 2 weeks after proof approval. Nothing was sent.",
        post=[P("$780 + tax for 120 with kraft envelopes. 50% deposit, proof in 5 business days, print 2 weeks after you approve.")]),
])

IW_BODY = ("Hi,\n\nI'd like to freeze my membership (Theo Marchetti) for September and October. I'm rehabbing a knee injury. Please confirm the freeze dates and any fee.\n\nThanks,\nTheo")

A_GYM = Agent("Gym Membership Freeze", [
    compose_send("2026-09-01 07:30:40",
                 composed_pre("email ironwood athletic and ask to freeze my membership for sept and oct, knee. members@ironwoodathletic.ca",
                              "members@ironwoodathletic.ca", "Membership freeze - Sept/Oct", IW_BODY, "Send to Ironwood?", "yes", "Sending.", confirm_gap=20),
                 "members@ironwoodathletic.ca", "Membership freeze - Sept/Oct", IW_BODY, "Sent. Ironwood will hold your spot."),
])

HP_BODY = ("Hi Harold,\n\nAfter last week's storm the fence between our yards is leaning pretty badly near the back. I got a quote from a fence company for $1,150 to reset the posts "
           "and replace two panels. Would you be up for splitting it?\n\nThanks,\nTheo (next door)")

A_FENCE = Agent("Neighbour Fence Repair", [
    compose_send("2026-09-30 18:40:20",
                 composed_pre("email harold next door (harold.pemberton@quaymail.net). the fence between us is leaning after the storm, ask if he'll split the $1150 repair",
                              "harold.pemberton@quaymail.net", "Our shared fence", HP_BODY, "Neighbourly enough?", "lol yes send", "Sending.", confirm_gap=30),
                 "harold.pemberton@quaymail.net", "Our shared fence", HP_BODY, "Sent to Harold."),
])

SB_BODY = ("Hi Sofia,\n\nSo excited for the cottage Aug 7-9! What should we bring, and can you send directions? Happy to handle a dinner.\n\nTheo")

A_SOFIA = Agent("Email to Sofia Cottage Weekend", [
    compose_send("2026-07-29 18:05:44",
                 composed_pre("email sofia (sofia.brandt@quaymail.net) and ask what we should bring to the cottage aug 7-9, and for directions. say we'll do a dinner",
                              "sofia.brandt@quaymail.net", "Cottage weekend Aug 7-9", SB_BODY, "Good?", "yes", "Sending.", confirm_gap=20),
                 "sofia.brandt@quaymail.net", "Cottage weekend Aug 7-9", SB_BODY, "Sent to Sofia."),
])

CORE_AGENTS: List[Agent] = [
    A_HARROW, A_PRIYA_N, A_KITCHEN, A_INBOX, A_COPPERLEAF, A_BRIEF, A_MORTGAGE, A_ENGAGE, A_MARCO, A_GABE,
    A_FERNWAY, A_HYDRO, A_DENTIST, A_MOM, A_TOMASZ, A_PRAIRIE, A_OSTERIA, A_DESK, A_PHYSIO, A_HOTEL,
    A_ELAINE, A_STATIONERY, A_GYM, A_FENCE, A_SOFIA,
]

# Hand-written chit-chat in the older window (the rest of the older filler is generated).
OLDER_CHATS: List[Tuple[str, List[Any]]] = [
    ("2026-07-20 20:14:31", [U("hey poke, theo here. jules says you can deal with my email so i dont have to"),
                             P("Hey Theo. That's the idea. Point me at the inbox chaos and I'll handle it."),
                             U("bold. we'll see"), P("Challenge accepted.")]),
]

# Chit-chat in the recent window (no delegation). (start time, entries)
RECENT_CHATS: List[Tuple[str, List[Any]]] = [
    ("2026-10-14 21:48:10", [U("is it weird to bring wine to a work offsite"), P("Not weird. Weird is bringing boxed wine. One good bottle for the cabin and you're a hero.")]),
    ("2026-10-16 22:31:40", [U("what's a good movie for a friday night, nothing sad"), P("Knives Out. Cozy sweaters, murder, zero tears.")]),
    ("2026-10-18 13:05:22", [U("how long do i roast a 4lb chicken"), P("About 80-90 min at 425°F, until the thigh hits 165°F. Rest it 15 min before carving."),
                             U("ty"), P("Crispy skin is in your future.")]),
    ("2026-10-17 15:10:00", [U("whats a good gift for a 6 yr old who likes dinosaurs"), P("A dig-your-own fossil kit. Messy, educational, loud. Peak 6."),
                             U("lol perfect"), P("The parents will love the plaster dust.")]),
    ("2026-10-18 19:04:30", [U("lol the library thing again"), P("They really want you to read those books.")]),
    ("2026-10-19 12:30:40", [U("how many weeks til june 12"), P("About 34 weeks from today."), U("oh god"), P("Plenty of time. Mostly.")]),
]

# =============================================================================================
# CASES (gold labels live only here and in cases.json)
# =============================================================================================

CASES: List[Dict[str, Any]] = [
    {
        "id": "c01_followup_named_counterpart",
        "category": "followup_counterpart_in_name",
        "rule": 1,
        "message": "did harrow hill ever confirm they got the deposit?",
        "expected": [{"task": "check for Harrow Hill's confirmation of the $4k second deposit", "gold": "Harrow Hill Venue Deposit"}],
        "rationale": "On 2026-10-15 (recent entries) 'Harrow Hill Venue Deposit' drafted and sent the second-deposit note to Celeste Moreau <celeste@harrowhillestate.ca> "
                     "in the Harrow Hill wedding thread (harrow-hill-venue-deposit.log). Asking whether the venue confirmed is a follow-up on that thread (rule 1). "
                     "The counterpart is named in the agent name. Shared-word hard negatives such as 'Security Deposit Refund' concern a different counterpart.",
    },
    {
        "id": "c02_new_task_known_counterpart",
        "category": "new_task_known_counterpart",
        "rule": 2,
        "message": "can you email priya and ask if she can run the client demo friday? im double booked",
        "expected": [{"task": "ask Priya Natarajan to run Friday's client demo", "gold": "Priya Roadmap Sync"}],
        "rationale": "Priya Natarajan <priya@northfoldstudio.ca> (Northfold engineering lead) is owned by 'Priya Roadmap Sync' (requests on 07-31, 08-14, 10-14, 10-16; "
                     "the 10-14 and 10-16 exchanges are in the recent 80 entries). Running a client demo is a new work thread for the same colleague, so rule 2 applies. "
                     "The other Priya (Priya Sandhu, photographer, owned by 'Engagement Shoot Booking') doesn't fit a work demo, and no agent owns 'demo' as a topic.",
    },
    {
        "id": "c03_counterpart_not_in_owner_name",
        "category": "new_task_owner_name_unrelated",
        "rule": 2,
        "message": "ask dmitri if his guys do bathrooms too? the upstairs one is next on the list",
        "expected": [{"task": "ask Dmitri Volkov whether Ironbark also does bathroom renovations", "gold": "Kitchen Reno Quote Follow-up"}],
        "rationale": "Dmitri Volkov <dmitri@ironbarkreno.ca> (Ironbark Renovations) is owned by 'Kitchen Reno Quote Follow-up', which handled every Dmitri thread "
                     "(quote 08-06/08-27, acceptance 09-09, cabinet-order check 10-16 in the recent entries, where the agent_message names Dmitri). The agent name "
                     "doesn't mention Dmitri. A bathroom question is a new task for the same contractor, so person and topic (renovation) point to the same agent.",
    },
    {
        "id": "c04_reply_to_email_found_by_unrelated_agent",
        "category": "reply_to_found_email",
        "rule": 1,
        "message": "ok reply to the tire place and tell them saturday 9am works",
        "expected": [{"task": "reply to Bramblewood Auto's winter tire email booking Sat Oct 24 9:00", "gold": "Inbox Catch-Up Scan"}],
        "rationale": "On 2026-10-17 (recent entries) 'Inbox Catch-Up Scan' found the Bramblewood Auto Service email 'Time to book your winter tire changeover' "
                     "(slots Sat Oct 24 9:00 / Tue Oct 27 16:30) and reported its thread ID. Replying to that email goes to the agent that found it (rule 1). "
                     "No other agent has ever touched Bramblewood or tires. Generic inbox distractors ('Inbox Summary', 'Unread Email Check', ...) never saw this email.",
    },
    {
        "id": "c05_confirm_pending_draft",
        "category": "confirm_pending_draft",
        "rule": 1,
        "message": "yep looks good, send it",
        "expected": [{"task": "send the pending Copperleaf reply draft", "gold": "Copperleaf Renewal Thread"}],
        "rationale": "The last entries of the recent window (2026-10-19 ~19:39) show 'Copperleaf Renewal Thread' creating a draft reply to Hana Ishikawa "
                     "<hana.ishikawa@copperleafdata.com> (two-year term at $18,400/yr), which Poke displayed and asked to confirm. 'Send it' refers to that draft (rule 1).",
    },
    {
        "id": "c06_modify_existing_trigger",
        "category": "modify_reminder",
        "rule": 1,
        "message": "can you push the sunday night rundown to 8:30 instead of 7? 7 is right when we sit down to eat",
        "expected": [{"task": "move the Sunday 19:00 week-ahead trigger to 20:30", "gold": "Sunday Week Ahead Brief"}],
        "rationale": "'Sunday Week Ahead Brief' created the weekly trigger (createTrigger succeeded, FREQ=WEEKLY;BYDAY=SU at 19:00) on 2026-08-05, and it fired on "
                     "2026-10-18 at 19:00 in the recent entries ('Week-ahead rundown'). Changing that trigger's time belongs to the agent that owns it (rule 1). "
                     "The other trigger owners (Hydro Bill Reminder, monthly; Mom Thanksgiving Visit, one-off) aren't Sunday rundowns.",
    },
    {
        "id": "c07_revive_dormant_counterpart",
        "category": "dormant_counterpart_summary_only",
        "rule": 2,
        "message": "can you ask wendell if we should lock the rate now or wait til after the nov 4 announcement",
        "expected": [{"task": "ask Wendell Achebe about locking the renewal rate before Nov 4", "gold": "Mortgage Renewal Paperwork"}],
        "rationale": "Wendell Achebe <wendell.achebe@brightmoorcu.ca> (Brightmoor Credit Union mortgage advisor) was handled only by 'Mortgage Renewal Paperwork' "
                     "(08-25 to 09-10, older entries only). The summary keeps the mortgage renewal with Wendell, the Oct 30 offer, and the rate decision before Nov 4. "
                     "He never appears in the recent 80. A new question to the same advisor goes to his owner (rule 2).",
    },
    {
        "id": "c08_same_first_name_other_person",
        "category": "same_first_name_other_person",
        "rule": 1,
        "message": "can you ask priya if she can send the engagement proofs early? jules keeps asking lol",
        "expected": [{"task": "email Priya Sandhu asking for the engagement proofs gallery early", "gold": "Engagement Shoot Booking"}],
        "rationale": "The engagement-shoot photographer is Priya Sandhu <priya@lumenandlinen.ca> (Lumen & Linen Photography), owned by 'Engagement Shoot Booking' "
                     "(inquiry 07-27, booking 08-12, and on 10-15 in the recent entries the agent reported 'proofing gallery by Fri Oct 23'). That's rules 1 and 2 together. "
                     "The hard negative is 'Priya Roadmap Sync', which owns a different Priya (Natarajan, priya@northfoldstudio.ca, engineering lead) and is more salient in the recent entries.",
    },
    {
        "id": "c09_new_counterpart_overlapping_name",
        "category": "new_counterpart_overlapping_name",
        "rule": 3,
        "message": "can you email marco ferrante at keyhaven music (marco@keyhavenmusic.ca) and ask if he has saturday morning slots for adult beginner piano?",
        "expected": [{"task": "ask Marco Ferrante (Keyhaven Music) about Saturday piano lessons", "gold": "NEW"}],
        "rationale": "Marco Ferrante <marco@keyhavenmusic.ca> has never appeared. No agent has dealt with Keyhaven Music or piano lessons. 'Email to Marco Soccer League' "
                     "owns a different Marco (Bellandi, marco@riverdalerecsoccer.ca), and 'Fernway Designer Search' owns Marcus Oyelaran. Rule 3 means a new agent.",
    },
    {
        "id": "c10_parallel_known_and_new",
        "category": "parallel_known_and_new",
        "rule": 3,
        "message": "tell gabe ill be like 20 min late to the kickoff wednesday, train thing. also can you email halcyon chimney (service@halcyonchimney.ca) and see if they can do a sweep before mid nov",
        "expected": [
            {"task": "tell Gabe Theo will be ~20 min late to Wednesday's offsite kickoff", "gold": "Email to Gabe Offsite Agenda"},
            {"task": "ask Halcyon Chimney about a chimney sweep before mid-November", "gold": "NEW"},
        ],
        "rationale": "Gabe Lindqvist <gabe@northfoldstudio.ca> and the Oct 21-22 Cedar Hollow offsite (10:00 Wed kickoff) are owned by 'Email to Gabe Offsite Agenda' "
                     "(agenda thread, final agenda sent 10-15 in the recent entries), so that part reuses it (rules 1 and 2). Halcyon Chimney has never appeared and no "
                     "agent covers chimneys. It's an independent task that can run in parallel, so it gets a new agent (rule 3).",
    },
    # ---- Dormant-owner pairs (held out). Same dormant owner, two phrasings: "name_match" shares
    # words with the owner's name; "inference" names only the person/org, so the only bridge is the
    # summary (which keeps the person but never the agent name). Every message asks for an action.
    {
        "id": "c11_dormant_name_match_noor", "category": "dormant_name_match", "pair": "noor", "split": "heldout", "rule": [1, 2],
        "message": "can we bump the save the date printing to 140? guest list grew",
        "expected": [{"task": "ask Noor (Inkwell & Vine) to raise the save-the-date order from 120 to 140", "gold": "Save the Date Printing"}],
        "rationale": "Noor Hassan's quote for 120 letterpress save-the-dates (summary, Pending) belongs to 'Save the Date Printing'; the message shares 'save the date printing'. Dormant: not in the recent 80. Topic sibling 'Wedding Invitation Calligrapher' is a different vendor.",
    },
    {
        "id": "c12_dormant_inference_noor", "category": "dormant_inference", "pair": "noor", "split": "heldout", "rule": [1, 2],
        "message": "ask noor if she can do 140 instead of 120, guest list grew",
        "expected": [{"task": "ask Noor (Inkwell & Vine) to raise the save-the-date order from 120 to 140", "gold": "Save the Date Printing"}],
        "rationale": "Same owner as c11. Only the summary links Noor to the 120-piece save-the-date quote; the agent name never appears in the summary.",
    },
    {
        "id": "c13_dormant_name_match_tidewater", "category": "dormant_name_match", "pair": "tidewater", "split": "heldout", "rule": [1, 2],
        "message": "email the dentist and ask if my cleaning can be at 5 instead",
        "expected": [{"task": "ask Tidewater Dental to move the cleaning to 17:00", "gold": "Dentist Cleaning Reschedule"}],
        "rationale": "Tidewater Dental cleaning reschedule thread (summary, Pending) is owned by 'Dentist Cleaning Reschedule'; message shares 'dentist' and 'cleaning'. Topic sibling 'Orthodontist Consult for Nephew' is a different patient and practice.",
    },
    {
        "id": "c14_dormant_inference_tidewater", "category": "dormant_inference", "pair": "tidewater", "split": "heldout", "rule": [1, 2],
        "message": "email tidewater and ask if i can get a 5pm slot instead",
        "expected": [{"task": "ask Tidewater Dental to move the cleaning to 17:00", "gold": "Dentist Cleaning Reschedule"}],
        "rationale": "Same owner as c13. Only the summary links Tidewater to the cleaning reschedule thread.",
    },
    {
        "id": "c15_dormant_name_match_ironwood", "category": "dormant_name_match", "pair": "ironwood", "split": "heldout", "rule": [1, 2],
        "message": "can you extend my gym membership freeze through november",
        "expected": [{"task": "ask Ironwood Athletic to extend the membership freeze through November", "gold": "Gym Membership Freeze"}],
        "rationale": "Ironwood Athletic freeze request (summary, Pending) is owned by 'Gym Membership Freeze'; message shares 'gym membership freeze'. Topic sibling 'Climbing Gym Day Pass' is a different club.",
    },
    {
        "id": "c16_dormant_inference_ironwood", "category": "dormant_inference", "pair": "ironwood", "split": "heldout", "rule": [1, 2],
        "message": "ask ironwood if they can extend my hold through november",
        "expected": [{"task": "ask Ironwood Athletic to extend the membership freeze through November", "gold": "Gym Membership Freeze"}],
        "rationale": "Same owner as c15. Only the summary links Ironwood to the freeze.",
    },
    {
        "id": "c17_dormant_name_match_harold", "category": "dormant_name_match", "pair": "harold", "split": "heldout", "rule": [1, 2],
        "message": "tell the neighbour im good to split the fence repair, 575 each",
        "expected": [{"task": "tell Harold Pemberton Theo agrees to split the $1,150 fence repair", "gold": "Neighbour Fence Repair"}],
        "rationale": "Harold's request to split the $1,150 fence repair (summary, Pending) is owned by 'Neighbour Fence Repair'; message shares 'neighbour fence repair'. Topic siblings 'Backyard Shed Permit' and 'Email to Rui Deck Repair Quote' are other counterparts.",
    },
    {
        "id": "c18_dormant_inference_harold", "category": "dormant_inference", "pair": "harold", "split": "heldout", "rule": [1, 2],
        "message": "tell harold im good to split it, 575 each",
        "expected": [{"task": "tell Harold Pemberton Theo agrees to split the $1,150 fence repair", "gold": "Neighbour Fence Repair"}],
        "rationale": "Same owner as c17. Only the summary links Harold to the fence thread.",
    },
    {
        "id": "c19_dormant_name_match_marcus", "category": "dormant_name_match", "pair": "marcus", "split": "heldout", "rule": [1, 2],
        "message": "can you push the designer search call to friday morning",
        "expected": [{"task": "ask Marcus Oyelaran (Fernway) to move the Thursday call to Friday morning", "gold": "Fernway Designer Search"}],
        "rationale": "Marcus's Thursday 14:00 call about the senior designer search (summary, Pending) is owned by 'Fernway Designer Search'; message shares 'designer search'. Topic sibling 'Email to Imani Contract Designer Rates' is a freelancer, not the search.",
    },
    {
        "id": "c20_dormant_inference_marcus", "category": "dormant_inference", "pair": "marcus", "split": "heldout", "rule": [1, 2],
        "message": "ask marcus if we can move our call to friday morning",
        "expected": [{"task": "ask Marcus Oyelaran (Fernway) to move the Thursday call to Friday morning", "gold": "Fernway Designer Search"}],
        "rationale": "Same owner as c19. Only the summary links Marcus to the designer search.",
    },
]

# =============================================================================================
# Generated (frozen) inputs
# =============================================================================================


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def distractor_agents(raw: List[Dict[str, Any]]) -> List[Agent]:
    """Turn generated distractor specs (fixtures/generated/distractors.json) into Agents."""
    agents = []
    for spec in raw:
        items: List[Any] = []
        for req in spec["requests"]:
            steps: List[Any] = []
            for st in req["steps"]:
                tool = st["tool"]
                if tool == "task_email_search":
                    emails = [Email(e["from"], e["subject"], e["date"], e["text"], thread=e.get("thread"),
                                    labels=tuple(e.get("labels") or ("CATEGORY_UPDATES", "INBOX")), key=e.get("key"),
                                    attachments=tuple(e.get("attachments") or ()))
                              for e in st.get("results", [])]
                    steps.append(Search(st["query"], st["gq"], emails))
                elif tool == "gmail_create_draft":
                    steps.append(Draft(st["to"], st["subject"], st["body"], thread=st.get("thread")))
                elif tool == "gmail_execute_draft":
                    steps.append(Send())
                elif tool == "gmail_forward_email":
                    steps.append(Forward(st["email_key"], st["to"], st["note"]))
                elif tool == "createTrigger":
                    steps.append(Trig(st["payload"], st.get("rrule"), st["start"]))
                elif tool == "gmail_search_people":
                    steps.append(People(st["query"], [(st["name"], st["email"])]))
                else:
                    raise ValueError(f"unsupported tool {tool} in {spec['name']}")
            post = [P(req["reply"])]
            if req.get("draft_view"):
                post = [DraftView(req["reply"])]
            items.append(Req(req["t"], [U(req["user"]), P(req["ack"])], req["instructions"], steps, resp=req.get("response"), post=post,
                             wait=req.get("wait")))
        agents.append(Agent(spec["name"], items, core=False, tier=spec["tier"]))
    return agents


# =============================================================================================
# Assembly
# =============================================================================================


@dataclass
class Built:
    agents: List[Agent]
    logs: Dict[str, List[Tuple[str, str, datetime]]]
    created: Dict[str, datetime]
    convo_core: List[Entry]           # every conversation entry produced by core agents
    convo_distractor: Dict[str, List[Entry]]
    conversation: List[Entry]         # final 380
    summary: Optional[Dict[str, Any]]


DISTRACTOR_START = "2026-07-20 08:00:00"

# ---------------------------------------------------------------------------------------------
# Real distractors: agents genuinely related to a core counterpart, modelled on the hybrid
# reuse/create behaviour the real IA shows (it names fresh agents after the task, e.g.
# "Email to Gabe Kickoff Delay", "Priya Demo Coverage Request" in our eval runs).
#   same_person: same counterpart, different topic. Rare. Only for counterparts whose case gold
#                is fixed by a specific thread/draft/trigger (rule 1) or that no case uses; never
#                for counterparts whose gold rests on affinity alone (rule 2), which would make
#                "which of their agents?" unanswerable.
#   same_topic:  same topic/work-type, different person or vendor. Common. Anchored to a person
#                or vendor (never a free-floating project) so person affinity still decides.
# Each replaces one noise distractor in the same tier, so roster sizes are unchanged.
# ---------------------------------------------------------------------------------------------
REAL_DISTRACTORS: List[Dict[str, Any]] = [
    # same person, different topic (8)
    {"name": "Mom Flight Rebooking", "kind": "same_person", "relates_to": "Mom Thanksgiving Visit", "tier": 50, "created": "2026-09-29 20:14:05"},
    {"name": "Harrow Hill Tasting Menu", "kind": "same_person", "relates_to": "Harrow Hill Venue Deposit", "tier": 200, "created": "2026-09-03 12:41:50"},
    {"name": "Lakeport Hydro Outage Credit", "kind": "same_person", "relates_to": "Hydro Bill Reminder", "tier": 400, "created": "2026-09-08 09:22:31"},
    {"name": "Copperleaf Invoice Copy", "kind": "same_person", "relates_to": "Copperleaf Renewal Thread", "tier": 400, "created": "2026-08-27 15:03:12"},
    {"name": "Email to Marco Spring Registration", "kind": "same_person", "relates_to": "Email to Marco Soccer League", "tier": 800, "created": "2026-10-02 18:55:40"},
    {"name": "Sofia Housewarming Gift", "kind": "same_person", "relates_to": "Email to Sofia Cottage Weekend", "tier": 800, "created": "2026-09-19 11:30:27"},
    {"name": "Tomasz November Book Pick", "kind": "same_person", "relates_to": "Email to Tomasz Book Club", "tier": 1600, "created": "2026-10-06 21:12:09"},
    {"name": "Oakhurst Chair Return", "kind": "same_person", "relates_to": "Standing Desk Receipt Lookup", "tier": 1600, "created": "2026-08-21 13:47:58"},
    # same topic / work-type, different person or vendor (36)
    {"name": "Backsplash Tile Order Stonehaven", "kind": "same_topic", "relates_to": "Kitchen Reno Quote Follow-up", "tier": 50, "created": "2026-10-05 10:18:44"},
    {"name": "Email to Bianca Wedding Florist Quote", "kind": "same_topic", "relates_to": "Harrow Hill Venue Deposit", "tier": 100, "created": "2026-09-11 19:40:02"},
    {"name": "Offsite Catering Cedar Hollow", "kind": "same_topic", "relates_to": "Email to Gabe Offsite Agenda", "tier": 100, "created": "2026-10-07 14:25:16"},
    {"name": "Massage Therapy Receipt Lookup", "kind": "same_topic", "relates_to": "Physio Knee Appointment", "tier": 100, "created": "2026-09-14 08:51:33"},
    {"name": "Email to Sam Birthday Party RSVP", "kind": "same_topic", "relates_to": "Jules Birthday Dinner", "tier": 200, "created": "2026-09-24 22:06:18"},
    {"name": "Email to Owen Client Demo Recording", "kind": "same_topic", "relates_to": "Priya Roadmap Sync", "tier": 200, "created": "2026-09-30 16:12:57"},
    {"name": "Property Tax Installment Reminder", "kind": "same_topic", "relates_to": "Mortgage Renewal Paperwork", "tier": 200, "created": "2026-08-14 09:05:00"},
    {"name": "Email to Felix Meetup Talk Slot", "kind": "same_topic", "relates_to": "Prairie UX Talk Proposal", "tier": 200, "created": "2026-09-09 13:33:21"},
    {"name": "Indoor Futsal Team Signup", "kind": "same_topic", "relates_to": "Email to Marco Soccer League", "tier": 200, "created": "2026-08-30 17:48:09"},
    {"name": "Office Chair Warranty Claim", "kind": "same_topic", "relates_to": "Standing Desk Receipt Lookup", "tier": 200, "created": "2026-09-01 10:27:45"},
    {"name": "Plumber Quote Basement Bathroom", "kind": "same_topic", "relates_to": "Kitchen Reno Quote Follow-up", "tier": 400, "created": "2026-09-21 12:09:38"},
    {"name": "Email to Theresa Officiant Booking", "kind": "same_topic", "relates_to": "Harrow Hill Venue Deposit", "tier": 400, "created": "2026-09-26 20:31:14"},
    {"name": "Email to Lena Sprint Retro Notes", "kind": "same_topic", "relates_to": "Priya Roadmap Sync", "tier": 400, "created": "2026-09-16 17:02:51"},
    {"name": "Orthodontist Consult for Nephew", "kind": "same_topic", "relates_to": "Dentist Cleaning Reschedule", "tier": 400, "created": "2026-08-25 18:44:20"},
    {"name": "Email to Imani Contract Designer Rates", "kind": "same_topic", "relates_to": "Fernway Designer Search", "tier": 400, "created": "2026-09-17 11:16:03"},
    {"name": "Email to Ines Choir Audition", "kind": "same_topic", "relates_to": "Email to Tomasz Book Club", "tier": 400, "created": "2026-09-05 19:59:26"},
    {"name": "Email to Aunt Gina Halifax Visit", "kind": "same_topic", "relates_to": "Mom Thanksgiving Visit", "tier": 400, "created": "2026-08-18 21:23:47"},
    {"name": "Friday Work Wrap-Up Digest", "kind": "same_topic", "relates_to": "Sunday Week Ahead Brief", "tier": 400, "created": "2026-09-04 16:30:00"},
    {"name": "Water Bill Autopay Setup", "kind": "same_topic", "relates_to": "Hydro Bill Reminder", "tier": 400, "created": "2026-08-11 08:39:12"},
    {"name": "Email to Nadia Mortgage Broker Referral", "kind": "same_topic", "relates_to": "Mortgage Renewal Paperwork", "tier": 800, "created": "2026-09-22 20:47:35"},
    {"name": "Engagement Ring Insurance Rider", "kind": "same_topic", "relates_to": "Engagement Shoot Booking", "tier": 800, "created": "2026-08-20 12:14:58"},
    {"name": "Climbing Gym Day Pass", "kind": "same_topic", "relates_to": "Gym Membership Freeze", "tier": 800, "created": "2026-10-03 09:58:17"},
    {"name": "Fireplace Insert Quote Ember & Co", "kind": "same_topic", "relates_to": None, "tier": 800, "created": "2026-09-27 15:36:42"},
    {"name": "Roadmap Template Research", "kind": "same_topic", "relates_to": "Priya Roadmap Sync", "tier": 800, "created": "2026-08-12 14:21:30"},
    {"name": "Quebec City Hotel Quote", "kind": "same_topic", "relates_to": "Montreal Weekend Hotel", "tier": 800, "created": "2026-09-13 22:10:05"},
    {"name": "Backyard Shed Permit", "kind": "same_topic", "relates_to": "Neighbour Fence Repair", "tier": 800, "created": "2026-08-29 10:43:56"},
    {"name": "Weekend Inbox Sweep", "kind": "same_topic", "relates_to": "Inbox Catch-Up Scan", "tier": 800, "created": "2026-09-06 10:02:14"},
    {"name": "Email to Dev Running Club Signup", "kind": "same_topic", "relates_to": "Email to Tomasz Book Club", "tier": 800, "created": "2026-08-23 07:55:48"},
    {"name": "Wedding Invitation Calligrapher", "kind": "same_topic", "relates_to": "Save the Date Printing", "tier": 1600, "created": "2026-09-15 18:26:11"},
    {"name": "Videographer Quote Comparison", "kind": "same_topic", "relates_to": "Engagement Shoot Booking", "tier": 1600, "created": "2026-09-25 21:38:24"},
    {"name": "Line of Credit Rate Change", "kind": "same_topic", "relates_to": "Mortgage Renewal Paperwork", "tier": 1600, "created": "2026-10-01 11:07:33"},
    {"name": "Email to Rui Deck Repair Quote", "kind": "same_topic", "relates_to": "Neighbour Fence Repair", "tier": 1600, "created": "2026-09-02 16:59:01"},
    {"name": "Northern Lights UX Summit Ticket", "kind": "same_topic", "relates_to": "Prairie UX Talk Proposal", "tier": 1600, "created": "2026-08-26 13:12:46"},
    {"name": "Lake Cabin Rental Muskoka", "kind": "same_topic", "relates_to": "Email to Sofia Cottage Weekend", "tier": 1600, "created": "2026-08-16 19:20:39"},
    {"name": "Supper Club Reservation Thornfield", "kind": "same_topic", "relates_to": "Jules Birthday Dinner", "tier": 1600, "created": "2026-10-09 17:45:52"},
    {"name": "Gas Bill Due Date Reminder", "kind": "same_topic", "relates_to": "Hydro Bill Reminder", "tier": 1600, "created": "2026-08-07 09:00:00"},
]

# Counterparts whose case gold rests on affinity alone (current + held-out cases): never give
# them a same_person sibling. NEW-gold case counterparts must have no agent at all.
AFFINITY_GOLD_OWNERS = {
    "Priya Roadmap Sync", "Kitchen Reno Quote Follow-up", "Mortgage Renewal Paperwork", "Email to Gabe Offsite Agenda",
    "Engagement Shoot Booking", "Fernway Designer Search", "Prairie UX Talk Proposal", "Save the Date Printing",
    "Dentist Cleaning Reschedule", "Gym Membership Freeze", "Neighbour Fence Repair", "Q3 Financials Elaine",
    "Montreal Weekend Hotel",
}
NEW_CASE_TERMS = ("keyhaven", "ferrante", "halcyon", "bramblewood", "chimney")


def real_distractor_violations(spec: Dict[str, Any]) -> List[str]:
    problems = []
    low = spec["name"].lower()
    if spec["kind"] == "same_person" and spec["relates_to"] in AFFINITY_GOLD_OWNERS:
        problems.append(f"same_person sibling for affinity-gold owner {spec['relates_to']!r}")
    if spec["relates_to"] is not None and spec["relates_to"] not in {a.name for a in CORE_AGENTS}:
        problems.append(f"relates_to {spec['relates_to']!r} is not a core agent")
    problems += [f"mentions NEW-case term {t!r}" for t in NEW_CASE_TERMS if t in low]
    if spec["tier"] not in TIER_COUNTS:
        problems.append(f"bad tier {spec['tier']}")
    if not (DISTRACTOR_START <= spec["created"] <= DISTRACTOR_END):
        problems.append("created outside the distractor window")
    return problems


def name_only_distractors(raw: List[Dict[str, Any]]) -> Tuple[List[Agent], Dict[str, datetime]]:
    """Distractors are roster names only: the IA never reads execution logs, so none are generated.

    Tier (the smallest roster a distractor joins) and creation time are deterministic hashes of the name.
    """
    # Original names fill tiers 50-400; "extended" names (added later) fill 800/1600 only, so the
    # smaller rosters are unchanged by the extension.
    names: List[str] = []
    tiers: List[int] = []
    for group, sizes in (("base", (50, 100, 200, 400)), ("extended", (800, 1600))):
        group_names = sorted(spec["name"] for spec in raw if (spec.get("tier_group") or "base") == group)
        group_names.sort(key=lambda n: _h("tier", n))
        group_tiers = [size for size in sizes for _ in range(TIER_COUNTS[size])]
        assert len(group_names) == len(group_tiers), f"{group}: {len(group_names)} names for {len(group_tiers)} slots"
        names.extend(group_names)
        tiers.extend(group_tiers)
    # Swap noise names for real distractors tier by tier (sizes unchanged). Seeds (hand-picked
    # generic names like "Inbox Summary") are never dropped; the rest are dropped in hash order.
    seeds = {spec["name"] for spec in raw if spec.get("seed")}
    drop: set = set()
    for tier in TIER_COUNTS:
        need = sum(1 for r in REAL_DISTRACTORS if r["tier"] == tier)
        pool = sorted((n for n, t in zip(names, tiers) if t == tier and n not in seeds), key=lambda n: _h("swap", n))
        drop.update(pool[:need])
    kept = [(n, t) for n, t in zip(names, tiers) if n not in drop]
    start, end = dt(DISTRACTOR_START), dt(DISTRACTOR_END)
    span = int((end - start).total_seconds())
    agents: List[Agent] = []
    created: Dict[str, datetime] = {}
    for name, tier in kept:
        agents.append(Agent(name, [], core=False, tier=tier))
        created[name] = start + timedelta(seconds=_h("created", name) % span)
    for spec in REAL_DISTRACTORS:
        agents.append(Agent(spec["name"], [], core=False, tier=spec["tier"]))
        created[spec["name"]] = dt(spec["created"])
    return agents, created


def build(include_generated: bool = True) -> Built:
    raw_names = load_json(GENERATED / "distractor_names.json", {"agents": []})["agents"] if include_generated else []
    distractors, distractor_created = name_only_distractors(raw_names)
    agents = CORE_AGENTS + distractors
    names = [a.name for a in agents]
    assert len(set(names)) == len(names), "duplicate agent names"
    world = World()
    assign_trigger_ids(world, agents)
    logs: Dict[str, List[Tuple[str, str, datetime]]] = {}
    created: Dict[str, datetime] = {}
    convo_core: List[Entry] = []
    convo_distractor: Dict[str, List[Entry]] = {}
    # render in chronological order of first activity so thread/email registries see first uses first
    created.update(distractor_created)
    order = sorted(CORE_AGENTS, key=lambda a: _first_time(a))
    for agent in order:
        lines, convo = render_agent(world, agent)
        logs[agent.name] = lines
        created[agent.name] = next(w for tag, _, w in lines if tag == "agent_request")
        if agent.core:
            convo_core.extend(convo)
        else:
            convo_distractor[agent.name] = convo
    recent_cut = dt(RECENT_START)
    for start, entries in OLDER_CHATS + RECENT_CHATS:
        convo_core.extend(_chat_entries(start, entries, f"chat:{start}"))

    core_recent = [e for e in convo_core if e.when >= recent_cut]
    core_older = [e for e in convo_core if e.when < recent_cut]
    filler = load_json(GENERATED / "older_filler.json", {"chats": [], "distractor_episodes": []}) if include_generated else {"chats": [], "distractor_episodes": []}
    older = list(core_older)
    for name in filler.get("distractor_episodes", []):
        older.extend(convo_distractor[name])
    chats = filler.get("chats", [])
    need = LAST_INDEX + 1 - len(older)
    chosen: List[Entry] = []
    for chat in chats:
        n = len(chat["entries"])
        if n <= need - len(chosen):
            chosen.extend(_chat_entries(chat["t"], [U(x["text"]) if x["tag"] == "user_message" else P(x["text"]) for x in chat["entries"]], f"chat:{chat['t']}"))
        if len(chosen) == need:
            break
    older.extend(chosen)
    conversation = sorted(older, key=lambda e: e.when) + sorted(core_recent, key=lambda e: e.when)
    summary = load_json(GENERATED / "summary.json", None) if include_generated else None
    return Built(agents, logs, created, convo_core, convo_distractor, conversation, summary)


def _first_time(agent: Agent) -> datetime:
    return min(dt(item.t) for item in agent.items)


def _chat_entries(start: str, entries: List[Any], episode: str) -> List[Entry]:
    out = []
    now = dt(start)
    for k, e in enumerate(entries):
        if k:
            default = jitter(f"{episode}:{k}", 20, 60) if isinstance(e, U) else jitter(f"{episode}:{k}", 2, 5)
            now += timedelta(seconds=e.gap if e.gap is not None else default)
        out.append(Entry(_TAG[type(e)], e.text, now, episode))
    return out


def conversation_lines(built: Built) -> List[str]:
    return [format_line(e.tag, e.payload, ts(e.when)) for e in built.conversation]


def rosters(built: Built) -> Dict[int, List[str]]:
    out = {}
    for size in ROSTER_SIZES:
        members = [a for a in built.agents if a.core or a.tier <= size]
        members.sort(key=lambda a: (built.created[a.name], a.name))
        out[size] = [a.name for a in members]
    return out


def write_all(built: Built) -> None:
    if built.summary is None:
        raise SystemExit("fixtures/generated/summary.json missing: run `python -m evals.routing.generate summary` first")
    conv_lines = conversation_lines(built)
    if len(conv_lines) != N_ENTRIES:
        raise SystemExit(f"conversation has {len(conv_lines)} entries, expected {N_ENTRIES}")
    digest = older_digest(built)
    if built.summary.get("entries_sha256") != digest:
        raise SystemExit("summary.json is stale (entries 0-299 changed): rerun `python -m evals.routing.generate summary`")
    if STATE.exists():
        shutil.rmtree(STATE)
    (STATE / "conversation").mkdir(parents=True)
    (STATE / "execution_agents").mkdir(parents=True)
    (STATE / "timezone.txt").write_text("America/Toronto", encoding="utf-8")
    (STATE / "conversation" / "poke_conversation.log").write_text("".join(conv_lines), encoding="utf-8")
    info = json.dumps({"last_index": LAST_INDEX, "updated_at": built.summary["updated_at"]})
    wm = [format_line("summary_info", info), format_line("conversation_summary", built.summary["summary"])] + conv_lines[LAST_INDEX + 1:]
    (STATE / "conversation" / "poke_working_memory.log").write_text("".join(wm), encoding="utf-8")
    # No execution agent logs are written: routing depends only on what the IA reads (roster names +
    # working memory). Core logs are still rendered in memory because the conversation is derived from them.
    ROSTERS.mkdir(parents=True, exist_ok=True)
    for size, names in rosters(built).items():
        (ROSTERS / f"roster_{size}.json").write_text(json.dumps(names, indent=2), encoding="utf-8")
    CASES_PATH.write_text(json.dumps({"version": 1, "cases": CASES}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def older_entries(built: Built) -> List[Tuple[str, str, str]]:
    return [(e.tag, ts(e.when), e.payload) for e in built.conversation[: LAST_INDEX + 1]]


def older_digest(built: Built) -> str:
    return hashlib.sha256(json.dumps(older_entries(built), ensure_ascii=False).encode("utf-8")).hexdigest()


# =============================================================================================
# Distractor checks (shared with generate.py)
# =============================================================================================

_ANY_RE = [re.compile(r"(?<![a-z0-9])" + re.escape(term.lower()) + r"(?![a-z0-9])") for term in DISTRACTOR_BANNED_ANYWHERE]
_NAME_RE = [re.compile(r"(?<![a-z0-9])" + pat + r"(?![a-z0-9])") for pat in DISTRACTOR_BANNED_NAME_TOPICS]
_BRAND_RE = [re.compile(r"(?<![a-z0-9])" + re.escape(b) + r"(?![a-z0-9])") for b in REAL_BRAND_BLOCKLIST]


def strip_accents(text: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def distractor_violations(name: str, text: str) -> List[str]:
    """Return reasons a distractor (name + all of its log/conversation text) is not allowed."""
    problems = []
    low_name = strip_accents(name.lower())
    low = strip_accents((name + "\n" + text).lower())
    for term, rx in zip(DISTRACTOR_BANNED_ANYWHERE, _ANY_RE):
        if rx.search(low):
            problems.append(f"mentions core term {term!r}")
    for sub in DISTRACTOR_BANNED_SUBSTRINGS:
        if sub in low:
            problems.append(f"contains banned substring {sub!r}")
    for pat, rx in zip(DISTRACTOR_BANNED_NAME_TOPICS, _NAME_RE):
        if rx.search(low_name):
            problems.append(f"name uses reserved topic /{pat}/")
    low_wo_urls = re.sub(r"https://mail\.google\.com\S*", "", low)
    for brand, rx in zip(REAL_BRAND_BLOCKLIST, _BRAND_RE):
        if rx.search(low_wo_urls):
            problems.append(f"real brand {brand!r}")
    return problems


# =============================================================================================
# Self-check
# =============================================================================================


def check(built: Built) -> List[str]:
    errors: List[str] = []
    core_names = [a.name for a in CORE_AGENTS]

    # 1. every line in every state file parses
    files = sorted(STATE.rglob("*.log"))
    for path in files:
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if parse_line(line) is None:
                errors.append(f"{path.relative_to(FIXTURES)}:{n} does not parse")
    tz_text = (STATE / "timezone.txt").read_text(encoding="utf-8")
    if tz_text.strip() != "America/Toronto":
        errors.append("timezone.txt must be America/Toronto")
    if (STATE / "execution_agents" / "roster.json").exists():
        errors.append("state/ must not contain roster.json")

    # 2. conversation: 380 entries, chronological
    conv = (STATE / "conversation" / "poke_conversation.log").read_text(encoding="utf-8").splitlines(keepends=True)
    if len(conv) != N_ENTRIES:
        errors.append(f"conversation has {len(conv)} entries")
    parsed = [parse_line(line) for line in conv]
    stamps = [p[1] for p in parsed if p]
    if stamps != sorted(stamps):
        errors.append("conversation timestamps are not chronological")
    if any(p and p[0] not in {"user_message", "poke_reply", "agent_message", "wait"} for p in parsed):
        errors.append("conversation has an unexpected tag")
    if stamps and not (stamps[LAST_INDEX] < RECENT_START <= stamps[LAST_INDEX + 1]):
        errors.append("entry 299/300 boundary does not match RECENT_START")

    # 3. working memory tail == conversation 300-379 byte for byte; last_index 299
    wm = (STATE / "conversation" / "poke_working_memory.log").read_text(encoding="utf-8").splitlines(keepends=True)
    head = [parse_line(line) for line in wm[:2]]
    if not head[0] or head[0][0] != "summary_info" or head[0][1] != "":
        errors.append("working memory line 1 must be summary_info without timestamp")
    else:
        info = json.loads(head[0][2])
        if info.get("last_index") != LAST_INDEX:
            errors.append(f"last_index is {info.get('last_index')}")
    if not head[1] or head[1][0] != "conversation_summary" or head[1][1] != "" or not head[1][2].strip():
        errors.append("working memory line 2 must be a non-empty conversation_summary without timestamp")
    if wm[2:] != conv[LAST_INDEX + 1:]:
        errors.append("working-memory tail != conversation entries 300-379")
    if built.summary and built.summary.get("entries_sha256") != older_digest(built):
        errors.append("summary was generated from different entries 0-299 (stale)")

    # 4. agents: unique slugs; no log files in state/; in-memory core logs well-formed
    slugs = [agent_log_filename(a.name) for a in built.agents]
    if len(set(slugs)) != len(slugs):
        errors.append("slug collision between agents")
    if list((STATE / "execution_agents").glob("*.log")):
        errors.append("state/execution_agents must not contain logs (routing fixtures are name-only)")
    for agent in CORE_AGENTS:
        tags = [t for t, _, _ in built.logs[agent.name]]
        if not tags or tags[0] != "agent_request" or tags[-1] != "agent_response":
            errors.append(f"{agent.name}: log must start with agent_request and end with agent_response")
        n_req = tags.count("agent_request")
        if not 1 <= n_req <= 6:
            errors.append(f"{agent.name}: {n_req} requests (expected 1-6)")
        whens = [w for _, _, w in built.logs[agent.name]]
        if whens != sorted(whens):
            errors.append(f"{agent.name}: log timestamps not chronological")

    # 5. rosters nested, sizes exact, roster_25 == core, every name has a log
    loaded = {}
    for size in ROSTER_SIZES:
        path = ROSTERS / f"roster_{size}.json"
        names = json.loads(path.read_text(encoding="utf-8"))
        loaded[size] = names
        if len(names) != size or len(set(names)) != size:
            errors.append(f"roster_{size} has {len(names)} names ({len(set(names))} unique)")
        expected_text = json.dumps(names, indent=2)
        if path.read_text(encoding="utf-8") != expected_text:
            errors.append(f"roster_{size}.json is not written like the server (indent=2)")
        order = [built.created[n] for n in names]
        if order != sorted(order):
            errors.append(f"roster_{size} not in creation order")
    if set(loaded[25]) != set(core_names):
        errors.append("roster_25 != core agents")
    for small, big in zip(ROSTER_SIZES, ROSTER_SIZES[1:]):
        if not set(loaded[small]) <= set(loaded[big]):
            errors.append(f"roster_{small} not a subset of roster_{big}")
    positions = [loaded[400].index(n) for n in core_names]
    if max(positions) < 300 or min(positions) > 50:
        errors.append(f"core agents not spread through roster_400 (positions {sorted(positions)})")

    # 6. cases
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))["cases"]
    if len(cases) != 20:
        errors.append(f"{len(cases)} cases")
    for case in cases:
        for exp in case["expected"]:
            if exp["gold"] != "NEW" and exp["gold"] not in loaded[25]:
                errors.append(f"{case['id']}: gold {exp['gold']!r} not in roster_25")

    # 7. distractors never mention core counterparts
    real = {r["name"]: r for r in REAL_DISTRACTORS}
    if len(real) != len(REAL_DISTRACTORS):
        errors.append("duplicate real distractor names")
    for spec in REAL_DISTRACTORS:
        for problem in real_distractor_violations(spec):
            errors.append(f"real distractor {spec['name']!r}: {problem}")
    for size in ROSTER_SIZES:  # each real distractor is present from its tier upward
        for spec in REAL_DISTRACTORS:
            if (spec["name"] in loaded[size]) != (spec["tier"] <= size):
                errors.append(f"real distractor {spec['name']!r} wrong membership in roster_{size}")
    for agent in built.agents:
        if agent.core or agent.name in real:
            continue
        problems = distractor_violations(agent.name, agent.name)
        if problems:
            errors.append(f"distractor {agent.name!r}: {problems[:3]}")

    # 8. recent window references only roster_25 agents; dormant counterpart absent from recent
    recent_text = "".join(conv[LAST_INDEX + 1:])
    for line in conv[LAST_INDEX + 1:]:
        p = parse_line(line)
        if p and p[0] == "agent_message":
            for chunk in p[2].split("\n"):
                m = re.match(r"\[(SUCCESS|FAILED)\] ([^:]+):", chunk)
                if m and m.group(2) not in loaded[25]:
                    errors.append(f"recent agent_message from non-core agent {m.group(2)!r}")
    for term in ("wendell", "brightmoor", "mortgage", "noor", "inkwell", "tidewater", "ironwood", "harold", "marcus", "fernway"):
        if term in recent_text.lower():
            errors.append(f"dormant counterpart term {term!r} appears in the recent 80 entries")
    last = parse_line(conv[-1])
    if not last or last[0] != "poke_reply" or "send" not in last[2].lower():
        errors.append("conversation must end with Poke asking to confirm a draft")
    if built.summary:
        low = built.summary["summary"].lower()
        for term in ("wendell", "mortgage"):
            if term not in low:
                errors.append(f"summary lost dormant counterpart term {term!r}")
    return errors


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="write fixtures, then run the self-check")
    parser.add_argument("--check-only", action="store_true", help="only run the self-check against existing files")
    parser.add_argument("--stats", action="store_true", help="print entry counts without writing")
    args = parser.parse_args(argv)
    built = build()
    if args.stats:
        recent = [e for e in built.convo_core if e.when >= dt(RECENT_START)]
        older = [e for e in built.convo_core if e.when < dt(RECENT_START)]
        print(f"core older entries: {len(older)}  recent entries: {len(recent)}  conversation total: {len(built.conversation)}")
        print(f"agents: {len(built.agents)}")
        return 0
    if not args.check_only:
        write_all(built)
        print(f"wrote {len(built.agents)} roster agents (no logs), {len(built.conversation)} conversation entries, rosters {list(ROSTER_SIZES)}, {len(CASES)} cases")
    if args.check or args.check_only:
        errors = check(built)
        if errors:
            print(f"SELF-CHECK FAILED ({len(errors)} problems):")
            for err in errors[:60]:
                print("  -", err)
            return 1
        print("SELF-CHECK PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
