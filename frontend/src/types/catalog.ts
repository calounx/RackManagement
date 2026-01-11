/**
 * TypeScript interfaces for the device catalog system
 * Matches backend Pydantic schemas in app/schemas.py
 */

// ============================================================================
// Enums
// ============================================================================

export enum DCIMType {
  NETBOX = 'netbox',
  RACKTABLES = 'racktables',
  RALPH = 'ralph',
}

export enum FetchConfidence {
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low',
}

// ============================================================================
// Pagination
// ============================================================================

export interface PaginationMetadata {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============================================================================
// Device Type Interfaces
// ============================================================================

export interface DeviceTypeBase {
  name: string;
  slug: string;
  icon?: string | null;
  description?: string | null;
  color?: string | null;
}

export interface DeviceTypeCreate extends DeviceTypeBase {}

export interface DeviceTypeUpdate {
  name?: string;
  slug?: string;
  icon?: string | null;
  description?: string | null;
  color?: string | null;
}

export interface DeviceTypeSummary {
  id: number;
  name: string;
  slug: string;
  icon?: string | null;
  color?: string | null;
}

export interface DeviceTypeResponse extends DeviceTypeBase {
  id: number;
  created_at: string;
  updated_at: string;
  model_count: number;
}

export interface DeviceTypeListResponse {
  items: DeviceTypeResponse[];
  pagination: PaginationMetadata;
}

// ============================================================================
// Brand Interfaces
// ============================================================================

export interface BrandBase {
  name: string;
  slug: string;
  website?: string | null;
  support_url?: string | null;
  logo_url?: string | null;
  description?: string | null;
  founded_year?: number | null;
  headquarters?: string | null;
}

export interface BrandCreate extends BrandBase {}

export interface BrandUpdate {
  name?: string;
  slug?: string;
  website?: string | null;
  support_url?: string | null;
  logo_url?: string | null;
  description?: string | null;
  founded_year?: number | null;
  headquarters?: string | null;
}

export interface BrandSummary {
  id: number;
  name: string;
  slug: string;
  logo_url?: string | null;
}

export interface BrandResponse extends BrandBase {
  id: number;
  last_fetched_at?: string | null;
  fetch_confidence?: FetchConfidence | null;
  fetch_source?: string | null;
  created_at: string;
  updated_at: string;
  model_count: number;
}

export interface BrandListResponse {
  items: BrandResponse[];
  pagination: PaginationMetadata;
}

// ============================================================================
// Model Interfaces
// ============================================================================

export interface ModelBase {
  name: string;
  variant?: string | null;
  description?: string | null;

  // Lifecycle
  release_date?: string | null;
  end_of_life?: string | null;

  // Physical dimensions
  height_u: number;
  width_type?: string | null;
  depth_mm?: number | null;
  weight_kg?: number | null;

  // Power and thermal
  power_watts?: number | null;
  heat_output_btu?: number | null;
  airflow_pattern?: string | null;
  max_operating_temp_c?: number | null;

  // Connectivity
  typical_ports?: Record<string, number> | null;

  // Mounting
  mounting_type?: string | null;

  // Documentation
  datasheet_url?: string | null;
  image_url?: string | null;
}

export interface ModelCreate extends ModelBase {
  brand_id: number;
  device_type_id: number;
  source?: string | null;
  confidence?: string | null;
}

export interface ModelUpdate {
  brand_id?: number;
  device_type_id?: number;
  name?: string;
  variant?: string | null;
  description?: string | null;
  release_date?: string | null;
  end_of_life?: string | null;
  height_u?: number;
  width_type?: string | null;
  depth_mm?: number | null;
  weight_kg?: number | null;
  power_watts?: number | null;
  heat_output_btu?: number | null;
  airflow_pattern?: string | null;
  max_operating_temp_c?: number | null;
  typical_ports?: Record<string, number> | null;
  mounting_type?: string | null;
  datasheet_url?: string | null;
  image_url?: string | null;
  source?: string | null;
  confidence?: string | null;
}

export interface ModelResponse extends ModelBase {
  id: number;
  brand_id: number;
  device_type_id: number;
  brand: BrandSummary;
  device_type: DeviceTypeSummary;
  source?: string | null;
  confidence?: string | null;
  fetched_at?: string | null;
  last_updated: string;
  device_count: number;
}

export interface ModelListResponse {
  items: ModelResponse[];
  pagination: PaginationMetadata;
}

// ============================================================================
// DCIM Connection Interfaces
// ============================================================================

export interface DCIMConnectionBase {
  name: string;
  type: DCIMType;
  base_url: string;
  api_token?: string | null;
  is_public: boolean;
}

export interface DCIMConnectionCreate extends DCIMConnectionBase {}

export interface DCIMConnectionUpdate {
  name?: string;
  type?: DCIMType;
  base_url?: string;
  api_token?: string | null;
  is_public?: boolean;
}

export interface DCIMConnectionResponse extends DCIMConnectionBase {
  id: number;
  last_sync?: string | null;
  sync_status?: string | null;
  created_at: string;
  updated_at: string;
  api_token?: string | null; // Masked in backend response
}

export interface DCIMConnectionListResponse {
  items: DCIMConnectionResponse[];
  pagination: PaginationMetadata;
}

export interface DCIMConnectionTestResult {
  success: boolean;
  message: string;
  response_time_ms?: number | null;
  system_info?: Record<string, any> | null;
}

// ============================================================================
// Filter and Search Types
// ============================================================================

export interface DeviceTypeFilters {
  search?: string;
  page?: number;
  page_size?: number;
}

export interface BrandFilters {
  search?: string;
  device_type_id?: number;
  page?: number;
  page_size?: number;
}

export interface ModelFilters {
  search?: string;
  brand_id?: number;
  device_type_id?: number;
  page?: number;
  page_size?: number;
}

export interface DCIMConnectionFilters {
  search?: string;
  type?: DCIMType;
  page?: number;
  page_size?: number;
}
