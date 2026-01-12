import axios, { type AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from 'axios';
import type {
  Rack,
  Device,
  DeviceSpec,
  Connection,
  ThermalData,
  RackCreate,
  DeviceCreate,
  ConnectionCreate,
  NetBoxHealthResponse,
  NetBoxImportResult,
} from '../types';
import { useDebugStore } from './debug-store';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class API {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // Debug logging
        if (useDebugStore.getState().enabled) {
          useDebugStore.getState().addLog({
            type: 'request',
            method: config.method?.toUpperCase(),
            url: `${config.baseURL}${config.url}`,
            data: config.data,
          });
        }

        // Store request start time
        (config as any).metadata = { startTime: Date.now() };

        // Add any auth tokens here if needed
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        // Debug logging
        if (useDebugStore.getState().enabled) {
          const duration = (response.config as any).metadata?.startTime
            ? Date.now() - (response.config as any).metadata.startTime
            : undefined;

          useDebugStore.getState().addLog({
            type: 'response',
            method: response.config.method?.toUpperCase(),
            url: `${response.config.baseURL}${response.config.url}`,
            status: response.status,
            duration,
            data: response.data,
          });
        }

        return response;
      },
      (error: AxiosError) => {
        // Debug logging
        if (useDebugStore.getState().enabled) {
          const duration = (error.config as any)?.metadata?.startTime
            ? Date.now() - (error.config as any).metadata.startTime
            : undefined;

          useDebugStore.getState().addLog({
            type: 'error',
            method: error.config?.method?.toUpperCase(),
            url: error.config?.url ? `${error.config.baseURL}${error.config.url}` : undefined,
            status: error.response?.status,
            duration,
            error: error.message,
            data: error.response?.data,
          });
        }

        // Handle errors globally
        if (error.response) {
          // Server responded with error status
          console.error('API Error:', error.response.status, error.response.data);
        } else if (error.request) {
          // Request made but no response
          console.error('Network Error:', error.message);
        } else {
          // Something else happened
          console.error('Error:', error.message);
        }
        return Promise.reject(error);
      }
    );
  }

  // Health check
  async healthCheck() {
    const response = await this.client.get('/health');
    return response.data;
  }

  // ==================== Data Transformers ====================

  // TODO: Backend should provide device_type field in DeviceSpec
  // For now, infer from brand/model as temporary solution
  private inferDeviceType(brand?: string, model?: string): string {
    const combined = `${brand} ${model}`.toLowerCase();
    if (combined.includes('switch')) return 'switch';
    if (combined.includes('router')) return 'router';
    if (combined.includes('firewall')) return 'firewall';
    if (combined.includes('server')) return 'server';
    if (combined.includes('storage')) return 'storage';
    if (combined.includes('pdu')) return 'pdu';
    if (combined.includes('ups')) return 'ups';
    return 'other';
  }

  private transformPorts(typicalPorts?: any): any[] {
    if (!typicalPorts) return [];
    return Object.entries(typicalPorts).map(([name, count]) => ({
      name,
      type: name.includes('ethernet') ? 'ethernet' : name.includes('sfp') ? 'fiber' : 'other',
      count: count as number,
    }));
  }

  private transformDevice(backendDevice: any): Device {
    // Transform backend device format to frontend format
    const spec = backendDevice.specification || {};
    return {
      id: backendDevice.id,
      name: backendDevice.custom_name || `${spec.brand || 'Unknown'} ${spec.model || 'Device'}`,
      manufacturer: spec.brand || 'Unknown',
      model: spec.model || 'Unknown',
      device_type: this.inferDeviceType(spec.brand, spec.model),
      rack_id: backendDevice.rack_id || null,
      start_unit: backendDevice.start_unit || null,
      height_units: spec.height_u || 1,
      power_consumption_watts: spec.power_watts || 0,
      weight_kg: spec.weight_kg || 0,
      temperature_celsius: backendDevice.temperature_celsius || 25,
      status: backendDevice.status || 'active',
      ip_address: backendDevice.ip_address || null,
      mac_address: backendDevice.mac_address || null,
      serial_number: backendDevice.serial_number || null,
      notes: backendDevice.notes || null,
      created_at: backendDevice.created_at || new Date().toISOString(),
      updated_at: backendDevice.last_updated || new Date().toISOString(),
      spec_id: backendDevice.specification_id,
      spec: spec ? {
        ...spec,
        // Map backend field names to frontend (for backwards compatibility)
        manufacturer: spec.brand,
        device_type: this.inferDeviceType(spec.brand, spec.model),
        height_units: spec.height_u,
        power_consumption_watts: spec.power_watts,
        max_temperature_celsius: spec.max_operating_temp_c,
        dimensions_mm: spec.depth_mm ? `${spec.depth_mm}mm depth` : null,
        ports: this.transformPorts(spec.typical_ports),
        specifications: spec,
        datasheet_url: spec.source_url || null,
        created_at: spec.fetched_at || spec.last_updated,
        updated_at: spec.last_updated,
      } : undefined,
    };
  }

  private transformRack(backendRack: any): Rack {
    // Parse width_inches from string format ('19"') to number (19)
    let width_inches = undefined;
    if (backendRack.width_inches) {
      const match = backendRack.width_inches.match(/(\d+)/);
      width_inches = match ? parseInt(match[1]) : undefined;
    }

    return {
      id: backendRack.id,
      name: backendRack.name,
      location: backendRack.location || 'Unknown',
      total_height_u: backendRack.total_height_u || 42,
      width_inches: width_inches,
      depth_mm: backendRack.depth_mm || undefined,
      max_power_watts: backendRack.max_power_watts || 5000,
      max_weight_kg: backendRack.max_weight_kg || 500,
      cooling_type: backendRack.cooling_type || undefined,
      cooling_capacity_btu: backendRack.cooling_capacity_btu || undefined,
      ambient_temp_c: backendRack.ambient_temp_c || undefined,
      max_inlet_temp_c: backendRack.max_inlet_temp_c || undefined,
      airflow_cfm: backendRack.airflow_cfm || undefined,
      created_at: backendRack.created_at || new Date().toISOString(),
      updated_at: backendRack.updated_at || new Date().toISOString(),
      devices: backendRack.devices ? backendRack.devices.map((d: any) => this.transformDevice(d)) : undefined,
    };
  }

  // ==================== Racks ====================

  async getRacks(): Promise<Rack[]> {
    const response = await this.client.get('/racks/');
    return response.data.map((rack: any) => this.transformRack(rack));
  }

  async getRack(id: number): Promise<Rack> {
    const response = await this.client.get(`/racks/${id}`);
    return this.transformRack(response.data);
  }

  async createRack(data: RackCreate): Promise<Rack> {
    // Transform width_inches to backend format (only transformation needed)
    const backendData: any = { ...data };
    if (data.width_inches !== undefined) {
      backendData.width_inches = `${data.width_inches}"`;
    }

    const response = await this.client.post('/racks/', backendData);
    return this.transformRack(response.data);
  }

  async updateRack(id: number, data: Partial<RackCreate>): Promise<Rack> {
    // Transform width_inches to backend format (only transformation needed)
    const backendData: any = { ...data };
    if (data.width_inches !== undefined) {
      backendData.width_inches = `${data.width_inches}"`;
    }

    const response = await this.client.put(`/racks/${id}`, backendData);
    return this.transformRack(response.data);
  }

  async deleteRack(id: number): Promise<void> {
    await this.client.delete(`/racks/${id}`);
  }

  async getRackThermal(id: number): Promise<ThermalData> {
    const response = await this.client.get(`/racks/${id}/thermal`);
    return response.data;
  }

  // ==================== Devices ====================

  async getDevices(rackId?: number): Promise<Device[]> {
    const params = rackId ? { rack_id: rackId } : {};
    const response = await this.client.get('/devices/', { params });
    return response.data.map((device: any) => this.transformDevice(device));
  }

  async getDevice(id: number): Promise<Device> {
    const response = await this.client.get(`/devices/${id}`);
    return this.transformDevice(response.data);
  }

  async createDevice(data: DeviceCreate): Promise<Device> {
    const response = await this.client.post('/devices/', data);
    return this.transformDevice(response.data);
  }

  async createDeviceFromModel(data: {
    model_id: number;
    custom_name?: string;
    serial_number?: string;
    access_frequency?: string;
    notes?: string;
  }): Promise<Device> {
    const response = await this.client.post('/devices/from-model', data);
    return this.transformDevice(response.data);
  }

  async updateDevice(id: number, data: Partial<DeviceCreate>): Promise<Device> {
    const response = await this.client.put(`/devices/${id}`, data);
    return this.transformDevice(response.data);
  }

  async deleteDevice(id: number): Promise<void> {
    await this.client.delete(`/devices/${id}`);
  }

  async moveDevice(id: number, rackId: number | null, startUnit: number | null): Promise<Device> {
    const response = await this.client.post(`/devices/${id}/move`, {
      rack_id: rackId,
      start_unit: startUnit,
    });
    return this.transformDevice(response.data);
  }

  // ==================== Device Specs ====================

  async getDeviceSpecs(
    brand?: string,
    deviceType?: string
  ): Promise<DeviceSpec[]> {
    const params: any = {};
    if (brand) params.brand = brand;
    if (deviceType) params.device_type = deviceType;

    const response = await this.client.get('/device-specs/', { params });
    // Add inferred device_type and frontend-compatible field aliases
    // TODO: Backend should provide device_type field
    return response.data.map((spec: any) => ({
      ...spec,
      device_type: this.inferDeviceType(spec.brand, spec.model),
      // Frontend-compatible aliases
      manufacturer: spec.brand,
      height_units: spec.height_u,
      power_consumption_watts: spec.power_watts,
    }));
  }

  async getDeviceSpec(id: number): Promise<DeviceSpec> {
    const response = await this.client.get(`/device-specs/${id}`);
    return response.data;
  }

  async createDeviceSpec(data: Omit<DeviceSpec, 'id'>): Promise<DeviceSpec> {
    const response = await this.client.post('/device-specs/', data);
    return response.data;
  }

  async updateDeviceSpec(id: number, data: Partial<DeviceSpec>): Promise<DeviceSpec> {
    const response = await this.client.put(`/device-specs/${id}`, data);
    return response.data;
  }

  async deleteDeviceSpec(id: number): Promise<void> {
    await this.client.delete(`/device-specs/${id}`);
  }

  async fetchSpecsFromUrl(brand: string, model: string): Promise<DeviceSpec> {
    const response = await this.client.post('/device-specs/fetch/', { brand, model });
    return response.data;
  }

  // ==================== Connections ====================

  async getConnections(rackId?: number): Promise<Connection[]> {
    const params = rackId ? { rack_id: rackId } : {};
    const response = await this.client.get('/connections/', { params });
    return response.data;
  }

  async getConnection(id: number): Promise<Connection> {
    const response = await this.client.get(`/connections/${id}`);
    return response.data;
  }

  async createConnection(data: ConnectionCreate): Promise<Connection> {
    const response = await this.client.post('/connections/', data);
    return response.data;
  }

  async updateConnection(id: number, data: Partial<ConnectionCreate>): Promise<Connection> {
    const response = await this.client.put(`/connections/${id}`, data);
    return response.data;
  }

  async deleteConnection(id: number): Promise<void> {
    await this.client.delete(`/connections/${id}`);
  }

  async validateConnection(data: ConnectionCreate): Promise<{
    valid: boolean;
    warnings: string[];
    errors: string[];
  }> {
    const response = await this.client.post('/connections/validate', data);
    return response.data;
  }

  // ==================== Stats & Analytics ====================

  async getStats(): Promise<{
    total_racks: number;
    total_devices: number;
    total_connections: number;
    total_power_consumption: number;
    average_temperature: number;
    rack_utilization: number;
  }> {
    const response = await this.client.get('/stats/');
    return response.data;
  }

  async getRackUtilization(id: number): Promise<{
    rack_id: number;
    total_units: number;
    used_units: number;
    utilization_percentage: number;
    devices_count: number;
  }> {
    const response = await this.client.get(`/racks/${id}/utilization`);
    return response.data;
  }

  // ==================== Search ====================

  async searchDevices(query: string): Promise<Device[]> {
    const response = await this.client.get('/devices/search', {
      params: { q: query },
    });
    return response.data;
  }

  async searchDeviceSpecs(query: string): Promise<DeviceSpec[]> {
    const response = await this.client.get('/device-specs/search', {
      params: { q: query },
    });
    return response.data;
  }

  // ==================== NetBox DCIM Integration ====================

  async checkNetBoxHealth(): Promise<NetBoxHealthResponse> {
    const response = await this.client.get('/dcim/health');
    return response.data;
  }

  async importRackFromNetBox(
    rackName: string,
    importDevices: boolean = true,
    overwriteExisting: boolean = false
  ): Promise<NetBoxImportResult> {
    const response = await this.client.post('/dcim/import-rack', {
      rack_name: rackName,
      import_devices: importDevices,
      overwrite_existing: overwriteExisting,
    });
    return response.data;
  }

  // ==================== Optimization ====================

  async optimizeRack(
    rackId: number,
    lockedDeviceIds?: number[],
    weights?: {
      cable?: number;
      weight?: number;
      thermal?: number;
      access?: number;
    }
  ): Promise<any> {
    const response = await this.client.post(`/racks/${rackId}/optimize`, {
      locked_positions: lockedDeviceIds || [],
      weights: weights || {
        cable: 0.30,
        weight: 0.25,
        thermal: 0.25,
        access: 0.20
      }
    });
    return response.data;
  }
}

// Export singleton instance
export const api = new API();

// Export error helper
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.data?.detail) {
      return typeof error.response.data.detail === 'string'
        ? error.response.data.detail
        : JSON.stringify(error.response.data.detail);
    }
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unknown error occurred';
}
