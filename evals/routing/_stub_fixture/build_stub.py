"""Build a tiny stub fixture (6 agents, rosters 3/6, 3 cases) for harness tests.

    python -m evals.routing._stub_fixture.build_stub [out_dir]   # default: this directory
"""

from __future__ import annotations

import atexit
import json
import shutil
import sys
from pathlib import Path

from evals.routing.run import _init_data_dir

atexit.register(shutil.rmtree, _init_data_dir(), True)  # temp data dir, set before logfmt imports server
from evals.routing.logfmt import agent_log_filename, format_line  # noqa: E402

HERE = Path(__file__).resolve().parent

AGENTS = {
    "Email to Priya Shah": [
        ("agent_request", "2026-10-02 10:01:12", "Email Priya Shah (priya.shah@northwind-events.com) at Northwind Events asking for the revised venue contract for the Dec 5 offsite."),
        ("agent_action", "2026-10-02 10:01:15", 'Calling gmail_create_draft with: {"recipient_email": "priya.shah@northwind-events.com", "subject": "Revised venue contract", "body": "Hi Priya,\\n\\nCould you send the revised contract?", "is_html": false}'),
        ("tool_response", "2026-10-02 10:01:16", 'gmail_create_draft: {"successful": true, "data": {"id": "r111", "message": {"threadId": "1a2b3c"}}}'),
        ("agent_response", "2026-10-02 10:01:18", "Draft created to priya.shah@northwind-events.com asking for the revised venue contract."),
    ],
    "Nightly Digest Reminder": [
        ("agent_request", "2026-10-03 21:00:02", "Set up a reminder every night at 9pm to send Ali a digest of unread important emails."),
        ("agent_action", "2026-10-03 21:00:05", "createTrigger succeeded | trigger_id=7"),
        ("agent_action", "2026-10-03 21:00:05", 'Calling createTrigger with: {"payload": "Send nightly digest", "recurrence_rule": "FREQ=DAILY;BYHOUR=21"}'),
        ("tool_response", "2026-10-03 21:00:05", 'createTrigger: {"trigger_id": 7, "status": "active"}'),
        ("agent_response", "2026-10-03 21:00:07", "Nightly digest reminder created for 9:00 PM every day (trigger 7)."),
    ],
    "Japan Trip Flights": [
        ("agent_request", "2026-10-05 12:30:00", "Find the flight confirmation for the Japan trip."),
        ("agent_action", "2026-10-05 12:30:03", 'Calling task_email_search with: {"query": "flight confirmation Tokyo"}'),
        ("tool_response", "2026-10-05 12:30:06", 'task_email_search: [{"id": "m1", "thread_id": "t9", "subject": "Your ANA booking", "sender": "noreply@ana.co.jp"}]'),
        ("agent_response", "2026-10-05 12:30:08", "Found the ANA booking confirmation: YYZ to HND on Nov 12."),
    ],
    "Landlord Lease Renewal": [
        ("agent_request", "2026-10-08 09:15:40", "Email Marco Rossi (marco@rossiproperties.ca), the landlord, to say Ali wants to renew the lease for another year."),
        ("agent_action", "2026-10-08 09:15:44", 'Calling gmail_create_draft with: {"recipient_email": "marco@rossiproperties.ca", "subject": "Lease renewal", "body": "Hi Marco,\\n\\nI\'d like to renew.", "is_html": false}'),
        ("tool_response", "2026-10-08 09:15:45", 'gmail_create_draft: {"successful": true, "data": {"id": "r222", "message": {"threadId": "4d5e6f"}}}'),
        ("agent_response", "2026-10-08 09:15:47", "Draft created to marco@rossiproperties.ca about renewing the lease. It has not been sent."),
    ],
    "Dentist Appointment": [
        ("agent_request", "2026-10-09 14:00:00", "Find the email from Bloor Dental about Ali's cleaning appointment."),
        ("agent_response", "2026-10-09 14:00:09", "Bloor Dental confirmed a cleaning on Oct 28 at 3pm."),
    ],
    "AliExpress Order Tracking": [
        ("agent_request", "2026-10-11 18:02:00", "Track the AliExpress order for the phone case."),
        ("agent_response", "2026-10-11 18:02:10", "The AliExpress order shipped Oct 9; ETA Oct 25."),
    ],
}

ROSTER_6 = [
    "Email to Priya Shah",
    "Nightly Digest Reminder",
    "Japan Trip Flights",
    "Landlord Lease Renewal",
    "Dentist Appointment",
    "AliExpress Order Tracking",
]
ROSTER_3 = ["Email to Priya Shah", "Nightly Digest Reminder", "Landlord Lease Renewal"]

CONVERSATION = [
    ("user_message", "2026-10-02 10:00:50", "can you email priya at northwind and ask for the revised venue contract"),
    ("poke_reply", "2026-10-02 10:01:00", "On it, drafting a note to Priya now."),
    ("agent_message", "2026-10-02 10:01:20", "[SUCCESS] Email to Priya Shah: Draft created to priya.shah@northwind-events.com asking for the revised venue contract."),
    ("poke_reply", "2026-10-02 10:01:25", "To: priya.shah@northwind-events.com\nSubject: Revised venue contract\n\nHi Priya,\n\nCould you send the revised contract?"),
    ("user_message", "2026-10-03 20:59:40", "remind me every night at 9 with a digest of my important emails"),
    ("poke_reply", "2026-10-03 20:59:50", "Setting that up."),
    ("agent_message", "2026-10-03 21:00:08", "[SUCCESS] Nightly Digest Reminder: Nightly digest reminder created for 9:00 PM every day (trigger 7)."),
    ("poke_reply", "2026-10-03 21:00:12", "Done, you'll get a digest every night at 9pm."),
    ("user_message", "2026-10-08 09:15:20", "email marco and tell him i want to renew the lease"),
    ("poke_reply", "2026-10-08 09:15:30", "Drafting that for Marco."),
    ("wait", "2026-10-08 09:15:31", "Waiting for the lease renewal draft."),
    ("agent_message", "2026-10-08 09:15:48", "[SUCCESS] Landlord Lease Renewal: Draft created to marco@rossiproperties.ca about renewing the lease. It has not been sent."),
    ("poke_reply", "2026-10-08 09:15:52", "To: marco@rossiproperties.ca\nSubject: Lease renewal\n\nHi Marco,\n\nI'd like to renew."),
    ("poke_reply", "2026-10-08 09:15:53", "Want me to send it or change anything?"),
]
SUMMARIZED = 4  # entries 0..3 are folded into the summary
SUMMARY = (
    "Summary generated: Ali asked to email Priya Shah (priya.shah@northwind-events.com, Northwind Events) "
    "for the revised venue contract for the Dec 5 offsite; agent 'Email to Priya Shah' drafted it."
)

CASES = {
    "version": 1,
    "cases": [
        {
            "id": "s01_known_counterpart",
            "category": "new_task_known_counterpart",
            "rule": 2,
            "message": "can you email priya and ask if she's free for a call thursday?",
            "expected": [{"task": "ask Priya about Thursday call", "gold": "Email to Priya Shah"}],
            "rationale": "Priya Shah is owned by 'Email to Priya Shah' (summary + log).",
        },
        {
            "id": "s02_trigger_change",
            "category": "change_reminder",
            "rule": 1,
            "message": "push my nightly digest to 10pm",
            "expected": [{"task": "move digest trigger to 10pm", "gold": "Nightly Digest Reminder"}],
            "rationale": "nightly-digest-reminder.log has createTrigger succeeded | trigger_id=7.",
        },
        {
            "id": "s03_two_parallel",
            "category": "two_parallel_tasks",
            "rule": [1, 3],
            "message": "yep send the lease one. also email sam chen at hackclub and ask when the hackathon signup closes",
            "expected": [
                {"task": "send the lease renewal draft", "gold": "Landlord Lease Renewal"},
                {"task": "ask Sam Chen about hackathon signup", "gold": "NEW"},
            ],
            "rationale": "Lease draft pending in recent entries; Sam Chen has no owner.",
        },
    ],
}


def build(out: Path) -> None:
    for sub in ("state", "rosters"):
        shutil.rmtree(out / sub, ignore_errors=True)
    state = out / "state"
    (state / "conversation").mkdir(parents=True)
    (state / "execution_agents").mkdir(parents=True)
    (out / "rosters").mkdir(parents=True)
    (state / "timezone.txt").write_text("America/Toronto", encoding="utf-8")

    conv_lines = [format_line(t, p, ts) for t, ts, p in CONVERSATION]
    (state / "conversation" / "poke_conversation.log").write_text("".join(conv_lines), encoding="utf-8")
    wm = [
        format_line("summary_info", json.dumps({"last_index": SUMMARIZED - 1, "updated_at": "2026-10-08T13:20:00+00:00"})),
        format_line("conversation_summary", SUMMARY),
        *conv_lines[SUMMARIZED:],
    ]
    (state / "conversation" / "poke_working_memory.log").write_text("".join(wm), encoding="utf-8")

    for name, entries in AGENTS.items():
        lines = [format_line(t, p, ts) for t, ts, p in entries]
        (state / "execution_agents" / agent_log_filename(name)).write_text("".join(lines), encoding="utf-8")

    for size, roster in ((3, ROSTER_3), (6, ROSTER_6)):
        (out / "rosters" / f"roster_{size}.json").write_text(json.dumps(roster, indent=2), encoding="utf-8")
    (out / "cases.json").write_text(json.dumps(CASES, indent=2), encoding="utf-8")


if __name__ == "__main__":
    target = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE
    build(target)
    print(f"stub fixture written to {target}")
