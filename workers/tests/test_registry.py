"""Verify the component registry is complete and consistent."""

from unlock_workers.registry import COMPONENTS


def test_all_components_registered() -> None:
    """Every planned component should have a registry entry."""
    expected = {
        "data-manager",
        "source-access",
        "transform-engine",
        "data-access",
        "config-access",
        "schema-engine",
        "access-engine",
        "llm-gateway",
    }
    assert set(COMPONENTS.keys()) == expected


def test_data_manager_has_workflows_no_activities() -> None:
    """The Data Manager is a workflow runner — it should have no activities."""
    dm = COMPONENTS["data-manager"]
    assert len(dm.workflows) == 4
    assert len(dm.activities) == 0


def test_activity_components_have_no_workflows() -> None:
    """Activity components should not register workflows."""
    for name, config in COMPONENTS.items():
        if name == "data-manager":
            continue
        assert len(config.workflows) == 0, f"{name} should not have workflows"
        assert len(config.activities) >= 1, f"{name} should have at least one activity"


def test_each_component_has_unique_queue() -> None:
    """No two components should share a task queue."""
    queues = [config.task_queue for config in COMPONENTS.values()]
    assert len(queues) == len(set(queues)), "Components share a task queue"
