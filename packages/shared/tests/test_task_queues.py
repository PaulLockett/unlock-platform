"""Verify task queue constants are consistent and unique."""

from unlock_shared.task_queues import (
    ACCESS_ENGINE_QUEUE,
    CONFIG_ACCESS_QUEUE,
    DATA_ACCESS_QUEUE,
    DATA_MANAGER_QUEUE,
    LLM_GATEWAY_QUEUE,
    SCHEDULER_QUEUE,
    SCHEMA_ENGINE_QUEUE,
    SOURCE_ACCESS_QUEUE,
    TRANSFORM_ENGINE_QUEUE,
)


def test_all_queues_are_unique() -> None:
    """No two components should share a queue — that would defeat isolation."""
    queues = [
        DATA_MANAGER_QUEUE,
        TRANSFORM_ENGINE_QUEUE,
        SCHEMA_ENGINE_QUEUE,
        ACCESS_ENGINE_QUEUE,
        SOURCE_ACCESS_QUEUE,
        DATA_ACCESS_QUEUE,
        CONFIG_ACCESS_QUEUE,
        LLM_GATEWAY_QUEUE,
        SCHEDULER_QUEUE,
    ]
    assert len(queues) == len(set(queues)), "Duplicate task queue names found"


def test_queue_naming_convention() -> None:
    """All queues should follow the pattern: <component>-queue."""
    queues = [
        DATA_MANAGER_QUEUE,
        TRANSFORM_ENGINE_QUEUE,
        SCHEMA_ENGINE_QUEUE,
        ACCESS_ENGINE_QUEUE,
        SOURCE_ACCESS_QUEUE,
        DATA_ACCESS_QUEUE,
        CONFIG_ACCESS_QUEUE,
        LLM_GATEWAY_QUEUE,
        SCHEDULER_QUEUE,
    ]
    for queue in queues:
        assert queue.endswith("-queue"), f"Queue '{queue}' doesn't end with '-queue'"
