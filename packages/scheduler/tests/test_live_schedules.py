"""Live smoke tests against Temporal Cloud schedules.

These run in CI where Temporal Cloud credentials are available (GitHub secrets).
They verify that mocked behavior in test_activities.py matches real Temporal
Schedule API behavior — catching SDK version mismatches, API changes, and
authentication issues that mocks can't detect.

Skipped automatically when TEMPORAL_API_KEY is not set, so they never run
locally unless you have Temporal Cloud credentials configured.

The test schedule targets a no-op workflow name ("NoOpScheduleTest") — it won't
actually execute since no worker listens for it. We're testing schedule CRUD,
not workflow execution.
"""

from __future__ import annotations

import os
import uuid

import pytest

SKIP = not os.environ.get("TEMPORAL_API_KEY")
REASON = "TEMPORAL_API_KEY not set — requires Temporal Cloud credentials"

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(SKIP, reason=REASON),
]

# Unique prefix per test run so parallel/repeated runs don't collide.
RUN_ID = uuid.uuid4().hex[:8]


class TestLiveScheduleLifecycle:
    """Full lifecycle: register → describe → pause → resume → list → cancel."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self):
        from unlock_scheduler.activities import (
            cancel_harvest,
            describe_harvest,
            list_harvests,
            pause_harvest,
            register_harvest,
            resume_harvest,
        )
        from unlock_shared.scheduler_models import (
            CancelHarvestRequest,
            DescribeHarvestRequest,
            ListHarvestsRequest,
            PauseHarvestRequest,
            RegisterHarvestRequest,
            ResumeHarvestRequest,
        )

        source = f"smoke-test-{RUN_ID}"
        schedule_id = f"harvest-smoke-test-{RUN_ID.lower()}"

        try:
            # 1. Register a schedule
            reg = await register_harvest(RegisterHarvestRequest(
                source_name=source,
                cron_expression="0 0 1 1 *",  # yearly — won't actually fire
                note=f"Smoke test run {RUN_ID}",
            ))
            assert reg.success, f"register_harvest failed: {reg.message}"
            assert reg.schedule_id == schedule_id

            # 2. Describe — should exist, not paused
            desc = await describe_harvest(DescribeHarvestRequest(source_name=source))
            assert desc.success, f"describe_harvest failed: {desc.message}"
            assert desc.schedule_id == schedule_id
            assert desc.is_paused is False
            assert desc.cron_expression == "0 0 1 1 *"
            assert desc.next_run_time != ""

            # 3. Pause
            paused = await pause_harvest(PauseHarvestRequest(
                source_name=source,
                note="Smoke test pause",
            ))
            assert paused.success, f"pause_harvest failed: {paused.message}"

            # 4. Describe — should be paused
            desc2 = await describe_harvest(DescribeHarvestRequest(source_name=source))
            assert desc2.success
            assert desc2.is_paused is True

            # 5. Resume
            resumed = await resume_harvest(ResumeHarvestRequest(
                source_name=source,
                note="Smoke test resume",
            ))
            assert resumed.success, f"resume_harvest failed: {resumed.message}"

            # 6. Describe — should be unpaused
            desc3 = await describe_harvest(DescribeHarvestRequest(source_name=source))
            assert desc3.success
            assert desc3.is_paused is False

            # 7. List — should include our schedule
            listed = await list_harvests(ListHarvestsRequest())
            assert listed.success, f"list_harvests failed: {listed.message}"
            found = [s for s in listed.schedules if s["schedule_id"] == schedule_id]
            assert len(found) == 1, f"Schedule {schedule_id} not found in list"

            # 8. Register again — idempotent, should succeed
            reg2 = await register_harvest(RegisterHarvestRequest(
                source_name=source,
                cron_expression="0 0 1 1 *",
                note="Idempotent re-register",
            ))
            assert reg2.success, f"Idempotent register failed: {reg2.message}"

            # 9. Cancel
            cancelled = await cancel_harvest(CancelHarvestRequest(source_name=source))
            assert cancelled.success, f"cancel_harvest failed: {cancelled.message}"

            # 10. Describe after cancel — should fail (schedule gone)
            gone = await describe_harvest(DescribeHarvestRequest(source_name=source))
            assert gone.success is False

        finally:
            # Cleanup: always try to delete the schedule even if test fails
            try:
                from unlock_scheduler.activities import cancel_harvest as _cancel
                from unlock_shared.scheduler_models import CancelHarvestRequest as _Req

                await _cancel(_Req(source_name=source))
            except Exception:
                pass
