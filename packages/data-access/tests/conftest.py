"""Test fixtures for Data Access activities.

Provides a MockEngine/MockConnection that mimics SQLAlchemy async engine behavior,
recording executed SQL and returning canned results. Activities use
`get_engine().begin()` — we mock `get_engine` to return our MockEngine.

Fixtures provide realistic civic engagement data: LinkedIn posts, emails,
X tweets, PostHog pageviews, RB2B enrichment.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest

# ============================================================================
# Mock SQLAlchemy async engine/connection
# ============================================================================


class MockCursorResult:
    """Mimics SQLAlchemy CursorResult for SELECT queries."""

    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self._rows = rows or []
        self.rowcount = len(self._rows)

    def fetchone(self) -> Any | None:
        if self._rows:
            return MappingRow(self._rows[0])
        return None

    def fetchall(self) -> list[Any]:
        return [MappingRow(r) for r in self._rows]

    def scalar(self) -> Any | None:
        if self._rows:
            first = self._rows[0]
            return next(iter(first.values()))
        return None

    def scalars(self) -> MockScalars:
        return MockScalars(self._rows)

    def __iter__(self):
        return iter(MappingRow(r) for r in self._rows)

    def mappings(self) -> MockMappings:
        return MockMappings(self._rows)


class MockMappings:
    """Mimics result.mappings() for dict-like row access."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def fetchall(self) -> list[dict[str, Any]]:
        return self._rows

    def fetchone(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None

    def all(self) -> list[dict[str, Any]]:
        return self._rows

    def __iter__(self):
        return iter(self._rows)


class MockScalars:
    """Mimics result.scalars() for single-column access."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return [next(iter(r.values())) for r in self._rows]

    def first(self) -> Any | None:
        if self._rows:
            return next(iter(self._rows[0].values()))
        return None


class MappingRow:
    """Mimics a SQLAlchemy Row that supports both attribute and index access."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return self._data.get(name)

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, int):
            return list(self._data.values())[key]
        return self._data[key]

    def _mapping(self) -> dict[str, Any]:
        return self._data

    @property
    def _asdict(self) -> dict[str, Any]:
        return self._data


class MockConnection:
    """Mimics AsyncConnection with execute() recording."""

    def __init__(self) -> None:
        self.executed: list[Any] = []
        self._responses: list[MockCursorResult] = []
        self._default_response = MockCursorResult()

    def queue_response(self, rows: list[dict[str, Any]]) -> None:
        """Queue a response for the next execute() call."""
        self._responses.append(MockCursorResult(rows))

    async def execute(self, stmt: Any, parameters: Any = None) -> MockCursorResult:
        self.executed.append(stmt)
        if self._responses:
            return self._responses.pop(0)
        return self._default_response

    async def __aenter__(self) -> MockConnection:
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass


class MockEngine:
    """Mimics AsyncEngine with begin() context manager."""

    def __init__(self) -> None:
        self.connection = MockConnection()

    def begin(self) -> MockEngine:
        return self

    async def __aenter__(self) -> MockConnection:
        return self.connection

    async def __aexit__(self, *args: Any) -> None:
        pass


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_engine() -> MockEngine:
    """Provide a MockEngine that records SQL calls."""
    return MockEngine()


@pytest.fixture
def mock_conn(mock_engine: MockEngine) -> MockConnection:
    """Shortcut to the connection for queueing responses."""
    return mock_engine.connection


# -- Realistic IDs --

SOURCE_UNIPILE_ID = str(uuid.uuid4())
SOURCE_X_ID = str(uuid.uuid4())
SOURCE_POSTHOG_ID = str(uuid.uuid4())
SOURCE_RB2B_ID = str(uuid.uuid4())

CHANNEL_LINKEDIN_ID = str(uuid.uuid4())
CHANNEL_X_ID = str(uuid.uuid4())
CHANNEL_EMAIL_ID = str(uuid.uuid4())
CHANNEL_WEBSITE_ID = str(uuid.uuid4())

PERSON_JANE_ID = str(uuid.uuid4())
PERSON_BOB_ID = str(uuid.uuid4())

CONTENT_POST_ID = str(uuid.uuid4())
CONTENT_TWEET_ID = str(uuid.uuid4())

ORG_UNLOCK_ID = str(uuid.uuid4())
EVENT_WORKSHOP_ID = str(uuid.uuid4())

PIPELINE_RUN_ID = str(uuid.uuid4())


@pytest.fixture
def source_rows() -> list[dict[str, Any]]:
    """Seed source lookup rows."""
    return [
        {"id": SOURCE_UNIPILE_ID, "source_key": "unipile"},
        {"id": SOURCE_X_ID, "source_key": "x"},
        {"id": SOURCE_POSTHOG_ID, "source_key": "posthog"},
        {"id": SOURCE_RB2B_ID, "source_key": "rb2b"},
    ]


@pytest.fixture
def channel_rows() -> list[dict[str, Any]]:
    """Seed channel lookup rows."""
    return [
        {"id": CHANNEL_LINKEDIN_ID, "channel_key": "linkedin"},
        {"id": CHANNEL_X_ID, "channel_key": "x"},
        {"id": CHANNEL_EMAIL_ID, "channel_key": "email"},
        {"id": CHANNEL_WEBSITE_ID, "channel_key": "website"},
    ]


@pytest.fixture
def person_jane_row() -> dict[str, Any]:
    """Jane Smith — a multi-platform contact."""
    return {
        "id": PERSON_JANE_ID,
        "display_name": "Jane Smith",
        "primary_email": "jane@example.com",
        "title": "Community Organizer",
        "company_name": "Unlock Alabama",
        "industry": "Civic Tech",
        "bio": "Building civic engagement tools",
        "first_seen_at": datetime(2026, 1, 1, tzinfo=UTC),
        "last_seen_at": datetime(2026, 2, 14, tzinfo=UTC),
        "is_active": True,
        "tags": ["organizer", "volunteer"],
    }


@pytest.fixture
def pipeline_run_row() -> dict[str, Any]:
    """An active pipeline run."""
    return {
        "id": PIPELINE_RUN_ID,
        "source_id": SOURCE_UNIPILE_ID,
        "status": "running",
        "started_at": datetime(2026, 2, 14, 10, 0, 0, tzinfo=UTC),
    }
