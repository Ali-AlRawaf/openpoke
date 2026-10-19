"""Tool definitions for interaction agent."""

import asyncio
import json
from dataclasses import dataclass
from html import escape
from typing import Any, List, Optional

from pydantic import ValidationError

from ...config import get_settings
from ...logging_config import logger
from ...services.conversation import get_conversation_log
from ...services.execution import AgentCard, RosterError, get_agent_roster, get_execution_agent_logs
from ...services.execution.agent_search import search_agent_cards
from ...services.execution.roster import ARTIFACTS_DESCRIPTION
from ..execution_agent.batch_manager import ExecutionBatchManager


@dataclass
class ToolResult:
    """Standardized payload returned by interaction-agent tools."""

    success: bool
    payload: Any = None
    user_message: Optional[str] = None
    recorded_reply: bool = False

# Tool schemas for OpenRouter
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_agents",
            "description": (
                "Search existing execution agents for one to reuse. Returns agent cards, each with the agent's name, "
                "a summary of its work, and its artifacts: the specific things it's tied to. "
                f"If there are {get_settings().agent_search_top_k} or fewer agents, returns all of them and the query "
                f"isn't used. Otherwise, returns the {get_settings().agent_search_top_k} agents most similar to the "
                "query, ordered by similarity; similar agents aren't necessarily relevant to the task."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The task in specific terms: the names and topic it involves, with references from the conversation spelled out (e.g., 'Acme Supplies damaged gearbox replacement').",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_agent",
            "description": "Create a new execution agent with a card describing it. Use only when no existing agent fits the task. Then call send_message_to_agent with the same name; both calls can go in the same response.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Human-readable agent name describing its purpose (e.g., 'Vercel Job Offer', 'Email to Sharanjeet'). Must not match an existing agent.",
                    },
                    "summary": {
                        "type": "string",
                        "description": "What this agent is for, in one or two sentences, at most 500 characters (e.g., 'Gets a replacement for the damaged gearbox from Acme Supplies.').",
                    },
                    "artifacts": {
                        "type": "array",
                        "description": f"{ARTIFACTS_DESCRIPTION} Empty if none.",
                        "items": {"type": "string"},
                    },
                },
                "required": ["agent_name", "summary", "artifacts"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_message_to_agent",
            "description": "Deliver instructions to an existing execution agent. The agent must already exist: find it with search_agents, or create it with create_agent first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Exact name of an existing agent, as returned by search_agents or create_agent.",
                    },
                    "instructions": {"type": "string", "description": "Instructions for the agent to execute."},
                },
                "required": ["agent_name", "instructions"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_message_to_user",
            "description": "Deliver a natural-language response directly to the user. Use this for updates, confirmations, or any assistant response the user should see immediately.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Plain-text message that will be shown to the user and recorded in the conversation log.",
                    },
                },
                "required": ["message"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_draft",
            "description": "Record an email draft so the user can review the exact text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email for the draft.",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject for the draft.",
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content (plain text).",
                    },
                },
                "required": ["to", "subject", "body"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wait",
            "description": "Wait silently when a message is already in conversation history to avoid duplicating responses. Adds a <wait> log entry that is not visible to the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Brief explanation of why waiting (e.g., 'Message already sent', 'Draft already created').",
                    },
                },
                "required": ["reason"],
                "additionalProperties": False,
            },
        },
    },
]

_EXECUTION_BATCH_MANAGER = ExecutionBatchManager()


# Render one agent card as XML; cards without a summary or artifacts stay a single <agent /> tag
def _render_agent_card(card: AgentCard) -> str:
    attrs = f'name="{escape(card.name or "agent", quote=True)}"'
    if card.last_active_at:
        attrs += f' last_active="{escape(card.last_active_at, quote=True)}"'
    if not card.summary and not card.artifacts:
        return f"<agent {attrs} />"

    lines: List[str] = [f"<agent {attrs}>"]
    if card.summary:
        lines.append(f"  <summary>{escape(card.summary, quote=False)}</summary>")
    for artifact in card.artifacts:
        lines.append(f"  <artifact>{escape(artifact, quote=False)}</artifact>")
    lines.append("</agent>")
    return "\n".join(lines)


# Look up existing execution agents: the whole roster when small, otherwise the top matches by embedding
async def search_agents(query: str) -> ToolResult:
    """Return existing execution agents rendered as <agent> cards."""
    roster = get_agent_roster()
    roster.load()
    cards = roster.get_cards()
    top_k = get_settings().agent_search_top_k

    if len(cards) <= top_k:
        logger.info(f"Agent search returned all {len(cards)} agents", extra={"query": query})
        if not cards:
            return ToolResult(success=True, payload="<active_agents>\nNone\n</active_agents>")
        body = "\n".join(_render_agent_card(card) for card in cards)
        header = f"All {len(cards)} existing agents. No search was run, so this is the complete roster."
        return ToolResult(success=True, payload=f"{header}\n<active_agents>\n{body}\n</active_agents>")

    try:
        matches = await search_agent_cards(query, cards, top_k)
    except Exception as exc:
        # Without embeddings, fall back to every agent's name (the pre-search roster format) so
        # routing degrades to the old behaviour instead of failing
        logger.error(f"Agent search failed, returning all agent names: {exc}", extra={"query": query})
        body = "\n".join(f'<agent name="{escape(card.name, quote=True)}" />' for card in cards)
        header = f"All {len(cards)} existing agents, names only. Search is unavailable, so this is the complete roster."
        return ToolResult(success=True, payload=f"{header}\n<active_agents>\n{body}\n</active_agents>")

    logger.info(
        f"Agent search returned top {len(matches)} of {len(cards)} agents",
        extra={"query": query, "matches": [card.name for card in matches]},
    )
    body = "\n".join(_render_agent_card(card) for card in matches)
    header = (
        f"Search results: the {len(matches)} agents most similar to your query, out of {len(cards)} existing agents, "
        "ordered by similarity."
    )
    return ToolResult(success=True, payload=f"{header}\n<active_agents>\n{body}\n</active_agents>")


# Register a new execution agent with its identity card
def create_agent(agent_name: str, summary: str, artifacts: List[str]) -> ToolResult:
    """Create a new execution agent card in the roster."""
    roster = get_agent_roster()
    roster.load()

    try:
        card = AgentCard(name=agent_name, summary=summary, artifacts=artifacts)
    except ValidationError as exc:
        return ToolResult(success=False, payload={"error": f"Invalid agent card: {exc}"})

    try:
        added = roster.add_card(card)
    except RosterError as exc:
        logger.error(str(exc))
        return ToolResult(success=False, payload={"error": "Failed to save the new agent: the agent roster could not be written."})

    if not added:
        return ToolResult(
            success=False,
            payload={"error": f"An agent named '{agent_name}' already exists. Use send_message_to_agent to reuse it."},
        )

    logger.info(f"Created agent: {agent_name}")
    return ToolResult(success=True, payload={"status": "created", "agent_name": agent_name})


# Dispatch instructions to an existing execution agent asynchronously
def send_message_to_agent(agent_name: str, instructions: str) -> ToolResult:
    """Send instructions to an execution agent."""
    roster = get_agent_roster()
    roster.load()
    if roster.get_card(agent_name) is None:
        return ToolResult(
            success=False,
            payload={
                "error": (
                    f"No agent named '{agent_name}'. Use search_agents to find the existing agent, "
                    "or create_agent if none fits."
                )
            },
        )

    roster.touch(agent_name)
    get_execution_agent_logs().record_request(agent_name, instructions)

    logger.info(f"Dispatched to agent: {agent_name}")

    async def _execute_async() -> None:
        try:
            result = await _EXECUTION_BATCH_MANAGER.execute_agent(agent_name, instructions)
            status = "SUCCESS" if result.success else "FAILED"
            logger.info(f"Agent '{agent_name}' completed: {status}")
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"Agent '{agent_name}' failed: {str(exc)}")

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.error("No running event loop available for async execution")
        return ToolResult(success=False, payload={"error": "No event loop available"})

    loop.create_task(_execute_async())

    return ToolResult(
        success=True,
        payload={
            "status": "submitted",
            "agent_name": agent_name,
        },
    )


# Send immediate message to user and record in conversation history
def send_message_to_user(message: str) -> ToolResult:
    """Record a user-visible reply in the conversation log."""
    log = get_conversation_log()
    log.record_reply(message)

    return ToolResult(
        success=True,
        payload={"status": "delivered"},
        user_message=message,
        recorded_reply=True,
    )


# Format and record email draft for user review
def send_draft(
    to: str,
    subject: str,
    body: str,
) -> ToolResult:
    """Record a draft update in the conversation log for the interaction agent."""
    log = get_conversation_log()

    message = f"To: {to}\nSubject: {subject}\n\n{body}"

    log.record_reply(message)
    logger.info(f"Draft recorded for: {to}")

    return ToolResult(
        success=True,
        payload={
            "status": "draft_recorded",
            "to": to,
            "subject": subject,
        },
        recorded_reply=True,
    )


# Record silent wait state to avoid duplicate responses
def wait(reason: str) -> ToolResult:
    """Wait silently and add a wait log entry that is not visible to the user."""
    log = get_conversation_log()
    
    # Record a dedicated wait entry so the UI knows to ignore it
    log.record_wait(reason)
    

    return ToolResult(
        success=True,
        payload={
            "status": "waiting",
            "reason": reason,
        },
        recorded_reply=True,
    )


# Return predefined tool schemas for LLM function calling
def get_tool_schemas():
    """Return OpenAI-compatible tool schemas."""
    return TOOL_SCHEMAS


# Route tool calls to appropriate handlers with argument validation and error handling
def handle_tool_call(name: str, arguments: Any) -> ToolResult:
    """Handle tool calls from interaction agent."""
    try:
        if isinstance(arguments, str):
            args = json.loads(arguments) if arguments.strip() else {}
        elif isinstance(arguments, dict):
            args = arguments
        else:
            return ToolResult(success=False, payload={"error": "Invalid arguments format"})

        if name == "search_agents":
            return search_agents(**args)
        if name == "create_agent":
            return create_agent(**args)
        if name == "send_message_to_agent":
            return send_message_to_agent(**args)
        if name == "send_message_to_user":
            return send_message_to_user(**args)
        if name == "send_draft":
            return send_draft(**args)
        if name == "wait":
            return wait(**args)

        logger.warning("unexpected tool", extra={"tool": name})
        return ToolResult(success=False, payload={"error": f"Unknown tool: {name}"})
    except json.JSONDecodeError:
        return ToolResult(success=False, payload={"error": "Invalid JSON"})
    except TypeError as exc:
        return ToolResult(success=False, payload={"error": f"Missing required arguments: {exc}"})
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("tool call failed", extra={"tool": name, "error": str(exc)})
        return ToolResult(success=False, payload={"error": "Failed to execute"})
