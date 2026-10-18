"""Write and parse log lines exactly as the server does.

Fixtures must be byte-compatible with server/data, so every line is produced with the
server's own encoder and checked with the server's own parsers.
"""

from __future__ import annotations

from typing import Optional, Tuple

from server.services.execution.log_store import ExecutionAgentLogStore, _encode_payload, _slugify

_parser = ExecutionAgentLogStore.__new__(ExecutionAgentLogStore)


def format_line(tag: str, payload: str, timestamp: Optional[str] = None) -> str:
    """Return one encoded log line (with trailing newline), as written by the server."""
    encoded = _encode_payload(str(payload))
    if timestamp:
        return f'<{tag} timestamp="{timestamp}">{encoded}</{tag}>\n'
    return f"<{tag}>{encoded}</{tag}>\n"


def parse_line(line: str) -> Optional[Tuple[str, str, str]]:
    """Parse a line the way the server does; None means the server would silently drop it."""
    return _parser._parse_line(line)


def agent_log_filename(agent_name: str) -> str:
    """File name the server uses for an execution agent's log."""
    return f"{_slugify(agent_name)}.log"


__all__ = ["format_line", "parse_line", "agent_log_filename"]
