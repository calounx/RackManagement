// ==================== Core Models ====================

export interface Rack {
  id: number;
  name: string;
  location: string;
  total_height_u: number;
  width_inches?: number;
  depth_mm?: number;
  max_power_watts: number;
  max_weight_kg: number;
  cooling_type?: string;
  cooling_capacity_btu?: number;
  ambient_temp_c?: number;
  max_inlet_temp_c?: number;
  airflow_cfm?: number;
  created_at: string;
  updated_at: string;
  devices?: Device[];
}

export interface RackCreate {
  name: string;
  location: string;
  total_height_u?: number;
  width_inches?: number;
  depth_mm?: number;
  max_power_watts?: number;
  max_weight_kg?: number;
  cooling_type?: string;
  cooling_capacity_btu?: number;
  ambient_temp_c?: number;
  max_inlet_temp_c?: number;
  airflow_cfm?: number;
}

export interface Device {
  id: number;
  name: string;
  manufacturer: string;
  model: string;
  device_type: string;
  rack_id: number | null;
  start_unit: number | null;
  height_units: number;
  power_consumption_watts: number;
  weight_kg: number;
  temperature_celsius: number;
  status: DeviceStatus;
  ip_address: string | null;
  mac_address: string | null;
  serial_number: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  spec_id?: number;
  rack?: Rack;
  spec?: DeviceSpec;
}

export interface DeviceCreate {
  name: string;
  manufacturer: string;
  model: string;
  device_type: string;
  rack_id?: number | null;
  start_unit?: number | null;
  height_units?: number;
  power_consumption_watts?: number;
  weight_kg?: number;
  temperature_celsius?: number;
  status?: DeviceStatus;
  ip_address?: string | null;
  mac_address?: string | null;
  serial_number?: string | null;
  notes?: string | null;
  spec_id?: number | null;
}

export interface DeviceSpec {
  // Backend fields (primary)
  id: number;
  brand: string;
  model: string;
  variant: string | null;
  height_u: number;
  width_type: string;
  depth_mm: number;
  weight_kg: number;
  power_watts: number;
  heat_output_btu: number;
  airflow_pattern: string;
  max_operating_temp_c: number;
  typical_ports: Record<string, number> | null;
  mounting_type: string;
  source: string;
  source_url: string | null;
  confidence: string;
  fetched_at: string | null;
  last_updated: string;
  device_type: string; // Inferred from brand/model until backend provides it

  // Frontend-compatible aliases (for backwards compatibility)
  manufacturer: string; // Alias for brand
  height_units: number; // Alias for height_u
  power_consumption_watts: number; // Alias for power_watts
}

export interface PortSpec {
  name: string;
  type: string;
  count: number;
  speed?: string;
}

export interface Connection {
  id: number;
  source_device_id: number;
  source_port: string;
  target_device_id: number;
  target_port: string;
  cable_type: CableType;
  cable_length_meters: number;
  status: ConnectionStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
  source_device?: Device;
  target_device?: Device;
}

export interface ConnectionCreate {
  source_device_id: number;
  source_port: string;
  target_device_id: number;
  target_port: string;
  cable_type: CableType;
  cable_length_meters?: number;
  status?: ConnectionStatus;
  notes?: string | null;
}

// ==================== Enums ====================

export type DeviceStatus = 'active' | 'inactive' | 'maintenance' | 'error';

export type CableType = 'ethernet' | 'fiber' | 'power' | 'console' | 'other';

export type ConnectionStatus = 'active' | 'inactive' | 'planned' | 'disconnected';

export type DeviceType =
  | 'server'
  | 'switch'
  | 'router'
  | 'firewall'
  | 'storage'
  | 'pdu'
  | 'ups'
  | 'patch_panel'
  | 'other';

// ==================== Thermal Data ====================

export interface ThermalData {
  rack_id: number;
  average_temperature: number;
  max_temperature: number;
  min_temperature: number;
  hotspots: ThermalHotspot[];
  airflow_direction: 'front-to-back' | 'back-to-front' | 'side-to-side';
  cooling_efficiency: number;
  timestamp: string;
}

export interface ThermalHotspot {
  device_id: number;
  device_name: string;
  temperature: number;
  start_unit: number;
  height_units: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

// ==================== Stats ====================

export interface SystemStats {
  total_racks: number;
  total_devices: number;
  total_connections: number;
  total_power_consumption: number;
  average_temperature: number;
  rack_utilization: number;
}

export interface RackUtilization {
  rack_id: number;
  total_units: number;
  used_units: number;
  utilization_percentage: number;
  devices_count: number;
}

// ==================== Validation ====================

export interface ValidationResult {
  valid: boolean;
  warnings: string[];
  errors: string[];
}

// ==================== UI State ====================

export interface Toast {
  id: string;
  title: string;
  description?: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
}

export interface DialogState {
  isOpen: boolean;
  title?: string;
  content?: React.ReactNode;
  onConfirm?: () => void;
  onCancel?: () => void;
}

export interface FilterState {
  search: string;
  status?: DeviceStatus;
  deviceType?: DeviceType;
  manufacturer?: string;
  rackId?: number;
}

export interface SortConfig {
  key: string;
  direction: 'asc' | 'desc';
}

// ==================== Form Data ====================

export interface DeviceFormData extends Omit<DeviceCreate, 'spec_id'> {
  useSpec?: boolean;
  selectedSpecId?: number;
}

export interface RackFormData extends RackCreate {
  // Additional form-specific fields if needed
}

export interface ConnectionFormData extends ConnectionCreate {
  // Additional form-specific fields if needed
}

// ==================== View Options ====================

export interface RackViewOptions {
  showThermal: boolean;
  showConnections: boolean;
  showLabels: boolean;
  zoom: number;
}

export interface TableColumn<T> {
  key: keyof T | string;
  label: string;
  sortable?: boolean;
  render?: (value: any, row: T) => React.ReactNode;
  width?: string;
}

// ==================== API Response Types ====================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ErrorResponse {
  detail: string | Record<string, any>;
  status_code: number;
}

// ==================== Chart Data ====================

export interface ChartDataPoint {
  label: string;
  value: number;
  color?: string;
}

export interface TimeSeriesData {
  timestamp: string;
  value: number;
}

export interface PowerDistribution {
  rack_id: number;
  rack_name: string;
  current_power: number;
  max_power: number;
  percentage: number;
}

// ==================== Export Types ====================

export interface ExportOptions {
  format: 'json' | 'csv' | 'pdf';
  includeConnections?: boolean;
  includeThermal?: boolean;
  includeSpecs?: boolean;
}

// ==================== Search Results ====================

export interface SearchResult {
  type: 'device' | 'rack' | 'connection';
  id: number;
  title: string;
  subtitle?: string;
  metadata?: Record<string, any>;
}

// ==================== Drag and Drop ====================

export interface DraggedDevice {
  device: Device;
  sourceRackId: number | null;
  sourceStartUnit: number | null;
}

export interface DropTarget {
  rackId: number;
  startUnit: number;
  valid: boolean;
  reason?: string;
}

// ==================== Notification Types ====================

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  actionUrl?: string;
  actionLabel?: string;
}

// ==================== User Preferences ====================

export interface UserPreferences {
  theme: 'dark' | 'light';
  defaultView: 'grid' | 'list' | 'rack';
  autoRefresh: boolean;
  refreshInterval: number;
  temperatureUnit: 'celsius' | 'fahrenheit';
  powerUnit: 'watts' | 'kilowatts';
  notifications: {
    thermal: boolean;
    power: boolean;
    connections: boolean;
  };
}

// ==================== Health Check ====================

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'down';
  database: boolean;
  api_version: string;
  uptime_seconds: number;
  timestamp: string;
}

// ==================== Device Catalog Management ====================

export interface DeviceTypeInfo {
  id: number;
  name: string;
  value: DeviceType;
  icon: string;
  color: string;
  brandsCount?: number;
  modelsCount?: number;
  description?: string;
}

export interface DeviceTypeCreate {
  name: string;
  value: DeviceType;
  icon: string;
  color: string;
  description?: string;
}

export interface Brand {
  id: number;
  name: string;
  device_types: DeviceType[];
  modelsCount?: number;
  created_at: string;
  updated_at: string;
}

export interface BrandCreate {
  name: string;
  device_types?: DeviceType[];
}

export interface ModelInfo {
  id: number;
  brand: string;
  model: string;
  device_type: DeviceType;
  height_units: number;
  power_consumption_watts: number;
  weight_kg: number;
  usageCount?: number;
  created_at: string;
  updated_at: string;
}
