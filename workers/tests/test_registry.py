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
        "scheduler",
    }
    assert set(COMPONENTS.keys()) == expected


def test_data_manager_has_workflows_no_activities() -> None:
    """The Data Manager is a workflow runner — it should have no activities."""
    dm = COMPONENTS["data-manager"]
    assert len(dm.workflows) == 4
    assert len(dm.activities) == 0


def test_non_manager_components_have_activities() -> None:
    """Non-manager components should register at least one activity.

    Engines may also register workflows (child workflows dispatched by
    the Manager), but they must have activities too.
    """
    # Components that are stubs — no activities yet
    stub_components = {"scheduler"}
    # Engines register both workflows and activities
    engine_components = {"transform-engine", "schema-engine", "access-engine"}
    for name, config in COMPONENTS.items():
        if name == "data-manager":
            continue
        if name in engine_components:
            assert len(config.workflows) >= 1, (
                f"{name} should have workflows"
            )
        if name not in stub_components:
            assert len(config.activities) >= 1, (
                f"{name} should have at least one activity"
            )


def test_source_access_has_business_verb_activities() -> None:
    """Source Access registers business verbs + deprecated CRUD aliases."""
    sa = COMPONENTS["source-access"]
    activity_names = {a.__name__ for a in sa.activities}
    # New business verb names
    assert "verify_source" in activity_names
    assert "harvest_records" in activity_names
    assert "probe_source" in activity_names
    assert "discover_schema" in activity_names
    # Deprecated aliases kept for backward compat
    assert "connect_source" in activity_names
    assert "fetch_source_data" in activity_names
    assert "test_connection" in activity_names
    assert "get_source_schema" in activity_names


def test_each_component_has_unique_queue() -> None:
    """No two components should share a task queue."""
    queues = [config.task_queue for config in COMPONENTS.values()]
    assert len(queues) == len(set(queues)), "Components share a task queue"
