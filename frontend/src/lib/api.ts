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

  // ==================== Racks ====================

  async getRacks(): Promise<Rack[]> {
    const response = await this.client.get('/racks/');
    return response.data;
  }

  async getRack(id: number): Promise<Rack> {
    const response = await this.client.get(`/racks/${id}`);
    return response.data;
  }

  async createRack(data: RackCreate): Promise<Rack> {
    const response = await this.client.post('/racks/', data);
    return response.data;
  }

  async updateRack(id: number, data: Partial<RackCreate>): Promise<Rack> {
    const response = await this.client.put(`/racks/${id}`, data);
    return response.data;
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
    return response.data;
  }

  async getDevice(id: number): Promise<Device> {
    const response = await this.client.get(`/devices/${id}`);
    return response.data;
  }

  async createDevice(data: DeviceCreate): Promise<Device> {
    const response = await this.client.post('/devices/', data);
    return response.data;
  }

  async updateDevice(id: number, data: Partial<DeviceCreate>): Promise<Device> {
    const response = await this.client.put(`/devices/${id}`, data);
    return response.data;
  }

  async deleteDevice(id: number): Promise<void> {
    await this.client.delete(`/devices/${id}`);
  }

  async moveDevice(id: number, rackId: number, startUnit: number): Promise<Device> {
    const response = await this.client.post(`/devices/${id}/move`, {
      rack_id: rackId,
      start_unit: startUnit,
    });
    return response.data;
  }

  // ==================== Device Specs ====================

  async getDeviceSpecs(
    manufacturer?: string,
    deviceType?: string
  ): Promise<DeviceSpec[]> {
    const params: any = {};
    if (manufacturer) params.manufacturer = manufacturer;
    if (deviceType) params.device_type = deviceType;

    const response = await this.client.get('/device-specs/', { params });
    return response.data;
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

  async fetchSpecsFromUrl(url: string): Promise<DeviceSpec> {
    const response = await this.client.post('/device-specs/fetch/', { url });
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
