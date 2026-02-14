"""Tests for Data Access activities — all 10 business verb activities.

Each test mocks get_engine() to return MockEngine, queues canned responses,
calls the activity, and asserts the result. Tests are written BEFORE activities.

Pattern: unittest.mock.patch("unlock_data_access.activities.get_engine")
returns MockEngine that records SQL calls and returns canned results.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch

import pytest
from unlock_shared.data_models import (
    CatalogContentRequest,
    ClosePipelineRunRequest,
    CommunicationRecord,
    ContentRecord,
    EngagementRecord,
    EnrollMemberRequest,
    IdentifyContactRequest,
    LogCommunicationRequest,
    MembershipRecord,
    OpenPipelineRunRequest,
    ParticipationRecord,
    PersonEmail,
    PersonLocation,
    PersonName,
    PersonPhone,
    ProfileContactRequest,
    RecordEngagementRequest,
    RegisterParticipationRequest,
    SurveyEngagementRequest,
)

# -- Realistic IDs (independent from conftest, consistent within this module) --

SOURCE_UNIPILE_ID = str(uuid.uuid4())
SOURCE_X_ID = str(uuid.uuid4())
SOURCE_POSTHOG_ID = str(uuid.uuid4())

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


# -- Inline mock engine (avoids cross-package conftest import collision) --


class _MappingRow:
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


class _MockCursorResult:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self._rows = rows or []
        self.rowcount = len(self._rows)

    def fetchone(self) -> Any | None:
        return _MappingRow(self._rows[0]) if self._rows else None

    def fetchall(self) -> list[Any]:
        return [_MappingRow(r) for r in self._rows]

    def scalar(self) -> Any | None:
        return next(iter(self._rows[0].values())) if self._rows else None

    def __iter__(self):
        return iter(_MappingRow(r) for r in self._rows)


class _MockConnection:
    def __init__(self) -> None:
        self.executed: list[Any] = []
        self._responses: list[_MockCursorResult] = []
        self._default_response = _MockCursorResult()

    def queue_response(self, rows: list[dict[str, Any]]) -> None:
        self._responses.append(_MockCursorResult(rows))

    async def execute(self, stmt: Any, parameters: Any = None) -> _MockCursorResult:
        self.executed.append(stmt)
        if self._responses:
            return self._responses.pop(0)
        return self._default_response

    async def __aenter__(self) -> _MockConnection:
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass


class MockEngine:
    def __init__(self) -> None:
        self.connection = _MockConnection()

    def begin(self) -> MockEngine:
        return self

    async def __aenter__(self) -> _MockConnection:
        return self.connection

    async def __aexit__(self, *args: Any) -> None:
        pass


@pytest.fixture
def engine() -> MockEngine:
    return MockEngine()


def _patch_engine(engine: MockEngine):
    return patch("unlock_data_access.activities.get_engine", return_value=engine)


# ============================================================================
# identify_contact
# ============================================================================


class TestIdentifyContact:
    """identify_contact: resolve external identity to internal person."""

    @pytest.mark.asyncio
    async def test_new_contact(self, engine: MockEngine):
        """When no source_mapping exists, creates a new person."""
        conn = engine.connection
        new_person_id = str(uuid.uuid4())

        # 1. source lookup
        conn.queue_response([{"id": SOURCE_UNIPILE_ID}])
        # 2. channel lookup
        conn.queue_response([{"id": CHANNEL_LINKEDIN_ID}])
        # 3. source_mapping lookup — not found
        conn.queue_response([])
        # 4. insert person
        conn.queue_response([{"id": new_person_id}])
        # 5. insert source_mapping
        conn.queue_response([{"id": str(uuid.uuid4())}])
        # 6. insert channel_identity
        conn.queue_response([{"id": str(uuid.uuid4())}])
        # 7. insert person_name
        conn.queue_response([{"id": str(uuid.uuid4())}])
        # 8. insert person_email
        conn.queue_response([{"id": str(uuid.uuid4())}])

        from unlock_data_access.activities import identify_contact

        req = IdentifyContactRequest(
            source_key="unipile",
            external_id="unipile-user-123",
            channel_key="linkedin",
            platform_user_id="li-123",
            display_name="Jane Smith",
            names=[PersonName(first_name="Jane", last_name="Smith", display_name="Jane Smith")],
            emails=[PersonEmail(email="jane@example.com", is_primary=True)],
        )

        with _patch_engine(engine):
            result = await identify_contact(req)

        assert result.success is True
        assert result.is_new is True
        assert result.person_id == new_person_id
        assert len(conn.executed) >= 4  # At least source, channel, mapping lookup, insert

    @pytest.mark.asyncio
    async def test_existing_contact(self, engine: MockEngine):
        """When source_mapping exists, returns existing person."""
        conn = engine.connection

        # 1. source lookup
        conn.queue_response([{"id": SOURCE_UNIPILE_ID}])
        # 2. channel lookup (not needed if no channel_key, but let's include)
        conn.queue_response([{"id": CHANNEL_LINKEDIN_ID}])
        # 3. source_mapping lookup — found
        conn.queue_response([{"internal_id": PERSON_JANE_ID}])

        from unlock_data_access.activities import identify_contact

        req = IdentifyContactRequest(
            source_key="unipile",
            external_id="unipile-user-123",
            channel_key="linkedin",
        )

        with _patch_engine(engine):
            result = await identify_contact(req)

        assert result.success is True
        assert result.is_new is False
        assert result.person_id == PERSON_JANE_ID

    @pytest.mark.asyncio
    async def test_with_phone_and_location(self, engine: MockEngine):
        """New contact with full history: name, email, phone, location."""
        conn = engine.connection
        new_id = str(uuid.uuid4())

        # source, channel, mapping(empty), insert person, mapping,
        # identity, name, email, phone, location
        conn.queue_response([{"id": SOURCE_UNIPILE_ID}])
        conn.queue_response([{"id": CHANNEL_LINKEDIN_ID}])
        conn.queue_response([])
        conn.queue_response([{"id": new_id}])
        conn.queue_response([{"id": str(uuid.uuid4())}])
        conn.queue_response([{"id": str(uuid.uuid4())}])
        conn.queue_response([{"id": str(uuid.uuid4())}])
        conn.queue_response([{"id": str(uuid.uuid4())}])
        conn.queue_response([{"id": str(uuid.uuid4())}])
        conn.queue_response([{"id": str(uuid.uuid4())}])

        from unlock_data_access.activities import identify_contact

        req = IdentifyContactRequest(
            source_key="unipile",
            external_id="ext-456",
            channel_key="linkedin",
            names=[PersonName(first_name="Bob", last_name="Jones")],
            emails=[PersonEmail(email="bob@example.com")],
            phones=[PersonPhone(phone="+12055551234", phone_type="mobile")],
            locations=[PersonLocation(city="Birmingham", state="AL", country="US")],
        )

        with _patch_engine(engine):
            result = await identify_contact(req)

        assert result.success is True
        assert result.is_new is True

    @pytest.mark.asyncio
    async def test_db_error_returns_failure(self, engine: MockEngine):
        """DB errors are wrapped into PlatformResult(success=False)."""
        conn = engine.connection

        # Make source lookup raise
        async def failing_execute(stmt, params=None):
            raise Exception("Connection refused")

        conn.execute = failing_execute

        from unlock_data_access.activities import identify_contact

        req = IdentifyContactRequest(
            source_key="unipile",
            external_id="user-err",
        )

        with _patch_engine(engine):
            result = await identify_contact(req)

        assert result.success is False
        assert "Connection refused" in result.message


# ============================================================================
# catalog_content
# ============================================================================


class TestCatalogContent:
    """catalog_content: register content items in the engagement graph."""

    @pytest.mark.asyncio
    async def test_new_content(self, engine: MockEngine):
        """Inserts new content with dedup via source_mappings."""
        conn = engine.connection

        # 1. source lookup
        conn.queue_response([{"id": SOURCE_X_ID}])
        # 2. channel lookup
        conn.queue_response([{"id": CHANNEL_X_ID}])
        # 3. source_mapping lookup — not found (new content)
        conn.queue_response([])
        # 4. insert content
        conn.queue_response([{"id": CONTENT_TWEET_ID}])
        # 5. insert source_mapping
        conn.queue_response([{"id": str(uuid.uuid4())}])

        from unlock_data_access.activities import catalog_content

        req = CatalogContentRequest(
            source_key="x",
            records=[
                ContentRecord(
                    channel_key="x",
                    content_type="tweet",
                    external_id="tweet-123",
                    body="Building civic tech in Alabama!",
                    published_at=datetime(2026, 2, 14, tzinfo=UTC),
                    like_count=42,
                    retweet_count=5,
                )
            ],
        )

        with _patch_engine(engine):
            result = await catalog_content(req)

        assert result.success is True
        assert result.created == 1

    @pytest.mark.asyncio
    async def test_duplicate_content_skipped(self, engine: MockEngine):
        """Existing content (found in source_mappings) is skipped."""
        conn = engine.connection

        conn.queue_response([{"id": SOURCE_X_ID}])
        conn.queue_response([{"id": CHANNEL_X_ID}])
        # source_mapping found — content already exists
        conn.queue_response([{"internal_id": CONTENT_TWEET_ID}])

        from unlock_data_access.activities import catalog_content

        req = CatalogContentRequest(
            source_key="x",
            records=[
                ContentRecord(
                    channel_key="x",
                    content_type="tweet",
                    external_id="tweet-123",
                    body="Duplicate tweet",
                )
            ],
        )

        with _patch_engine(engine):
            result = await catalog_content(req)

        assert result.success is True
        assert result.skipped == 1
        assert result.created == 0

    @pytest.mark.asyncio
    async def test_batch_content(self, engine: MockEngine):
        """Multiple content records in one batch."""
        conn = engine.connection

        conn.queue_response([{"id": SOURCE_UNIPILE_ID}])
        # Record 1: linkedin post
        conn.queue_response([{"id": CHANNEL_LINKEDIN_ID}])
        conn.queue_response([])
        conn.queue_response([{"id": str(uuid.uuid4())}])
        conn.queue_response([{"id": str(uuid.uuid4())}])
        # Record 2: email
        conn.queue_response([{"id": CHANNEL_EMAIL_ID}])
        conn.queue_response([])
        conn.queue_response([{"id": str(uuid.uuid4())}])
        conn.queue_response([{"id": str(uuid.uuid4())}])

        from unlock_data_access.activities import catalog_content

        req = CatalogContentRequest(
            source_key="unipile",
            records=[
                ContentRecord(channel_key="linkedin", content_type="post", external_id="li-1"),
                ContentRecord(channel_key="email", content_type="email", external_id="em-1"),
            ],
        )

        with _patch_engine(engine):
            result = await catalog_content(req)

        assert result.success is True
        assert result.created == 2


# ============================================================================
# record_engagement
# ============================================================================


class TestRecordEngagement:
    """record_engagement: capture person+content interactions."""

    @pytest.mark.asyncio
    async def test_batch_engagements(self, engine: MockEngine):
        conn = engine.connection

        # source lookup
        conn.queue_response([{"id": SOURCE_POSTHOG_ID}])
        # For each engagement: channel, person mapping, content mapping, insert
        # Engagement 1
        conn.queue_response([{"id": CHANNEL_WEBSITE_ID}])
        conn.queue_response([{"internal_id": PERSON_JANE_ID}])
        conn.queue_response([{"internal_id": CONTENT_POST_ID}])
        conn.queue_response([{"id": str(uuid.uuid4())}])
        # Engagement 2
        conn.queue_response([{"id": CHANNEL_WEBSITE_ID}])
        conn.queue_response([{"internal_id": PERSON_BOB_ID}])
        conn.queue_response([{"internal_id": CONTENT_POST_ID}])
        conn.queue_response([{"id": str(uuid.uuid4())}])

        from unlock_data_access.activities import record_engagement

        req = RecordEngagementRequest(
            source_key="posthog",
            records=[
                EngagementRecord(
                    person_external_id="jane-ph",
                    content_external_id="page-1",
                    channel_key="website",
                    engagement_type="view",
                    occurred_at=datetime(2026, 2, 14, tzinfo=UTC),
                    device_type="desktop",
                    browser="Chrome",
                ),
                EngagementRecord(
                    person_external_id="bob-ph",
                    content_external_id="page-1",
                    channel_key="website",
                    engagement_type="click",
                    occurred_at=datetime(2026, 2, 14, tzinfo=UTC),
                    target_url="https://example.com/signup",
                ),
            ],
        )

        with _patch_engine(engine):
            result = await record_engagement(req)

        assert result.success is True
        assert result.recorded == 2

    @pytest.mark.asyncio
    async def test_missing_person_skips(self, engine: MockEngine):
        """If person not found in source_mappings, engagement is skipped."""
        conn = engine.connection

        conn.queue_response([{"id": SOURCE_POSTHOG_ID}])
        conn.queue_response([{"id": CHANNEL_WEBSITE_ID}])
        # person not found
        conn.queue_response([])

        from unlock_data_access.activities import record_engagement

        req = RecordEngagementRequest(
            source_key="posthog",
            records=[
                EngagementRecord(
                    person_external_id="unknown-user",
                    content_external_id="page-1",
                    channel_key="website",
                    engagement_type="view",
                    occurred_at=datetime(2026, 2, 14, tzinfo=UTC),
                ),
            ],
        )

        with _patch_engine(engine):
            result = await record_engagement(req)

        assert result.success is True
        assert result.recorded == 0
        assert result.skipped == 1


# ============================================================================
# log_communication
# ============================================================================


class TestLogCommunication:
    """log_communication: capture person-to-person messages."""

    @pytest.mark.asyncio
    async def test_email_with_recipients(self, engine: MockEngine):
        conn = engine.connection

        # source
        conn.queue_response([{"id": SOURCE_UNIPILE_ID}])
        # channel
        conn.queue_response([{"id": CHANNEL_EMAIL_ID}])
        # sender mapping
        conn.queue_response([{"internal_id": PERSON_JANE_ID}])
        # insert message
        msg_id = str(uuid.uuid4())
        conn.queue_response([{"id": msg_id}])
        # recipient 1 mapping
        conn.queue_response([{"internal_id": PERSON_BOB_ID}])
        # insert recipient
        conn.queue_response([{"id": str(uuid.uuid4())}])

        from unlock_data_access.activities import log_communication

        req = LogCommunicationRequest(
            source_key="unipile",
            records=[
                CommunicationRecord(
                    sender_external_id="jane-unipile",
                    channel_key="email",
                    subject="Welcome to Unlock Alabama!",
                    body_plain="Hello Bob, welcome aboard...",
                    sent_at=datetime(2026, 2, 14, tzinfo=UTC),
                    recipient_ids=["bob-unipile"],
                )
            ],
        )

        with _patch_engine(engine):
            result = await log_communication(req)

        assert result.success is True
        assert result.logged == 1


# ============================================================================
# register_participation
# ============================================================================


class TestRegisterParticipation:
    """register_participation: record event attendance/completion."""

    @pytest.mark.asyncio
    async def test_event_attendance(self, engine: MockEngine):
        conn = engine.connection

        # source
        conn.queue_response([{"id": SOURCE_UNIPILE_ID}])
        # person mapping
        conn.queue_response([{"internal_id": PERSON_JANE_ID}])
        # event lookup by title
        conn.queue_response([{"id": EVENT_WORKSHOP_ID}])
        # insert participation
        conn.queue_response([{"id": str(uuid.uuid4())}])

        from unlock_data_access.activities import register_participation

        req = RegisterParticipationRequest(
            source_key="unipile",
            records=[
                ParticipationRecord(
                    person_external_id="jane-unipile",
                    event_title="Civic Tech Workshop",
                    participation_type="attended",
                    attended_at=datetime(2026, 2, 14, tzinfo=UTC),
                    feedback_score=5,
                    feedback_text="Great workshop!",
                )
            ],
        )

        with _patch_engine(engine):
            result = await register_participation(req)

        assert result.success is True
        assert result.registered == 1


# ============================================================================
# enroll_member
# ============================================================================


class TestEnrollMember:
    """enroll_member: record organizational affiliation."""

    @pytest.mark.asyncio
    async def test_new_membership(self, engine: MockEngine):
        conn = engine.connection

        # source
        conn.queue_response([{"id": SOURCE_UNIPILE_ID}])
        # person mapping
        conn.queue_response([{"internal_id": PERSON_JANE_ID}])
        # org lookup by name
        conn.queue_response([{"id": ORG_UNLOCK_ID}])
        # insert membership
        conn.queue_response([{"id": str(uuid.uuid4())}])

        from unlock_data_access.activities import enroll_member

        req = EnrollMemberRequest(
            source_key="unipile",
            records=[
                MembershipRecord(
                    person_external_id="jane-unipile",
                    organization_name="Unlock Alabama",
                    organization_type="nonprofit",
                    role="volunteer",
                    is_active=True,
                )
            ],
        )

        with _patch_engine(engine):
            result = await enroll_member(req)

        assert result.success is True
        assert result.enrolled == 1

    @pytest.mark.asyncio
    async def test_org_auto_created(self, engine: MockEngine):
        """If organization doesn't exist, it should be created."""
        conn = engine.connection

        conn.queue_response([{"id": SOURCE_UNIPILE_ID}])
        conn.queue_response([{"internal_id": PERSON_BOB_ID}])
        # org not found
        conn.queue_response([])
        # insert org
        new_org_id = str(uuid.uuid4())
        conn.queue_response([{"id": new_org_id}])
        # insert membership
        conn.queue_response([{"id": str(uuid.uuid4())}])

        from unlock_data_access.activities import enroll_member

        req = EnrollMemberRequest(
            source_key="unipile",
            records=[
                MembershipRecord(
                    person_external_id="bob-unipile",
                    organization_name="New Corp",
                    organization_type="company",
                    role="staff",
                )
            ],
        )

        with _patch_engine(engine):
            result = await enroll_member(req)

        assert result.success is True
        assert result.enrolled == 1


# ============================================================================
# profile_contact
# ============================================================================


class TestProfileContact:
    """profile_contact: assemble unified contact view."""

    @pytest.mark.asyncio
    async def test_by_person_id(self, engine: MockEngine):
        conn = engine.connection

        # person lookup
        conn.queue_response([{
            "id": PERSON_JANE_ID,
            "display_name": "Jane Smith",
            "primary_email": "jane@example.com",
            "title": "Community Organizer",
            "company_name": "Unlock Alabama",
            "bio": "Civic tech builder",
            "first_seen_at": datetime(2026, 1, 1, tzinfo=UTC),
            "last_seen_at": datetime(2026, 2, 14, tzinfo=UTC),
            "tags": ["organizer"],
        }])
        # names
        conn.queue_response([
            {"first_name": "Jane", "last_name": "Smith", "display_name": "Jane Smith",
             "name_type": "legal", "is_current": True, "channel_key": "linkedin"},
        ])
        # emails
        conn.queue_response([
            {"email": "jane@example.com", "email_type": "work", "is_primary": True},
        ])
        # phones
        conn.queue_response([
            {"phone": "+12055551234", "phone_type": "mobile", "is_primary": True},
        ])
        # locations
        conn.queue_response([
            {"city": "Birmingham", "state": "AL", "country": "US", "is_current": True},
        ])
        # identities
        conn.queue_response([
            {"channel_key": "linkedin", "username": "janesmith", "platform_user_id": "li-123"},
            {"channel_key": "x", "username": "jane_tweets", "platform_user_id": "x-456"},
        ])
        # engagement summary (count by type)
        conn.queue_response([
            {"engagement_type": "like", "count": 42},
            {"engagement_type": "view", "count": 100},
        ])
        # memberships
        conn.queue_response([
            {"organization_name": "Unlock Alabama", "role": "volunteer", "is_active": True},
        ])

        from unlock_data_access.activities import profile_contact

        req = ProfileContactRequest(person_id=PERSON_JANE_ID)

        with _patch_engine(engine):
            result = await profile_contact(req)

        assert result.success is True
        assert result.person_id == PERSON_JANE_ID
        assert result.display_name == "Jane Smith"
        assert len(result.names) == 1
        assert len(result.emails) == 1
        assert len(result.phones) == 1
        assert len(result.identities) == 2
        assert result.engagement_summary["like"] == 42

    @pytest.mark.asyncio
    async def test_by_email(self, engine: MockEngine):
        """Can look up contact by email address."""
        conn = engine.connection

        # email lookup → person_id
        conn.queue_response([{"person_id": PERSON_JANE_ID}])
        # Then same flow as by_person_id
        conn.queue_response([{
            "id": PERSON_JANE_ID,
            "display_name": "Jane Smith",
            "primary_email": "jane@example.com",
            "title": None, "company_name": None, "bio": None,
            "first_seen_at": None, "last_seen_at": None, "tags": None,
        }])
        conn.queue_response([])  # names
        conn.queue_response([])  # emails
        conn.queue_response([])  # phones
        conn.queue_response([])  # locations
        conn.queue_response([])  # identities
        conn.queue_response([])  # engagements
        conn.queue_response([])  # memberships

        from unlock_data_access.activities import profile_contact

        req = ProfileContactRequest(email="jane@example.com")

        with _patch_engine(engine):
            result = await profile_contact(req)

        assert result.success is True
        assert result.person_id == PERSON_JANE_ID

    @pytest.mark.asyncio
    async def test_not_found(self, engine: MockEngine):
        conn = engine.connection
        conn.queue_response([])  # person not found

        from unlock_data_access.activities import profile_contact

        req = ProfileContactRequest(person_id=str(uuid.uuid4()))

        with _patch_engine(engine):
            result = await profile_contact(req)

        assert result.success is False
        assert "not found" in result.message.lower()


# ============================================================================
# survey_engagement
# ============================================================================


class TestSurveyEngagement:
    """survey_engagement: broad view of engagement data."""

    @pytest.mark.asyncio
    async def test_filtered_query(self, engine: MockEngine):
        conn = engine.connection

        # channel lookup (survey_engagement resolves channel_key)
        conn.queue_response([{"id": CHANNEL_LINKEDIN_ID}])
        # count query
        conn.queue_response([{"count": 2}])
        # data query
        conn.queue_response([
            {
                "engagement_type": "like",
                "occurred_at": "2026-02-14T10:00:00+00:00",
                "person_id": PERSON_JANE_ID,
                "content_id": CONTENT_POST_ID,
                "channel_key": "linkedin",
            },
            {
                "engagement_type": "comment",
                "occurred_at": "2026-02-14T11:00:00+00:00",
                "person_id": PERSON_BOB_ID,
                "content_id": CONTENT_POST_ID,
                "channel_key": "linkedin",
            },
        ])

        from unlock_data_access.activities import survey_engagement

        req = SurveyEngagementRequest(
            channel_key="linkedin",
            since=datetime(2026, 2, 14, tzinfo=UTC),
            limit=10,
        )

        with _patch_engine(engine):
            result = await survey_engagement(req)

        assert result.success is True
        assert result.total_count == 2
        assert len(result.records) == 2
        assert result.has_more is False

    @pytest.mark.asyncio
    async def test_pagination(self, engine: MockEngine):
        conn = engine.connection

        conn.queue_response([{"count": 50}])
        conn.queue_response([{"engagement_type": "view"}] * 10)

        from unlock_data_access.activities import survey_engagement

        req = SurveyEngagementRequest(limit=10, offset=0)

        with _patch_engine(engine):
            result = await survey_engagement(req)

        assert result.success is True
        assert result.total_count == 50
        assert result.has_more is True


# ============================================================================
# open_pipeline_run / close_pipeline_run
# ============================================================================


class TestPipelineRunLifecycle:
    """open/close_pipeline_run: ingestion execution tracking."""

    @pytest.mark.asyncio
    async def test_open(self, engine: MockEngine):
        conn = engine.connection

        conn.queue_response([{"id": SOURCE_UNIPILE_ID}])
        conn.queue_response([{"id": PIPELINE_RUN_ID}])

        from unlock_data_access.activities import open_pipeline_run

        req = OpenPipelineRunRequest(
            source_key="unipile",
            workflow_run_id="wf-abc-123",
            resource_type="posts",
        )

        with _patch_engine(engine):
            result = await open_pipeline_run(req)

        assert result.success is True
        assert result.pipeline_run_id == PIPELINE_RUN_ID

    @pytest.mark.asyncio
    async def test_close_success(self, engine: MockEngine):
        conn = engine.connection

        # Update pipeline_run
        conn.queue_response([{
            "id": PIPELINE_RUN_ID,
            "duration_seconds": 45.2,
        }])

        from unlock_data_access.activities import close_pipeline_run

        req = ClosePipelineRunRequest(
            pipeline_run_id=PIPELINE_RUN_ID,
            status="completed",
            record_count=100,
            records_created=80,
            records_updated=15,
            records_skipped=5,
            pages_fetched=10,
        )

        with _patch_engine(engine):
            result = await close_pipeline_run(req)

        assert result.success is True
        assert result.pipeline_run_id == PIPELINE_RUN_ID

    @pytest.mark.asyncio
    async def test_close_failure(self, engine: MockEngine):
        conn = engine.connection

        conn.queue_response([{
            "id": PIPELINE_RUN_ID,
            "duration_seconds": 12.5,
        }])

        from unlock_data_access.activities import close_pipeline_run

        req = ClosePipelineRunRequest(
            pipeline_run_id=PIPELINE_RUN_ID,
            status="failed",
            error_message="Rate limit exceeded",
            record_count=50,
            records_created=50,
        )

        with _patch_engine(engine):
            result = await close_pipeline_run(req)

        assert result.success is True
        assert result.pipeline_run_id == PIPELINE_RUN_ID


# ============================================================================
# hello_store_data (backward compat shim)
# ============================================================================


class TestHelloStoreData:
    """The deprecated shim must still work for IngestWorkflow compatibility."""

    @pytest.mark.asyncio
    async def test_shim_returns_stored(self):
        from unlock_data_access.activities import hello_store_data

        result = await hello_store_data("test data payload")
        assert result == "Stored: test data payload"
