"""ConfigureWorkflow: polymorphic dispatch to Config Access.

Routes configuration requests to the appropriate Config Access activity based
on config_type:
  - "schema"   → publish_schema
  - "pipeline" → define_pipeline
  - "view"     → activate_view

The Manager converts list[dict] fields to typed Pydantic models (FieldMapping,
TransformRule, FunnelStage) before passing to activities — Clients send simple
dicts, but Config Access receives validated domain objects.
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from unlock_config_access.activities import (
        activate_view,
        define_pipeline,
        publish_schema,
    )
    from unlock_shared.config_models import (
        ActivateViewRequest,
        DefinePipelineRequest,
        FieldMapping,
        FunnelStage,
        PublishSchemaRequest,
        TransformRule,
    )
    from unlock_shared.manager_models import ConfigureRequest, ConfigureResult
    from unlock_shared.task_queues import CONFIG_ACCESS_QUEUE


@workflow.defn
class ConfigureWorkflow:
    """Routes configuration requests to the matching Config Access activity."""

    @workflow.run
    async def run(self, request: ConfigureRequest) -> ConfigureResult:
        if request.config_type == "schema":
            return await self._configure_schema(request)
        elif request.config_type == "pipeline":
            return await self._configure_pipeline(request)
        elif request.config_type == "view":
            return await self._configure_view(request)
        else:
            return ConfigureResult(
                success=False,
                message=(
                    f"Unknown config_type: '{request.config_type}'. "
                    "Expected 'schema', 'pipeline', or 'view'."
                ),
            )

    async def _configure_schema(self, request: ConfigureRequest) -> ConfigureResult:
        """Publish a schema definition to Config Access."""
        field_mappings = [FieldMapping(**f) for f in request.fields]
        stages = [FunnelStage(**s) for s in request.funnel_stages]

        result = await workflow.execute_activity(
            publish_schema,
            PublishSchemaRequest(
                name=request.name,
                description=request.description,
                schema_type=request.schema_type,
                fields=field_mappings,
                funnel_stages=stages,
                created_by=request.created_by,
            ),
            task_queue=CONFIG_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not result.success:
            return ConfigureResult(
                success=False,
                message=f"Failed to publish schema: {result.message}",
                config_type="schema",
            )

        return ConfigureResult(
            success=True,
            message=f"Schema '{request.name}' published (v{result.version})",
            config_type="schema",
            resource_id=result.schema_id,
            version=result.version,
        )

    async def _configure_pipeline(self, request: ConfigureRequest) -> ConfigureResult:
        """Register a transformation pipeline in Config Access."""
        rules = [TransformRule(**r) for r in request.transform_rules]

        result = await workflow.execute_activity(
            define_pipeline,
            DefinePipelineRequest(
                name=request.name,
                description=request.description,
                source_type=request.source_type,
                transform_rules=rules,
                schedule_cron=request.schedule_cron,
                created_by=request.created_by,
            ),
            task_queue=CONFIG_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not result.success:
            return ConfigureResult(
                success=False,
                message=f"Failed to define pipeline: {result.message}",
                config_type="pipeline",
            )

        return ConfigureResult(
            success=True,
            message=f"Pipeline '{request.name}' defined (v{result.version})",
            config_type="pipeline",
            resource_id=result.pipeline_id,
            version=result.version,
        )

    async def _configure_view(self, request: ConfigureRequest) -> ConfigureResult:
        """Activate a data view in Config Access."""
        result = await workflow.execute_activity(
            activate_view,
            ActivateViewRequest(
                name=request.name,
                description=request.description,
                schema_id=request.schema_id,
                visibility=request.visibility,
                filters=request.filters,
                layout_config=request.layout_config,
                created_by=request.created_by,
            ),
            task_queue=CONFIG_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not result.success:
            return ConfigureResult(
                success=False,
                message=f"Failed to activate view: {result.message}",
                config_type="view",
            )

        return ConfigureResult(
            success=True,
            message=f"View '{request.name}' activated",
            config_type="view",
            resource_id=result.view_id,
            share_token=result.share_token,
        )
