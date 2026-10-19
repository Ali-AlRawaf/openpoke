"""Agent roster management - a list of agent cards (name, summary, artifacts)."""

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator, List, Optional, TypeVar

from pydantic import BaseModel, Field

from ...config import data_dir
from ...logging_config import logger
from ...utils.timezones import now_in_user_timezone

_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

T = TypeVar("T")

# What artifacts are, shared by the create_agent tool schema and the card updater prompt
ARTIFACTS_DESCRIPTION = (
    "Short strings for what this agent's work involves, as someone would mention it later: people, organizations, "
    "email addresses, events, places, objects, topics (e.g., 'Acme Supplies <support@acmesupplies.com>', "
    "'damaged gearbox replacement', 'courier pick-up on 2026-11-15'). Not system IDs such as draft, thread, or "
    "message IDs. At most 15 artifacts, each at most 50 characters."
)


class RosterError(Exception):
    """roster.json could not be read or written."""


def _now() -> str:
    return now_in_user_timezone(_TIMESTAMP_FORMAT)


class AgentCard(BaseModel):
    """Identity of an execution agent, used to find it again for reuse.

    `artifacts` are free-form strings for the specific things the agent is tied to (see
    ARTIFACTS_DESCRIPTION).
    """

    name: str
    summary: str = ""
    artifacts: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=_now)
    last_active_at: str = Field(default_factory=_now)


class AgentRoster:
    """Roster that stores agent cards in a JSON file shared by the interaction and execution agents.

    Every access holds an flock on a sidecar lock file: shared for reads, exclusive for
    read-modify-write. Writes go to a temp file that atomically replaces roster.json, so a
    crash never leaves a half-written roster.
    """

    def __init__(self, roster_path: Path):
        self._roster_path = roster_path
        self._lock_path = roster_path.with_name(roster_path.name + ".lock")
        self._cards: list[AgentCard] = []
        self.load()

    @contextmanager
    def _locked(self, exclusive: bool) -> Iterator[None]:
        self._roster_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._lock_path, "a") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _read(self) -> list[AgentCard]:
        """Read cards from disk; caller holds the lock. Raises on a corrupt file."""
        if not self._roster_path.exists():
            return []
        with open(self._roster_path, "r") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("roster.json must contain a JSON list")
        return [self._parse_entry(entry) for entry in data]

    @staticmethod
    def _parse_entry(entry: object) -> AgentCard:
        if isinstance(entry, dict):
            return AgentCard.model_validate(entry)
        # Legacy format: a bare agent name
        return AgentCard(name=str(entry), created_at="", last_active_at="")

    def _write(self, cards: list[AgentCard]) -> None:
        """Atomically replace roster.json; caller holds the exclusive lock."""
        fd, tmp_path = tempfile.mkstemp(dir=self._roster_path.parent, prefix=".roster-", suffix=".json")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump([card.model_dump() for card in cards], f, indent=2)
            os.replace(tmp_path, self._roster_path)
        except BaseException:
            Path(tmp_path).unlink(missing_ok=True)
            raise

    def _mutate(self, change: Callable[[list[AgentCard]], T]) -> T:
        """Read the latest roster, apply `change`, and write it back, all under the exclusive lock.

        `change` edits the list in place and returns a result. Raises RosterError if the roster
        can't be read or written, so a corrupt file is never overwritten.
        """
        try:
            with self._locked(exclusive=True):
                cards = self._read()
                result = change(cards)
                self._write(cards)
                self._cards = cards
                return result
        except Exception as exc:
            raise RosterError(f"Failed to update roster.json: {exc}") from exc

    def load(self) -> None:
        """Reload agent cards from roster.json (legacy lists of names become bare cards)."""
        try:
            with self._locked(exclusive=False):
                self._cards = self._read()
        except Exception as exc:
            logger.warning(f"Failed to load roster.json: {exc}")
            self._cards = []

    def add_card(self, card: AgentCard) -> bool:
        """Add an agent card; returns False if an agent with that name already exists.

        Raises RosterError if the roster can't be read or written.
        """

        def change(cards: list[AgentCard]) -> bool:
            if any(existing.name == card.name for existing in cards):
                return False
            cards.append(card)
            return True

        return self._mutate(change)

    def touch(self, agent_name: str) -> None:
        """Mark an agent as active now (best effort: failures are logged, not raised)."""

        def change(cards: list[AgentCard]) -> None:
            for existing in cards:
                if existing.name == agent_name:
                    existing.last_active_at = _now()

        try:
            self._mutate(change)
        except RosterError as exc:
            logger.warning(str(exc))

    def update_card(self, agent_name: str, summary: str, artifacts: List[str]) -> bool:
        """Replace an agent's summary and artifacts; returns False if the agent doesn't exist
        or the roster can't be written (logged)."""

        def change(cards: list[AgentCard]) -> bool:
            for existing in cards:
                if existing.name == agent_name:
                    existing.summary = summary
                    existing.artifacts = list(artifacts)
                    return True
            return False

        try:
            return self._mutate(change)
        except RosterError as exc:
            logger.warning(str(exc))
            return False

    def get_card(self, agent_name: str) -> Optional[AgentCard]:
        """Get the card for an agent by exact name (from the last load)."""
        for card in self._cards:
            if card.name == agent_name:
                return card
        return None

    def get_cards(self) -> list[AgentCard]:
        """Get all agent cards in creation order (from the last load)."""
        return list(self._cards)

    def get_agents(self) -> list[str]:
        """Get list of all agent names (from the last load)."""
        return [card.name for card in self._cards]

    def clear(self) -> None:
        """Clear the agent roster."""
        try:
            with self._locked(exclusive=True):
                self._roster_path.unlink(missing_ok=True)
                self._cards = []
            logger.info("Cleared agent roster")
        except Exception as exc:
            logger.warning(f"Failed to clear roster.json: {exc}")


_DATA_DIR = data_dir()
_ROSTER_PATH = _DATA_DIR / "execution_agents" / "roster.json"

_agent_roster = AgentRoster(_ROSTER_PATH)


def get_agent_roster() -> AgentRoster:
    """Get the singleton roster instance."""
    return _agent_roster
