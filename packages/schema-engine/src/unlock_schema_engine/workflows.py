"""Schema Engine workflows: child workflows dispatched by Data Manager.

Encapsulates the volatility of HOW data shapes evolve. New sources introduce
unexpected fields, users define new analysis schemas, existing schemas need
versioning. The Manager is unaffected by these changes.

Two workflows:
  GenerateMappingsWorkflow — discover source schema → generate field mappings
  ValidateSchemaWorkflow   — validate data against schema → detect drift
"""

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from unlock_config_access.activities import publish_schema, survey_configs
    from unlock_data_access.activities import survey_engagement
    from unlock_shared.config_models import (
        PublishSchemaRequest,
        SurveyConfigsRequest,
    )
    from unlock_shared.data_models import SurveyEngagementRequest
    from unlock_shared.schema_models import (
        GenerateMappingsPointer,
        GenerateMappingsRequest,
        ValidateSchemaPointer,
        ValidateSchemaRequest,
    )
    from unlock_shared.source_models import FetchRequest
    from unlock_shared.task_queues import (
        CONFIG_ACCESS_QUEUE,
        DATA_ACCESS_QUEUE,
        SCHEMA_ENGINE_QUEUE,
        SOURCE_ACCESS_QUEUE,
    )
    from unlock_source_access.activities import get_source_schema

    from unlock_schema_engine.activities import (
        generate_field_mappings,
        validate_and_detect_drift,
    )


@workflow.defn
class GenerateMappingsWorkflow:
    """Discover source schema, generate field mappings, store in Config Access."""

    @workflow.run
    async def run(
        self, request: GenerateMappingsRequest,
    ) -> GenerateMappingsPointer:
        # Step 1: Discover source schema from Source Access
        source_config = request.source_config
        fetch_req = FetchRequest(
            source_id=source_config.get("source_id", request.source_type),
            source_type=request.source_type,
            resource_type=source_config.get("resource_type", "posts"),
            auth_env_var=source_config.get("auth_env_var"),
            base_url=source_config.get("base_url"),
            config_json=source_config.get("config_json"),
        )

        source_schema = await workflow.execute_activity(
            get_source_schema,
            fetch_req,
            task_queue=SOURCE_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(minutes=2),
        )

        if not source_schema.success:
            return GenerateMappingsPointer(
                success=False,
                message=(
                    f"Failed to discover source schema: "
                    f"{source_schema.message}"
                ),
            )

        # Step 2: Get target schema if target_schema_id provided
        target_fields: dict[str, str] = {}
        if request.target_schema_id:
            configs_result = await workflow.execute_activity(
                survey_configs,
                SurveyConfigsRequest(
                    config_type="schema",
                    status="active",
                ),
                task_queue=CONFIG_ACCESS_QUEUE,
                start_to_close_timeout=timedelta(seconds=30),
            )

            if configs_result.success:
                for item in configs_result.items:
                    if item.get("id") == request.target_schema_id:
                        for field in item.get("fields", []):
                            name = field.get("target_field", "")
                            if name:
                                target_fields[name] = field.get(
                                    "transform", "string",
                                )
                        break

        # Step 3: Generate mappings (engine activity — pure computation)
        mapping_input = {
            "source_fields": source_schema.fields,
            "target_fields": target_fields,
        }
        mapping_output = await workflow.execute_activity(
            generate_field_mappings,
            mapping_input,
            task_queue=SCHEMA_ENGINE_QUEUE,
            start_to_close_timeout=timedelta(minutes=2),
        )

        mappings = mapping_output.get("mappings", [])
        unmapped_source = mapping_output.get("unmapped_source", [])
        unmapped_target = mapping_output.get("unmapped_target", [])

        # Step 4: Publish mappings to Config Access as a schema
        schema_name = f"{request.source_type}_mappings"
        pub_result = await workflow.execute_activity(
            publish_schema,
            PublishSchemaRequest(
                name=schema_name,
                description=(
                    f"Auto-generated mappings for {request.source_type}"
                ),
                schema_type="analysis",
                fields=mappings,
            ),
            task_queue=CONFIG_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not pub_result.success:
            return GenerateMappingsPointer(
                success=False,
                message=(
                    f"Failed to publish mappings: {pub_result.message}"
                ),
            )

        return GenerateMappingsPointer(
            success=True,
            message=(
                f"Generated {len(mappings)} mappings for "
                f"{request.source_type}"
            ),
            schema_id=pub_result.schema_id,
            version=pub_result.version,
            mappings_generated=len(mappings),
            unmapped_source_fields=unmapped_source,
            unmapped_target_fields=unmapped_target,
        )


@workflow.defn
class ValidateSchemaWorkflow:
    """Validate data against schema and detect drift."""

    @workflow.run
    async def run(
        self, request: ValidateSchemaRequest,
    ) -> ValidateSchemaPointer:
        # Step 1: Get schema definition from Config Access
        configs_result = await workflow.execute_activity(
            survey_configs,
            SurveyConfigsRequest(
                config_type="schema",
            ),
            task_queue=CONFIG_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not configs_result.success:
            return ValidateSchemaPointer(
                success=False,
                message=(
                    f"Failed to fetch schema: {configs_result.message}"
                ),
                schema_id=request.schema_id,
            )

        # Find matching schema
        schema_def = None
        for item in configs_result.items:
            if item.get("id") == request.schema_id:
                schema_def = item
                break

        if schema_def is None:
            return ValidateSchemaPointer(
                success=False,
                message=(
                    f"Schema '{request.schema_id}' not found"
                ),
                schema_id=request.schema_id,
            )

        # Step 2: Get sample data from Data Access
        engagement_result = await workflow.execute_activity(
            survey_engagement,
            SurveyEngagementRequest(
                source_key=request.source_type,
                limit=100,
            ),
            task_queue=DATA_ACCESS_QUEUE,
            start_to_close_timeout=timedelta(minutes=2),
        )

        if not engagement_result.success:
            return ValidateSchemaPointer(
                success=False,
                message=(
                    f"Failed to fetch data: "
                    f"{engagement_result.message}"
                ),
                schema_id=request.schema_id,
            )

        # Step 3: Validate + detect drift (engine activity)
        validate_input = {
            "schema_def": schema_def,
            "records": engagement_result.records,
        }
        validate_output = await workflow.execute_activity(
            validate_and_detect_drift,
            validate_input,
            task_queue=SCHEMA_ENGINE_QUEUE,
            start_to_close_timeout=timedelta(minutes=2),
        )

        drift = validate_output.get("drift", {})
        valid_count = validate_output.get("valid_count", 0)
        invalid_count = validate_output.get("invalid_count", 0)
        has_drift = drift.get("has_drift", False)
        new_fields = drift.get("new_fields", [])
        missing_fields = drift.get("missing_fields", [])

        return ValidateSchemaPointer(
            success=True,
            message=(
                f"Validated {valid_count + invalid_count} records, "
                f"drift={'yes' if has_drift else 'no'}"
            ),
            schema_id=request.schema_id,
            is_valid=invalid_count == 0,
            valid_count=valid_count,
            invalid_count=invalid_count,
            drift_detected=has_drift,
            new_fields_count=len(new_fields),
            missing_fields_count=len(missing_fields),
        )
