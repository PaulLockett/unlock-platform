/**
 * TypeScript interfaces mirroring the Python boundary models.
 *
 * These types match the Pydantic models in unlock_shared so the Canvas
 * can serialize/deserialize workflow inputs and results correctly.
 */

// ============================================================================
// Domain objects
// ============================================================================

export interface FieldMapping {
  source_field: string;
  target_field: string;
  transform?: string | null;
  default_value?: string | null;
}

export interface TransformRule {
  rule_type: string;
  config?: Record<string, string | number | boolean | null>;
  order?: number;
}

export interface FunnelStage {
  name: string;
  description?: string | null;
  filter_expression?: string | null;
  order?: number;
}

export interface SchemaDefinition {
  id: string;
  name: string;
  description?: string | null;
  version: number;
  status: string;
  schema_type: string;
  fields: FieldMapping[];
  funnel_stages: FunnelStage[];
  created_at?: string | null;
  updated_at?: string | null;
  created_by?: string | null;
}

export interface PipelineDefinition {
  id: string;
  name: string;
  description?: string | null;
  version: number;
  status: string;
  source_type: string;
  transform_rules: TransformRule[];
  schedule_cron?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  created_by?: string | null;
}

export interface PanelPosition {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface ChartConfig {
  x_axis?: string;
  y_axis?: string;
  group_by?: string;
  color_scheme?: string;
  value_field?: string;
  label_field?: string;
  columns?: string[];
  sort_by?: string;
  sort_direction?: "asc" | "desc";
  page_size?: number;
  aggregation?: string;
  label?: string;
  stacked?: boolean;
  warning_threshold?: number;
  critical_threshold?: number;
}

export interface PanelQueryConfig {
  schema_id?: string;
  channel_key?: string | null;
  engagement_type?: string | null;
  since?: string | null;
  until?: string | null;
  source_key?: string | null;
}

export type ChartType =
  | "bar"
  | "line"
  | "pie"
  | "area"
  | "funnel"
  | "table"
  | "metric";

export interface Panel {
  id: string;
  title: string;
  chart_type: ChartType;
  position: PanelPosition;
  chart_config: ChartConfig;
  query_config: PanelQueryConfig;
}

export interface LayoutConfig {
  grid_columns: number;
  panels: Panel[];
}

export interface ViewDefinition {
  id: string;
  name: string;
  description?: string | null;
  schema_id: string;
  status: string;
  share_token?: string | null;
  visibility: string;
  filters: Record<string, unknown>;
  layout_config: LayoutConfig | Record<string, unknown>;
  cloned_from?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  created_by?: string | null;
}

export interface ViewPermission {
  view_id: string;
  principal_id: string;
  principal_type: string;
  permission: "read" | "write" | "admin";
  granted_at?: string | null;
  granted_by?: string | null;
}

// ============================================================================
// Manager Request/Result (what Canvas sends to API routes)
// ============================================================================

export interface QueryRequest {
  share_token: string;
  user_id: string;
  user_type?: string;
  channel_key?: string | null;
  engagement_type?: string | null;
  since?: string | null;
  until?: string | null;
  limit?: number;
  offset?: number;
}

export interface QueryResult {
  success: boolean;
  message: string;
  records: Record<string, unknown>[];
  total_count: number;
  has_more: boolean;
  view_name: string;
  schema_id: string;
}

export interface ConfigureRequest {
  config_type: "schema" | "pipeline" | "view";
  name: string;
  description?: string | null;
  created_by?: string | null;
  // Schema-specific
  schema_type?: string;
  fields?: Record<string, unknown>[];
  funnel_stages?: Record<string, unknown>[];
  // Pipeline-specific
  source_type?: string;
  transform_rules?: Record<string, unknown>[];
  schedule_cron?: string | null;
  // View-specific
  schema_id?: string;
  filters?: Record<string, unknown>;
  layout_config?: Record<string, unknown>;
  visibility?: string;
}

export interface ConfigureResult {
  success: boolean;
  message: string;
  config_type: string;
  resource_id: string;
  version: number;
  share_token: string;
}

export interface ShareRequest {
  share_token: string;
  granter_id: string;
  recipient_id: string;
  recipient_type?: string;
  permission: string;
}

export interface ShareResult {
  success: boolean;
  message: string;
  view_id: string;
  share_token: string;
  granted_permission: string;
}

export interface RetrieveViewResult {
  success: boolean;
  message: string;
  view: ViewDefinition | null;
  schema_def: SchemaDefinition | null;
  permissions: ViewPermission[];
}

export interface SurveyConfigsResult {
  success: boolean;
  message: string;
  items: Record<string, unknown>[];
  total_count: number;
  has_more: boolean;
}

// ============================================================================
// Ingest (admin)
// ============================================================================

export interface IngestRequest {
  source_name: string;
  source_type: string;
  resource_type?: string;
  channel_key?: string | null;
  auth_env_var?: string | null;
  base_url?: string | null;
  config_json?: string | null;
  since?: string | null;
  max_pages?: number;
}

export interface IngestResult {
  success: boolean;
  message: string;
  source_name: string;
  records_fetched: number;
  records_stored: number;
  records_transformed: number;
  pipeline_run_id: string;
}
