"""Refresh an execution agent's card (summary + artifacts) after it finishes a task."""

from __future__ import annotations

import asyncio
import json
from typing import Dict, List

from pydantic import BaseModel, ConfigDict, ValidationError

from ...config import get_settings
from ...logging_config import logger
from ...openrouter_client import request_chat_completion
from .log_store import get_execution_agent_logs
from .roster import ARTIFACTS_DESCRIPTION, AgentCard, get_agent_roster

_MAX_ENTRY_CHARS = 1000
_MAX_TASK_ENTRIES = 40

_SYSTEM_PROMPT = f"""You maintain the card that identifies an execution agent, so an assistant can find and reuse the right agent later. You get the agent's current card and the log of the task it just finished. Return the updated card.

Rules:
- summary: at most 3 sentences and 500 characters. Keep what the agent is for, then what it has done and anything still pending. Don't restate the agent's name.
- artifacts: {ARTIFACTS_DESCRIPTION} Prefer exact identifiers over general descriptions.
- Only include things the agent acted on or was asked about. If it searched or read many emails, include only the ones the task was about, not everything it saw.
- Keep existing artifacts unless the task superseded them (e.g. a date that changed). Merge duplicates. List the most important first."""


class _CardUpdate(BaseModel):
    """Shape of the updater's output, enforced by OpenRouter structured outputs."""

    model_config = ConfigDict(extra="forbid")

    summary: str
    artifacts: List[str]


_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {"name": "agent_card", "strict": True, "schema": _CardUpdate.model_json_schema()},
}

# Serialize updates per agent so two tasks finishing together don't overwrite each other's card
_agent_locks: Dict[str, asyncio.Lock] = {}


def _lock_for(agent_name: str) -> asyncio.Lock:
    lock = _agent_locks.get(agent_name)
    if lock is None:
        lock = _agent_locks[agent_name] = asyncio.Lock()
    return lock


async def update_agent_card(agent_name: str, instructions: str) -> None:
    """Rewrite the agent's card from its current card plus the log of the task it just finished."""
    async with _lock_for(agent_name):
        roster = get_agent_roster()
        roster.load()
        card = roster.get_card(agent_name)
        if card is None:
            logger.warning(f"[{agent_name}] Card update skipped: agent not in roster")
            return

        task_log = _render_task_log(agent_name, instructions)
        if not task_log:
            return

        settings = get_settings()
        try:
            response = await request_chat_completion(
                model=settings.card_updater_model,
                messages=[{"role": "user", "content": _build_prompt(card, task_log)}],
                system=_SYSTEM_PROMPT,
                api_key=settings.openrouter_api_key,
                response_format=_RESPONSE_FORMAT,
            )
            content = ((response.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            update = _CardUpdate.model_validate_json(content)
        except ValidationError as exc:
            # Structured outputs guarantee the shape, so this means a refusal or truncated output
            logger.warning(f"[{agent_name}] Card update returned unusable output: {exc}")
            return
        except Exception as exc:
            logger.warning(f"[{agent_name}] Card update failed: {exc}")
            return

        summary, artifacts = update.summary, update.artifacts
        if roster.update_card(agent_name, summary, artifacts):
            logger.info(f"[{agent_name}] Card updated ({len(artifacts)} artifacts)")


def _render_task_log(agent_name: str, instructions: str) -> str:
    """Render the log entries from this task's request onward."""
    entries = list(get_execution_agent_logs().iter_entries(agent_name))
    start = None
    for index in range(len(entries) - 1, -1, -1):
        tag, _, payload = entries[index]
        if tag == "agent_request" and payload == instructions:
            start = index
            break
    if start is None:
        return ""

    task_entries = entries[start:]
    if len(task_entries) > _MAX_TASK_ENTRIES:
        # Keep the request plus the most recent entries (which end with the final response)
        task_entries = [task_entries[0], *task_entries[-(_MAX_TASK_ENTRIES - 1):]]

    lines: List[str] = []
    for tag, _, payload in task_entries:
        text = payload if len(payload) <= _MAX_ENTRY_CHARS else payload[:_MAX_ENTRY_CHARS] + "…"
        lines.append(f"<{tag}>{text}</{tag}>")
    return "\n".join(lines)


def _build_prompt(card: AgentCard, task_log: str) -> str:
    current = json.dumps({"summary": card.summary, "artifacts": card.artifacts}, indent=2)
    return (
        f"<agent_name>{card.name}</agent_name>\n"
        f"<current_card>\n{current}\n</current_card>\n"
        f"<task_log>\n{task_log}\n</task_log>"
    )

