"""Tests for Source Access Pydantic models.

Verifies:
  - Models parse from JSON fixtures correctly
  - Default values are sensible
  - Serialization round-trips work
  - Shared boundary models validate correctly
"""

from datetime import datetime

import pytest
from unlock_shared.source_models import (
    ConnectionResult,
    FetchRequest,
    FetchResult,
    SourceConfig,
    SourceSchema,
)
from unlock_source_access.models.posthog import PostHogEvent, PostHogPerson
from unlock_source_access.models.rb2b import RB2BCompany, RB2BPerson
from unlock_source_access.models.unipile import UnipileEmail, UnipilePost
from unlock_source_access.models.x import XTweet, XTweetMetrics, XUser


class TestUnipileModels:
    def test_post_from_dict(self):
        post = UnipilePost(
            id="post-001",
            provider="LINKEDIN",
            text="Test post",
            likes=42,
            comments=8,
            impressions=2500,
        )
        assert post.likes == 42
        assert post.provider == "LINKEDIN"

    def test_post_defaults(self):
        post = UnipilePost(id="min")
        assert post.likes == 0
        assert post.shares == 0
        assert post.attachments == []

    def test_email_from_dict(self):
        email = UnipileEmail(
            id="email-001",
            subject="Test email",
            from_address="test@example.com",
            to_addresses=["team@unlock.org"],
        )
        assert email.subject == "Test email"
        assert len(email.to_addresses) == 1

    def test_post_serialization_roundtrip(self):
        original = UnipilePost(
            id="rt-001",
            provider="INSTAGRAM",
            likes=100,
            created_at=datetime(2024, 12, 1, 10, 0),
        )
        data = original.model_dump()
        restored = UnipilePost(**data)
        assert restored == original


class TestXModels:
    def test_tweet_with_metrics(self):
        tweet = XTweet(
            id="123",
            text="Hello X",
            public_metrics=XTweetMetrics(like_count=45, retweet_count=12),
        )
        assert tweet.public_metrics.like_count == 45

    def test_tweet_defaults(self):
        tweet = XTweet(id="min")
        assert tweet.public_metrics.like_count == 0
        assert tweet.edit_history_tweet_ids == []

    def test_user_model(self):
        user = XUser(
            id="999",
            username="unlockalabama",
            name="Unlock Alabama",
            verified=False,
        )
        assert user.username == "unlockalabama"

    def test_tweet_serialization_roundtrip(self):
        original = XTweet(
            id="rt-001",
            text="Roundtrip test",
            created_at=datetime(2024, 12, 1, 15, 30),
            public_metrics=XTweetMetrics(impression_count=3200),
        )
        data = original.model_dump()
        restored = XTweet(**data)
        assert restored == original


class TestPostHogModels:
    def test_event_with_properties(self):
        event = PostHogEvent(
            id="evt-001",
            event="$pageview",
            distinct_id="user-abc",
            properties={"$current_url": "https://example.com"},
        )
        assert event.event == "$pageview"
        assert "$current_url" in event.properties

    def test_person_model(self):
        person = PostHogPerson(
            id="person-001",
            distinct_ids=["user-abc", "anon-xyz"],
            is_identified=True,
        )
        assert len(person.distinct_ids) == 2
        assert person.is_identified

    def test_event_defaults(self):
        event = PostHogEvent()
        assert event.properties == {}
        assert event.elements == []


class TestRB2BModels:
    def test_person_with_company(self):
        person = RB2BPerson(
            id="v-001",
            email="test@corp.com",
            first_name="John",
            company=RB2BCompany(
                name="TechCorp",
                industry="Technology",
                employee_count=250,
            ),
        )
        assert person.company.name == "TechCorp"
        assert person.company.employee_count == 250

    def test_person_defaults(self):
        person = RB2BPerson()
        assert person.email == ""
        assert person.company.name == ""
        assert person.page_views == []
        assert person.visit_count == 0


class TestBoundaryModels:
    """Tests for the shared boundary models used at the Temporal activity boundary."""

    def test_source_config_minimal(self):
        config = SourceConfig(source_id="test", source_type="unipile")
        assert config.rate_limit_per_second == 5.0
        assert config.auth_env_var is None

    def test_fetch_request_defaults(self):
        req = FetchRequest(source_id="test", source_type="x")
        assert req.resource_type == "posts"
        assert req.max_pages == 100
        assert req.since is None

    def test_connection_result_inherits_platform_result(self):
        result = ConnectionResult(
            success=True,
            message="Connected",
            source_id="test",
            source_type="unipile",
        )
        assert result.success
        assert result.source_id == "test"

    def test_fetch_result_with_records(self):
        result = FetchResult(
            success=True,
            message="Fetched 2 records",
            source_id="test",
            records=[{"id": "1"}, {"id": "2"}],
            record_count=2,
        )
        assert len(result.records) == 2
        assert result.record_count == 2

    def test_source_schema(self):
        schema = SourceSchema(
            success=True,
            message="Found 3 fields",
            source_id="test",
            fields={"id": "str", "likes": "int", "created_at": "str"},
        )
        assert len(schema.fields) == 3

    @pytest.mark.parametrize(
        "source_type",
        ["unipile", "x", "posthog", "rb2b"],
    )
    def test_source_config_all_types(self, source_type: str):
        """All four source types can create a valid SourceConfig."""
        config = SourceConfig(
            source_id=f"test-{source_type}",
            source_type=source_type,
            auth_env_var=f"{source_type.upper()}_KEY",
        )
        assert config.source_type == source_type
