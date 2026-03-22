"""Component registry: maps component names to their workflows and activities.

This is the central lookup table that the runner uses to determine what to
register on a worker based on the CLI argument. Each component entry specifies:

- task_queue: Which Temporal task queue this worker polls
- workflows: Workflow classes to register (only the Data Manager has these)
- activities: Activity functions to register

The key insight: every Railway service uses the same Docker image. The only
difference is the CMD argument (e.g., "source-access"), which selects which
entry from this registry to use. This keeps the build simple (one Dockerfile)
while maintaining complete runtime isolation between components.
"""

from dataclasses import dataclass, field
from typing import Any

from unlock_access_engine.activities import (
    compute_effective_permissions,
    evaluate_access_decision,
    hello_check_access,
)
from unlock_access_engine.workflows import (
    CheckAccessWorkflow,
    EvaluatePermissionsWorkflow,
)
from unlock_config_access.activities import (
    activate_view,
    archive_schema,
    clone_view,
    define_pipeline,
    grant_access,
    hello_load_config,
    publish_schema,
    retrieve_view,
    revoke_access,
    survey_configs,
)
from unlock_data_access.activities import (
    catalog_content,
    close_pipeline_run,
    enroll_member,
    hello_store_data,
    identify_contact,
    log_communication,
    open_pipeline_run,
    profile_contact,
    record_engagement,
    register_participation,
    survey_engagement,
)
from unlock_data_manager.workflows.configure import ConfigureWorkflow
from unlock_data_manager.workflows.ingest import IngestWorkflow
from unlock_data_manager.workflows.manage_source import ManageSourceWorkflow
from unlock_data_manager.workflows.query import QueryWorkflow
from unlock_data_manager.workflows.retrieve_view import RetrieveViewWorkflow
from unlock_data_manager.workflows.revoke_access import RevokeAccessWorkflow
from unlock_data_manager.workflows.share import ShareWorkflow
from unlock_data_manager.workflows.survey_configs import SurveyConfigsWorkflow
from unlock_llm_gateway.activities import hello_llm_assess
from unlock_scheduler.activities import (
    cancel_harvest,
    describe_harvest,
    list_harvests,
    pause_harvest,
    register_harvest,
    resume_harvest,
)
from unlock_schema_engine.activities import (
    generate_field_mappings,
    hello_validate_schema,
    validate_and_detect_drift,
)
from unlock_schema_engine.workflows import (
    GenerateMappingsWorkflow,
    ValidateSchemaWorkflow,
)
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
from unlock_source_access.activities import (
    connect_source,
    discover_schema,
    fetch_source_data,
    get_source_schema,
    harvest_records,
    identify_source,
    probe_source,
    register_source,
    test_connection,
    verify_source,
)
from unlock_transform_engine.activities import (
    apply_transform_rules,
    hello_transform,
    validate_pipeline,
)
from unlock_transform_engine.workflows import TransformWorkflow


@dataclass
class ComponentConfig:
    """Configuration for a single component's worker."""

    task_queue: str
    workflows: list[Any] = field(default_factory=list)
    activities: list[Any] = field(default_factory=list)


COMPONENTS: dict[str, ComponentConfig] = {
    "data-manager": ComponentConfig(
        task_queue=DATA_MANAGER_QUEUE,
        workflows=[
            IngestWorkflow,
            QueryWorkflow,
            ConfigureWorkflow,
            ShareWorkflow,
            ManageSourceWorkflow,
            SurveyConfigsWorkflow,
            RetrieveViewWorkflow,
            RevokeAccessWorkflow,
        ],
    ),
    "source-access": ComponentConfig(
        task_queue=SOURCE_ACCESS_QUEUE,
        activities=[
            verify_source,
            harvest_records,
            probe_source,
            discover_schema,
            identify_source,
            register_source,
            # Deprecated aliases — remove when callers migrate
            connect_source,
            fetch_source_data,
            test_connection,
            get_source_schema,
        ],
    ),
    "transform-engine": ComponentConfig(
        task_queue=TRANSFORM_ENGINE_QUEUE,
        workflows=[TransformWorkflow],
        activities=[hello_transform, apply_transform_rules, validate_pipeline],
    ),
    "data-access": ComponentConfig(
        task_queue=DATA_ACCESS_QUEUE,
        activities=[
            hello_store_data,
            identify_contact,
            catalog_content,
            record_engagement,
            log_communication,
            register_participation,
            enroll_member,
            profile_contact,
            survey_engagement,
            open_pipeline_run,
            close_pipeline_run,
        ],
    ),
    "config-access": ComponentConfig(
        task_queue=CONFIG_ACCESS_QUEUE,
        activities=[
            hello_load_config,
            publish_schema,
            define_pipeline,
            activate_view,
            retrieve_view,
            grant_access,
            revoke_access,
            clone_view,
            archive_schema,
            survey_configs,
        ],
    ),
    "schema-engine": ComponentConfig(
        task_queue=SCHEMA_ENGINE_QUEUE,
        workflows=[GenerateMappingsWorkflow, ValidateSchemaWorkflow],
        activities=[
            hello_validate_schema,
            generate_field_mappings,
            validate_and_detect_drift,
        ],
    ),
    "access-engine": ComponentConfig(
        task_queue=ACCESS_ENGINE_QUEUE,
        workflows=[CheckAccessWorkflow, EvaluatePermissionsWorkflow],
        activities=[
            hello_check_access,
            evaluate_access_decision,
            compute_effective_permissions,
        ],
    ),
    "llm-gateway": ComponentConfig(
        task_queue=LLM_GATEWAY_QUEUE,
        activities=[hello_llm_assess],
    ),
    "scheduler": ComponentConfig(
        task_queue=SCHEDULER_QUEUE,
        activities=[
            register_harvest,
            pause_harvest,
            resume_harvest,
            cancel_harvest,
            describe_harvest,
            list_harvests,
        ],
    ),
}
