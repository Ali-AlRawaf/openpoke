"""Tool definitions for interaction agent."""

import asyncio
import json
from dataclasses import dataclass
from html import escape
from typing import Any, List, Optional

from pydantic import ValidationError

from ...logging_config import logger
from ...services.conversation import get_conversation_log
from ...services.execution import AgentCard, RosterError, get_agent_roster, get_execution_agent_logs
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
            "description": "Search existing execution agents to find one to reuse before creating a new one. Returns matching agent cards: name, summary, and the artifacts (people, organizations, events, threads, ...) each agent is tied to.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What the task involves: the people, organizations, and topic (e.g., 'Ali Al Rawaf lunch invite', 'Ironwood gym membership hold').",
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
            "description": "Create a new execution agent. Only do this when search_agents found no relevant existing agent. Then call send_message_to_agent with the same name to give it instructions; both calls can go in the same response.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Human-readable agent name describing its purpose (e.g., 'Vercel Job Offer', 'Email to Sharanjeet'). Must not match an existing agent.",
                    },
                    "summary": {
                        "type": "string",
                        "description": "One or two sentences on what this agent is for and who it deals with, at most 500 characters (e.g., 'Handles booking and rescheduling Theo's dental cleanings with Tidewater Dental.').",
                    },
                    "artifacts": {
                        "type": "array",
                        "description": (
                            "Short strings for anything this agent is tied to: people, organizations, email addresses, "
                            "events and dates, threads, places. Include identifiers when known (e.g., "
                            "'Ironwood Fitness <members@ironwoodfit.ca>, Theo's gym', 'membership hold through Nov 30', "
                            "'Wedding at Harrow Hill, 2027-06-12'). At most 15 artifacts, each at most 150 characters. "
                            "Empty if none."
                        ),
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


# Look up existing execution agents; for now returns the full roster regardless of query
def search_agents(query: str) -> ToolResult:
    """Return existing execution agents rendered as <agent> cards."""
    roster = get_agent_roster()
    roster.load()
    cards = roster.get_cards()

    body = "\n".join(_render_agent_card(card) for card in cards) if cards else "None"

    logger.info(f"Agent search returned {len(cards)} agents", extra={"query": query})
    return ToolResult(success=True, payload=f"<active_agents>\n{body}\n</active_agents>")


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
