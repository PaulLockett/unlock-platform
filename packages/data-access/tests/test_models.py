"""Tests for Data Access boundary models.

Validates:
  - All model fields have correct types and defaults
  - Pydantic serialization/deserialization works
  - PlatformResult inheritance chain
  - PersonHistory records have temporal fields
"""

from datetime import UTC, datetime

from unlock_shared.data_models import (
    CatalogContentRequest,
    CatalogContentResult,
    ClosePipelineRunRequest,
    ClosePipelineRunResult,
    CommunicationRecord,
    ContactIdentity,
    ContentRecord,
    EngagementRecord,
    EnrollMemberResult,
    IdentifyContactRequest,
    IdentifyContactResult,
    LogCommunicationResult,
    MembershipRecord,
    OpenPipelineRunRequest,
    OpenPipelineRunResult,
    ParticipationRecord,
    PersonEmail,
    PersonLocation,
    PersonName,
    PersonPhone,
    ProfileContactResult,
    RecordEngagementRequest,
    RecordEngagementResult,
    RegisterParticipationResult,
    SurveyEngagementRequest,
    SurveyEngagementResult,
)
from unlock_shared.models import PlatformResult


class TestPersonHistoryModels:
    """Person history records must carry temporal tracking fields."""

    def test_person_name_defaults(self):
        name = PersonName(display_name="Jane Smith")
        assert name.display_name == "Jane Smith"
        assert name.is_current is True
        assert name.name_type is None
        assert name.observed_at is None

    def test_person_name_full(self):
        name = PersonName(
            first_name="Jane",
            last_name="Smith",
            display_name="Jane Smith",
            name_type="legal",
            source_key="unipile",
            channel_key="linkedin",
            is_current=True,
            observed_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        assert name.first_name == "Jane"
        assert name.source_key == "unipile"

    def test_person_email_required_field(self):
        email = PersonEmail(email="jane@example.com")
        assert email.email == "jane@example.com"
        assert email.is_primary is False
        assert email.is_verified is False

    def test_person_phone_required_field(self):
        phone = PersonPhone(phone="+12055551234")
        assert phone.phone == "+12055551234"
        assert phone.is_primary is False

    def test_person_location_defaults(self):
        loc = PersonLocation(city="Birmingham", state="AL")
        assert loc.city == "Birmingham"
        assert loc.is_current is True
        assert loc.country is None

    def test_serialization_roundtrip(self):
        name = PersonName(
            first_name="Jane",
            last_name="Smith",
            observed_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        data = name.model_dump()
        restored = PersonName.model_validate(data)
        assert restored.first_name == "Jane"
        assert restored.observed_at is not None


class TestContactIdentity:
    def test_minimal(self):
        ci = ContactIdentity(channel_key="linkedin")
        assert ci.channel_key == "linkedin"
        assert ci.platform_user_id is None
        assert ci.is_verified is False

    def test_full(self):
        ci = ContactIdentity(
            channel_key="x",
            platform_user_id="12345",
            username="janesmith",
            profile_url="https://x.com/janesmith",
            display_name="Jane Smith",
            followers_count=1000,
        )
        assert ci.followers_count == 1000


class TestContentRecord:
    def test_minimal(self):
        cr = ContentRecord(channel_key="linkedin", content_type="post")
        assert cr.like_count == 0
        assert cr.tags is None

    def test_full_linkedin_post(self):
        cr = ContentRecord(
            channel_key="linkedin",
            content_type="post",
            source_key="unipile",
            external_id="urn:li:activity:123",
            title=None,
            body="Excited to announce...",
            published_at=datetime(2026, 2, 14, tzinfo=UTC),
            like_count=42,
            comment_count=5,
            share_count=3,
            tags=["announcement"],
        )
        assert cr.body == "Excited to announce..."
        assert cr.like_count == 42


class TestEngagementRecord:
    def test_required_fields(self):
        er = EngagementRecord(
            person_external_id="user123",
            content_external_id="post456",
            channel_key="x",
            engagement_type="like",
            occurred_at=datetime(2026, 2, 14, tzinfo=UTC),
        )
        assert er.engagement_type == "like"
        assert er.utm_source is None


class TestCommunicationRecord:
    def test_email(self):
        cr = CommunicationRecord(
            sender_external_id="user123",
            channel_key="email",
            subject="Welcome to Unlock Alabama",
            body_plain="Hello Jane...",
            sent_at=datetime(2026, 2, 14, tzinfo=UTC),
            recipient_ids=["user456", "user789"],
            cc_ids=["user000"],
        )
        assert len(cr.recipient_ids) == 2
        assert cr.is_automated is False


class TestParticipationRecord:
    def test_event_attendance(self):
        pr = ParticipationRecord(
            person_external_id="user123",
            event_title="Civic Tech Workshop",
            participation_type="attended",
            attended_at=datetime(2026, 2, 14, tzinfo=UTC),
        )
        assert pr.participation_type == "attended"
        assert pr.feedback_score is None


class TestMembershipRecord:
    def test_volunteer(self):
        mr = MembershipRecord(
            person_external_id="user123",
            organization_name="Unlock Alabama",
            organization_type="nonprofit",
            role="volunteer",
            is_active=True,
        )
        assert mr.role == "volunteer"
        assert mr.department is None


class TestResultModels:
    """All result models must extend PlatformResult."""

    def test_identify_contact_result_inherits(self):
        r = IdentifyContactResult(success=True, message="ok", person_id="abc", is_new=True)
        assert isinstance(r, PlatformResult)
        assert r.is_new is True

    def test_catalog_content_result(self):
        r = CatalogContentResult(success=True, message="ok", created=5, updated=2, skipped=1)
        assert r.created == 5

    def test_record_engagement_result(self):
        r = RecordEngagementResult(success=True, message="ok", recorded=10)
        assert r.recorded == 10

    def test_log_communication_result(self):
        r = LogCommunicationResult(success=True, message="ok", logged=3)
        assert r.logged == 3

    def test_register_participation_result(self):
        r = RegisterParticipationResult(success=True, message="ok", registered=2, updated=1)
        assert r.registered == 2

    def test_enroll_member_result(self):
        r = EnrollMemberResult(success=True, message="ok", enrolled=1)
        assert r.enrolled == 1

    def test_profile_contact_result(self):
        r = ProfileContactResult(
            success=True,
            message="ok",
            person_id="abc",
            display_name="Jane",
            tags=["organizer"],
        )
        assert r.display_name == "Jane"
        assert r.names is None

    def test_survey_engagement_result(self):
        r = SurveyEngagementResult(
            success=True, message="ok", records=[{"type": "like"}], total_count=1
        )
        assert r.has_more is False

    def test_open_pipeline_run_result(self):
        r = OpenPipelineRunResult(success=True, message="ok", pipeline_run_id="run-1")
        assert r.pipeline_run_id == "run-1"

    def test_close_pipeline_run_result(self):
        r = ClosePipelineRunResult(
            success=True, message="ok", pipeline_run_id="run-1", duration_seconds=45.2
        )
        assert r.duration_seconds == 45.2

    def test_failure_result(self):
        r = IdentifyContactResult(success=False, message="DB connection failed")
        assert r.success is False
        assert r.person_id == ""


class TestRequestModels:
    """Request models carry the right defaults and required fields."""

    def test_identify_contact_request(self):
        req = IdentifyContactRequest(
            source_key="unipile",
            external_id="user123",
            channel_key="linkedin",
            names=[PersonName(display_name="Jane Smith")],
            emails=[PersonEmail(email="jane@example.com", is_primary=True)],
        )
        assert req.source_key == "unipile"
        assert len(req.names) == 1
        assert len(req.emails) == 1

    def test_catalog_content_request(self):
        req = CatalogContentRequest(
            source_key="x",
            records=[ContentRecord(channel_key="x", content_type="tweet")],
        )
        assert len(req.records) == 1

    def test_record_engagement_request(self):
        req = RecordEngagementRequest(
            source_key="posthog",
            records=[
                EngagementRecord(
                    person_external_id="u1",
                    content_external_id="p1",
                    channel_key="website",
                    engagement_type="view",
                    occurred_at=datetime(2026, 2, 14, tzinfo=UTC),
                )
            ],
        )
        assert req.records[0].engagement_type == "view"

    def test_survey_engagement_request_defaults(self):
        req = SurveyEngagementRequest()
        assert req.limit == 100
        assert req.offset == 0
        assert req.channel_key is None

    def test_open_pipeline_run_request(self):
        req = OpenPipelineRunRequest(source_key="unipile", resource_type="posts")
        assert req.workflow_run_id is None

    def test_close_pipeline_run_request(self):
        req = ClosePipelineRunRequest(
            pipeline_run_id="run-1",
            status="completed",
            record_count=100,
            records_created=80,
            records_updated=15,
            records_skipped=5,
        )
        assert req.record_count == 100
