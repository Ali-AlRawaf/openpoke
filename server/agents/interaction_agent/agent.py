"""Interaction agent helpers for prompt construction."""

from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...config import get_settings
from ...services.execution import get_agent_roster

_prompt_path = Path(__file__).parent / "system_prompt.md"
SYSTEM_PROMPT = _prompt_path.read_text(encoding="utf-8").strip()


# Load and return the pre-defined system prompt from markdown file
def build_system_prompt() -> str:
    """Return the static system prompt for the interaction agent."""
    return SYSTEM_PROMPT


# Build structured message with conversation history, active agents, and current turn
def prepare_message_with_history(
    latest_text: str,
    transcript: str,
    message_type: str = "user",
) -> List[Dict[str, Any]]:
    """Compose a message that bundles history, roster, and the latest turn.

    The text is split into two content blocks: the shared context (history + roster) and the
    current turn. The model sees the same text either way; the split lets the context block
    carry a cache breakpoint so every call that shares it reads it from the prompt cache.
    """
    history = _render_conversation_history(transcript)
    roster = f"<active_agents>\n{_render_active_agents()}\n</active_agents>"
    context_block: Dict[str, Any] = {"type": "text", "text": f"{history}\n\n{roster}\n\n"}
    cache_control = _context_cache_control()
    if cache_control:
        context_block["cache_control"] = cache_control
    turn_block = {"type": "text", "text": _render_current_turn(latest_text, message_type)}
    return [{"role": "user", "content": [context_block, turn_block]}]


# Explicit cache breakpoint for the context block (Anthropic models only; others cache automatically)
def _context_cache_control() -> Optional[Dict[str, str]]:
    settings = get_settings()
    if not settings.prompt_cache_enabled or not settings.interaction_agent_model.startswith("anthropic/"):
        return None
    control = {"type": "ephemeral"}
    if settings.prompt_cache_ttl == "1h":
        control["ttl"] = "1h"
    return control


# Format conversation transcript into XML tags for LLM context
def _render_conversation_history(transcript: str) -> str:
    history = transcript.strip()
    if not history:
        history = "None"
    return f"<conversation_history>\n{history}\n</conversation_history>"


# Format currently active execution agents into XML tags for LLM awareness
def _render_active_agents() -> str:
    roster = get_agent_roster()
    roster.load()
    agents = roster.get_agents()

    if not agents:
        return "None"

    rendered: List[str] = []
    for agent_name in agents:
        name = escape(agent_name or "agent", quote=True)
        rendered.append(f'<agent name="{name}" />')

    return "\n".join(rendered)


# Wrap the current message in appropriate XML tags based on sender type
def _render_current_turn(latest_text: str, message_type: str) -> str:
    tag = "new_agent_message" if message_type == "agent" else "new_user_message"
    body = latest_text.strip()
    return f"<{tag}>\n{body}\n</{tag}>"
