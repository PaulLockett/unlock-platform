"""Tests for Scheduler activities — all 6 business verb activities.

Each test patches unlock_shared.temporal_client.connect to return a MockClient
that records calls and returns canned results. Tests are written BEFORE
activities (test-first).

Pattern: unittest.mock.patch("unlock_scheduler.activities.connect")
returns an async function yielding MockClient with create_schedule(),
get_schedule_handle(), and list_schedules().
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from unlock_shared.scheduler_models import (
    CancelHarvestRequest,
    DescribeHarvestRequest,
    ListHarvestsRequest,
    PauseHarvestRequest,
    RegisterHarvestRequest,
    ResumeHarvestRequest,
)

# ============================================================================
# Mock Temporal objects
# ============================================================================


class MockScheduleDescription:
    """Mimics temporalio.client.ScheduleDescription enough for describe_harvest."""

    def __init__(
        self,
        *,
        is_paused: bool = False,
        cron: str = "0 */6 * * *",
        next_run: datetime | None = None,
        recent_actions: list[dict[str, Any]] | None = None,
    ) -> None:
        self.schedule = MockScheduleState(is_paused=is_paused, cron=cron)
        self.info = MockScheduleInfo(
            next_run=next_run or datetime(2026, 3, 1, 12, 0, tzinfo=UTC),
            recent_actions=recent_actions or [],
        )


class MockScheduleState:
    def __init__(self, *, is_paused: bool, cron: str) -> None:
        self.state = MockSchedulePauseState(paused=is_paused)
        self.spec = MockScheduleSpec(cron=cron)


class MockSchedulePauseState:
    def __init__(self, *, paused: bool) -> None:
        self.paused = paused


class MockScheduleSpec:
    def __init__(self, *, cron: str) -> None:
        self.cron_expressions = [cron] if cron else []


class MockScheduleInfo:
    def __init__(
        self,
        *,
        next_run: datetime,
        recent_actions: list[dict[str, Any]],
    ) -> None:
        self.next_action_times = [next_run]
        self.recent_actions = [
            MockScheduleActionResult(**a) for a in recent_actions
        ]


class MockScheduleActionResult:
    """Mimics temporalio.client.ScheduleActionResult.

    Real structure: scheduled_at, started_at, action (ScheduleActionExecution).
    action is a ScheduleActionExecutionStartWorkflow with workflow_id and
    first_execution_run_id.
    """

    def __init__(
        self,
        *,
        workflow_id: str = "wf-1",
        start_time: str = "",
        status: str = "completed",
    ) -> None:
        self.action = MockScheduleActionExecutionStartWorkflow(
            workflow_id=workflow_id,
        )
        self.started_at = (
            datetime.fromisoformat(start_time)
            if start_time
            else datetime(2026, 2, 20, tzinfo=UTC)
        )


class MockScheduleActionExecutionStartWorkflow:
    """Mimics temporalio.client.ScheduleActionExecutionStartWorkflow."""

    def __init__(self, *, workflow_id: str) -> None:
        self.workflow_id = workflow_id
        self.first_execution_run_id = "run-1"


class MockScheduleHandle:
    """Mimics temporalio.client.ScheduleHandle."""

    def __init__(self, description: MockScheduleDescription | None = None) -> None:
        self._description = description or MockScheduleDescription()
        self.pause = AsyncMock()
        self.unpause = AsyncMock()
        self.delete = AsyncMock()

    async def describe(self) -> MockScheduleDescription:
        return self._description


class MockScheduleListState:
    """Mimics temporalio.client.ScheduleListState."""

    def __init__(self, *, paused: bool = False, note: str | None = None) -> None:
        self.paused = paused
        self.note = note


class MockScheduleListSchedule:
    """Mimics temporalio.client.ScheduleListSchedule."""

    def __init__(
        self,
        *,
        state: MockScheduleListState | None = None,
        spec: MockScheduleSpec | None = None,
    ) -> None:
        self.state = state or MockScheduleListState()
        self.spec = spec or MockScheduleSpec(cron="")


class MockScheduleListEntry:
    """Mimics temporalio.client.ScheduleListDescription.

    The real ScheduleListDescription.memo() is a method returning Mapping[str, Any],
    not a plain dict attribute. Our mock mirrors this interface.
    """

    def __init__(
        self,
        *,
        schedule_id: str,
        memo: dict[str, str] | None = None,
        is_paused: bool = False,
        note: str | None = None,
        cron: str = "",
    ) -> None:
        self.id = schedule_id
        self._memo = memo or {}
        self.schedule = MockScheduleListSchedule(
            state=MockScheduleListState(paused=is_paused, note=note),
            spec=MockScheduleSpec(cron=cron) if cron else MockScheduleSpec(cron=""),
        )

    async def memo(self) -> dict[str, str]:
        return self._memo


class MockClient:
    """Mimics temporalio.client.Client for schedule operations."""

    def __init__(
        self,
        *,
        handles: dict[str, MockScheduleHandle] | None = None,
        list_entries: list[MockScheduleListEntry] | None = None,
    ) -> None:
        self._handles = handles or {}
        self._list_entries = list_entries or []
        self.create_schedule = AsyncMock()

    def get_schedule_handle(self, schedule_id: str) -> MockScheduleHandle:
        if schedule_id not in self._handles:
            # Create a default handle that will raise on describe
            handle = MockScheduleHandle()
            handle.describe = AsyncMock(
                side_effect=Exception(f"Schedule {schedule_id} not found")
            )
            handle.pause = AsyncMock(
                side_effect=Exception(f"Schedule {schedule_id} not found")
            )
            handle.unpause = AsyncMock(
                side_effect=Exception(f"Schedule {schedule_id} not found")
            )
            handle.delete = AsyncMock(
                side_effect=Exception(f"Schedule {schedule_id} not found")
            )
            return handle
        return self._handles[schedule_id]

    async def list_schedules(self) -> MockScheduleListIter:
        return MockScheduleListIter(self._list_entries)


class MockScheduleListIter:
    """Async iterator over schedule list entries."""

    def __init__(self, entries: list[MockScheduleListEntry]) -> None:
        self._entries = entries
        self._index = 0

    def __aiter__(self) -> MockScheduleListIter:
        return self

    async def __anext__(self) -> MockScheduleListEntry:
        if self._index >= len(self._entries):
            raise StopAsyncIteration
        entry = self._entries[self._index]
        self._index += 1
        return entry


# ============================================================================
# Helper: _schedule_id derivation
# ============================================================================


class TestScheduleId:
    def test_deterministic_id(self):
        from unlock_scheduler.activities import _schedule_id

        assert _schedule_id("linkedin") == "harvest-linkedin"
        assert _schedule_id("Alabama Census") == "harvest-alabama-census"

    def test_normalizes_whitespace_and_case(self):
        from unlock_scheduler.activities import _schedule_id

        assert _schedule_id("  My Source  ") == "harvest-my-source"


# ============================================================================
# register_harvest
# ============================================================================


class TestRegisterHarvest:
    @pytest.mark.asyncio
    async def test_register_success(self):
        from unlock_scheduler.activities import register_harvest

        client = MockClient()
        mock_connect = AsyncMock(return_value=client)

        req = RegisterHarvestRequest(
            source_name="linkedin",
            cron_expression="0 */6 * * *",
            note="Initial setup",
        )

        with patch("unlock_scheduler.activities.connect", mock_connect):
            result = await register_harvest(req)

        assert result.success is True
        assert result.schedule_id == "harvest-linkedin"
        client.create_schedule.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_register_idempotent_already_exists(self):
        """Re-registering an existing schedule succeeds (idempotent)."""
        from temporalio.service import RPCError, RPCStatusCode
        from unlock_scheduler.activities import register_harvest

        client = MockClient()
        client.create_schedule = AsyncMock(
            side_effect=RPCError(
                message="schedule already running",
                status=RPCStatusCode.ALREADY_EXISTS,
                raw_grpc_status=6,
            )
        )
        mock_connect = AsyncMock(return_value=client)

        req = RegisterHarvestRequest(
            source_name="linkedin",
            cron_expression="0 */6 * * *",
        )

        with patch("unlock_scheduler.activities.connect", mock_connect):
            result = await register_harvest(req)

        assert result.success is True
        assert result.schedule_id == "harvest-linkedin"
        assert "already exists" in result.message.lower()

    @pytest.mark.asyncio
    async def test_register_unexpected_error(self):
        from unlock_scheduler.activities import register_harvest

        client = MockClient()
        client.create_schedule = AsyncMock(side_effect=RuntimeError("network failure"))
        mock_connect = AsyncMock(return_value=client)

        req = RegisterHarvestRequest(
            source_name="linkedin",
            cron_expression="0 */6 * * *",
        )

        with patch("unlock_scheduler.activities.connect", mock_connect):
            result = await register_harvest(req)

        assert result.success is False
        assert "network failure" in result.message


# ============================================================================
# pause_harvest
# ============================================================================


class TestPauseHarvest:
    @pytest.mark.asyncio
    async def test_pause_success(self):
        from unlock_scheduler.activities import pause_harvest

        handle = MockScheduleHandle()
        client = MockClient(handles={"harvest-linkedin": handle})
        mock_connect = AsyncMock(return_value=client)

        req = PauseHarvestRequest(source_name="linkedin", note="Maintenance window")

        with patch("unlock_scheduler.activities.connect", mock_connect):
            result = await pause_harvest(req)

        assert result.success is True
        assert result.schedule_id == "harvest-linkedin"
        handle.pause.assert_awaited_once_with(note="Maintenance window")

    @pytest.mark.asyncio
    async def test_pause_not_found(self):
        from unlock_scheduler.activities import pause_harvest

        client = MockClient()  # no handles registered
        mock_connect = AsyncMock(return_value=client)

        req = PauseHarvestRequest(source_name="nonexistent")

        with patch("unlock_scheduler.activities.connect", mock_connect):
            result = await pause_harvest(req)

        assert result.success is False


# ============================================================================
# resume_harvest
# ============================================================================


class TestResumeHarvest:
    @pytest.mark.asyncio
    async def test_resume_success(self):
        from unlock_scheduler.activities import resume_harvest

        handle = MockScheduleHandle()
        client = MockClient(handles={"harvest-linkedin": handle})
        mock_connect = AsyncMock(return_value=client)

        req = ResumeHarvestRequest(source_name="linkedin", note="Back online")

        with patch("unlock_scheduler.activities.connect", mock_connect):
            result = await resume_harvest(req)

        assert result.success is True
        assert result.schedule_id == "harvest-linkedin"
        handle.unpause.assert_awaited_once_with(note="Back online")

    @pytest.mark.asyncio
    async def test_resume_not_found(self):
        from unlock_scheduler.activities import resume_harvest

        client = MockClient()
        mock_connect = AsyncMock(return_value=client)

        req = ResumeHarvestRequest(source_name="nonexistent")

        with patch("unlock_scheduler.activities.connect", mock_connect):
            result = await resume_harvest(req)

        assert result.success is False


# ============================================================================
# cancel_harvest
# ============================================================================


class TestCancelHarvest:
    @pytest.mark.asyncio
    async def test_cancel_success(self):
        from unlock_scheduler.activities import cancel_harvest

        handle = MockScheduleHandle()
        client = MockClient(handles={"harvest-linkedin": handle})
        mock_connect = AsyncMock(return_value=client)

        req = CancelHarvestRequest(source_name="linkedin")

        with patch("unlock_scheduler.activities.connect", mock_connect):
            result = await cancel_harvest(req)

        assert result.success is True
        assert result.schedule_id == "harvest-linkedin"
        handle.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cancel_not_found(self):
        from unlock_scheduler.activities import cancel_harvest

        client = MockClient()
        mock_connect = AsyncMock(return_value=client)

        req = CancelHarvestRequest(source_name="nonexistent")

        with patch("unlock_scheduler.activities.connect", mock_connect):
            result = await cancel_harvest(req)

        assert result.success is False


# ============================================================================
# describe_harvest
# ============================================================================


class TestDescribeHarvest:
    @pytest.mark.asyncio
    async def test_describe_success(self):
        from unlock_scheduler.activities import describe_harvest

        desc = MockScheduleDescription(
            is_paused=False,
            cron="0 */6 * * *",
            next_run=datetime(2026, 3, 1, 12, 0, tzinfo=UTC),
            recent_actions=[
                {
                    "workflow_id": "wf-abc",
                    "start_time": "2026-02-20T06:00:00+00:00",
                    "status": "completed",
                },
            ],
        )
        handle = MockScheduleHandle(description=desc)
        client = MockClient(handles={"harvest-linkedin": handle})
        mock_connect = AsyncMock(return_value=client)

        req = DescribeHarvestRequest(source_name="linkedin")

        with patch("unlock_scheduler.activities.connect", mock_connect):
            result = await describe_harvest(req)

        assert result.success is True
        assert result.schedule_id == "harvest-linkedin"
        assert result.is_paused is False
        assert result.cron_expression == "0 */6 * * *"
        assert result.next_run_time != ""
        assert len(result.recent_runs) == 1
        assert result.recent_runs[0]["workflow_id"] == "wf-abc"

    @pytest.mark.asyncio
    async def test_describe_paused(self):
        from unlock_scheduler.activities import describe_harvest

        desc = MockScheduleDescription(is_paused=True, cron="0 0 * * *")
        handle = MockScheduleHandle(description=desc)
        client = MockClient(handles={"harvest-linkedin": handle})
        mock_connect = AsyncMock(return_value=client)

        req = DescribeHarvestRequest(source_name="linkedin")

        with patch("unlock_scheduler.activities.connect", mock_connect):
            result = await describe_harvest(req)

        assert result.success is True
        assert result.is_paused is True

    @pytest.mark.asyncio
    async def test_describe_not_found(self):
        from unlock_scheduler.activities import describe_harvest

        client = MockClient()
        mock_connect = AsyncMock(return_value=client)

        req = DescribeHarvestRequest(source_name="nonexistent")

        with patch("unlock_scheduler.activities.connect", mock_connect):
            result = await describe_harvest(req)

        assert result.success is False


# ============================================================================
# list_harvests
# ============================================================================


class TestListHarvests:
    @pytest.mark.asyncio
    async def test_list_success(self):
        from unlock_scheduler.activities import list_harvests

        entries = [
            MockScheduleListEntry(
                schedule_id="harvest-linkedin",
                memo={"source_name": "linkedin"},
            ),
            MockScheduleListEntry(
                schedule_id="harvest-census",
                memo={"source_name": "census"},
            ),
        ]
        client = MockClient(list_entries=entries)
        mock_connect = AsyncMock(return_value=client)

        req = ListHarvestsRequest()

        with patch("unlock_scheduler.activities.connect", mock_connect):
            result = await list_harvests(req)

        assert result.success is True
        assert len(result.schedules) == 2
        ids = [s["schedule_id"] for s in result.schedules]
        assert "harvest-linkedin" in ids
        assert "harvest-census" in ids

    @pytest.mark.asyncio
    async def test_list_empty(self):
        from unlock_scheduler.activities import list_harvests

        client = MockClient(list_entries=[])
        mock_connect = AsyncMock(return_value=client)

        req = ListHarvestsRequest()

        with patch("unlock_scheduler.activities.connect", mock_connect):
            result = await list_harvests(req)

        assert result.success is True
        assert len(result.schedules) == 0

    @pytest.mark.asyncio
    async def test_list_error(self):
        from unlock_scheduler.activities import list_harvests

        client = MockClient()
        client.list_schedules = AsyncMock(side_effect=RuntimeError("connection lost"))
        mock_connect = AsyncMock(return_value=client)

        req = ListHarvestsRequest()

        with patch("unlock_scheduler.activities.connect", mock_connect):
            result = await list_harvests(req)

        assert result.success is False
        assert "connection lost" in result.message
