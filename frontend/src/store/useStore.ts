import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type {
  Rack,
  Device,
  DeviceSpec,
  Connection,
  Toast,
  UserPreferences,
  FilterState,
  SortConfig,
  RackViewOptions,
} from '../types';
import { api, getErrorMessage } from '../lib/api';

interface AppState {
  // Data
  racks: Rack[];
  devices: Device[];
  deviceSpecs: DeviceSpec[];
  connections: Connection[];

  // UI State
  selectedRackId: number | null;
  selectedDeviceId: number | null;
  toasts: Toast[];
  loading: boolean;
  error: string | null;

  // Filters & Sorting
  filters: FilterState;
  sortConfig: SortConfig;

  // View Options
  rackViewOptions: RackViewOptions;

  // User Preferences
  preferences: UserPreferences;

  // Actions - Data Loading
  fetchRacks: () => Promise<void>;
  fetchDevices: (rackId?: number) => Promise<void>;
  fetchDeviceSpecs: () => Promise<void>;
  fetchConnections: (rackId?: number) => Promise<void>;
  refreshAll: () => Promise<void>;

  // Actions - Racks
  createRack: (data: any) => Promise<Rack | null>;
  updateRack: (id: number, data: any) => Promise<void>;
  deleteRack: (id: number) => Promise<void>;
  selectRack: (id: number | null) => void;

  // Actions - Devices
  createDevice: (data: any) => Promise<Device | null>;
  createDeviceFromModel: (data: any) => Promise<Device | null>;
  updateDevice: (id: number, data: any) => Promise<void>;
  deleteDevice: (id: number) => Promise<void>;
  moveDevice: (id: number, rackId: number | null, startUnit: number | null) => Promise<void>;
  selectDevice: (id: number | null) => void;

  // Actions - Device Specs
  createDeviceSpec: (data: any) => Promise<DeviceSpec | null>;
  fetchSpecsFromUrl: (brand: string, model: string) => Promise<DeviceSpec | null>;

  // Actions - Connections
  createConnection: (data: any) => Promise<Connection | null>;
  updateConnection: (id: number, data: any) => Promise<void>;
  deleteConnection: (id: number) => Promise<void>;

  // Actions - UI
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  setError: (error: string | null) => void;
  setFilters: (filters: Partial<FilterState>) => void;
  setSortConfig: (config: SortConfig) => void;
  setRackViewOptions: (options: Partial<RackViewOptions>) => void;
  setPreferences: (preferences: Partial<UserPreferences>) => void;
}

const defaultPreferences: UserPreferences = {
  theme: 'dark',
  defaultView: 'rack',
  autoRefresh: false,
  refreshInterval: 30000,
  temperatureUnit: 'celsius',
  powerUnit: 'watts',
  notifications: {
    thermal: true,
    power: true,
    connections: true,
  },
};

const defaultRackViewOptions: RackViewOptions = {
  showThermal: false,
  showConnections: true,
  showLabels: true,
  zoom: 1,
};

export const useStore = create<AppState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial State
        racks: [],
        devices: [],
        deviceSpecs: [],
        connections: [],
        selectedRackId: null,
        selectedDeviceId: null,
        toasts: [],
        loading: false,
        error: null,
        filters: {
          search: '',
        },
        sortConfig: {
          key: 'name',
          direction: 'asc',
        },
        rackViewOptions: defaultRackViewOptions,
        preferences: defaultPreferences,

        // Data Loading Actions
        fetchRacks: async () => {
          set({ loading: true, error: null });
          try {
            const racks = await api.getRacks();
            set({ racks, loading: false });
          } catch (error) {
            const message = getErrorMessage(error);
            set({ error: message, loading: false });
            get().addToast({
              title: 'Error loading racks',
              description: message,
              type: 'error',
            });
          }
        },

        fetchDevices: async (rackId?: number) => {
          set({ loading: true, error: null });
          try {
            const devices = await api.getDevices(rackId);
            set({ devices, loading: false });
          } catch (error) {
            const message = getErrorMessage(error);
            set({ error: message, loading: false });
            get().addToast({
              title: 'Error loading devices',
              description: message,
              type: 'error',
            });
          }
        },

        fetchDeviceSpecs: async () => {
          set({ loading: true, error: null });
          try {
            const deviceSpecs = await api.getDeviceSpecs();
            set({ deviceSpecs, loading: false });
          } catch (error) {
            const message = getErrorMessage(error);
            set({ error: message, loading: false });
            get().addToast({
              title: 'Error loading device specs',
              description: message,
              type: 'error',
            });
          }
        },

        fetchConnections: async (rackId?: number) => {
          set({ loading: true, error: null });
          try {
            const connections = await api.getConnections(rackId);
            set({ connections, loading: false });
          } catch (error) {
            const message = getErrorMessage(error);
            set({ error: message, loading: false });
            get().addToast({
              title: 'Error loading connections',
              description: message,
              type: 'error',
            });
          }
        },

        refreshAll: async () => {
          await Promise.all([
            get().fetchRacks(),
            get().fetchDevices(),
            get().fetchDeviceSpecs(),
            get().fetchConnections(),
          ]);
        },

        // Rack Actions
        createRack: async (data) => {
          set({ loading: true, error: null });
          try {
            const rack = await api.createRack(data);
            set((state) => ({
              racks: [...state.racks, rack],
              loading: false,
            }));
            get().addToast({
              title: 'Rack created',
              description: `${rack.name} has been created successfully`,
              type: 'success',
            });
            return rack;
          } catch (error) {
            const message = getErrorMessage(error);
            set({ error: message, loading: false });
            get().addToast({
              title: 'Error creating rack',
              description: message,
              type: 'error',
            });
            return null;
          }
        },

        updateRack: async (id, data) => {
          set({ loading: true, error: null });
          try {
            const updated = await api.updateRack(id, data);
            set((state) => ({
              racks: state.racks.map((r) => (r.id === id ? updated : r)),
              loading: false,
            }));
            get().addToast({
              title: 'Rack updated',
              description: `${updated.name} has been updated`,
              type: 'success',
            });
          } catch (error) {
            const message = getErrorMessage(error);
            set({ error: message, loading: false });
            get().addToast({
              title: 'Error updating rack',
              description: message,
              type: 'error',
            });
          }
        },

        deleteRack: async (id) => {
          set({ loading: true, error: null });
          try {
            await api.deleteRack(id);
            set((state) => ({
              racks: state.racks.filter((r) => r.id !== id),
              selectedRackId: state.selectedRackId === id ? null : state.selectedRackId,
              loading: false,
            }));
            get().addToast({
              title: 'Rack deleted',
              description: 'Rack has been deleted successfully',
              type: 'success',
            });
          } catch (error) {
            const message = getErrorMessage(error);
            set({ error: message, loading: false });
            get().addToast({
              title: 'Error deleting rack',
              description: message,
              type: 'error',
            });
          }
        },

        selectRack: (id) => set({ selectedRackId: id }),

        // Device Actions
        createDevice: async (data) => {
          set({ loading: true, error: null });
          try {
            const device = await api.createDevice(data);
            set((state) => ({
              devices: [...state.devices, device],
              loading: false,
            }));
            get().addToast({
              title: 'Device created',
              description: `${device.name} has been created successfully`,
              type: 'success',
            });
            return device;
          } catch (error) {
            const message = getErrorMessage(error);
            set({ error: message, loading: false });
            get().addToast({
              title: 'Error creating device',
              description: message,
              type: 'error',
            });
            return null;
          }
        },

        createDeviceFromModel: async (data) => {
          set({ loading: true, error: null });
          try {
            const device = await api.createDeviceFromModel(data);
            set((state) => ({
              devices: [...state.devices, device],
              loading: false,
            }));
            get().addToast({
              title: 'Device created from catalog',
              description: `${device.name} has been created successfully`,
              type: 'success',
            });
            return device;
          } catch (error) {
            const message = getErrorMessage(error);
            set({ error: message, loading: false });
            get().addToast({
              title: 'Error creating device',
              description: message,
              type: 'error',
            });
            return null;
          }
        },

        updateDevice: async (id, data) => {
          set({ loading: true, error: null });
          try {
            const updated = await api.updateDevice(id, data);
            set((state) => ({
              devices: state.devices.map((d) => (d.id === id ? updated : d)),
              loading: false,
            }));
            get().addToast({
              title: 'Device updated',
              description: `${updated.name} has been updated`,
              type: 'success',
            });
          } catch (error) {
            const message = getErrorMessage(error);
            set({ error: message, loading: false });
            get().addToast({
              title: 'Error updating device',
              description: message,
              type: 'error',
            });
          }
        },

        deleteDevice: async (id) => {
          set({ loading: true, error: null });
          try {
            await api.deleteDevice(id);
            set((state) => ({
              devices: state.devices.filter((d) => d.id !== id),
              selectedDeviceId: state.selectedDeviceId === id ? null : state.selectedDeviceId,
              loading: false,
            }));
            get().addToast({
              title: 'Device deleted',
              description: 'Device has been deleted successfully',
              type: 'success',
            });
          } catch (error) {
            const message = getErrorMessage(error);
            set({ error: message, loading: false });
            get().addToast({
              title: 'Error deleting device',
              description: message,
              type: 'error',
            });
          }
        },

        moveDevice: async (id, rackId, startUnit) => {
          set({ loading: true, error: null });
          try {
            const updated = await api.moveDevice(id, rackId, startUnit);
            set((state) => ({
              devices: state.devices.map((d) => (d.id === id ? updated : d)),
              loading: false,
            }));
            const message = rackId === null
              ? 'Device removed from rack'
              : `Device moved to rack unit ${startUnit}`;
            get().addToast({
              title: rackId === null ? 'Device removed' : 'Device moved',
              description: message,
              type: 'success',
            });
          } catch (error) {
            const message = getErrorMessage(error);
            set({ error: message, loading: false });
            get().addToast({
              title: 'Error moving device',
              description: message,
              type: 'error',
            });
          }
        },

        selectDevice: (id) => set({ selectedDeviceId: id }),

        // Device Spec Actions
        createDeviceSpec: async (data) => {
          set({ loading: true, error: null });
          try {
            const spec = await api.createDeviceSpec(data);
            set((state) => ({
              deviceSpecs: [...state.deviceSpecs, spec],
              loading: false,
            }));
            get().addToast({
              title: 'Device spec created',
              description: `${spec.manufacturer} ${spec.model} spec created`,
              type: 'success',
            });
            return spec;
          } catch (error) {
            const message = getErrorMessage(error);
            set({ error: message, loading: false });
            get().addToast({
              title: 'Error creating device spec',
              description: message,
              type: 'error',
            });
            return null;
          }
        },

        fetchSpecsFromUrl: async (brand, model) => {
          set({ loading: true, error: null });
          try {
            const spec = await api.fetchSpecsFromUrl(brand, model);
            set((state) => ({
              deviceSpecs: [...state.deviceSpecs, spec],
              loading: false,
            }));
            get().addToast({
              title: 'Specs fetched',
              description: `Fetched specs for ${spec.manufacturer} ${spec.model}`,
              type: 'success',
            });
            return spec;
          } catch (error) {
            const message = getErrorMessage(error);
            set({ error: message, loading: false });
            get().addToast({
              title: 'Error fetching specs',
              description: message,
              type: 'error',
            });
            return null;
          }
        },

        // Connection Actions
        createConnection: async (data) => {
          set({ loading: true, error: null });
          try {
            const connection = await api.createConnection(data);
            set((state) => ({
              connections: [...state.connections, connection],
              loading: false,
            }));
            get().addToast({
              title: 'Connection created',
              description: 'Connection has been created successfully',
              type: 'success',
            });
            return connection;
          } catch (error) {
            const message = getErrorMessage(error);
            set({ error: message, loading: false });
            get().addToast({
              title: 'Error creating connection',
              description: message,
              type: 'error',
            });
            return null;
          }
        },

        updateConnection: async (id, data) => {
          set({ loading: true, error: null });
          try {
            const updated = await api.updateConnection(id, data);
            set((state) => ({
              connections: state.connections.map((c) => (c.id === id ? updated : c)),
              loading: false,
            }));
            get().addToast({
              title: 'Connection updated',
              description: 'Connection has been updated',
              type: 'success',
            });
          } catch (error) {
            const message = getErrorMessage(error);
            set({ error: message, loading: false });
            get().addToast({
              title: 'Error updating connection',
              description: message,
              type: 'error',
            });
          }
        },

        deleteConnection: async (id) => {
          set({ loading: true, error: null });
          try {
            await api.deleteConnection(id);
            set((state) => ({
              connections: state.connections.filter((c) => c.id !== id),
              loading: false,
            }));
            get().addToast({
              title: 'Connection deleted',
              description: 'Connection has been deleted successfully',
              type: 'success',
            });
          } catch (error) {
            const message = getErrorMessage(error);
            set({ error: message, loading: false });
            get().addToast({
              title: 'Error deleting connection',
              description: message,
              type: 'error',
            });
          }
        },

        // UI Actions
        addToast: (toast) => {
          const id = `toast-${Date.now()}-${Math.random()}`;
          const newToast: Toast = {
            ...toast,
            id,
            duration: toast.duration || 5000,
          };

          set((state) => ({
            toasts: [...state.toasts, newToast],
          }));

          // Auto remove after duration
          if (newToast.duration && newToast.duration > 0) {
            setTimeout(() => {
              get().removeToast(id);
            }, newToast.duration);
          }
        },

        removeToast: (id) => {
          set((state) => ({
            toasts: state.toasts.filter((t) => t.id !== id),
          }));
        },

        setError: (error) => set({ error }),

        setFilters: (filters) => {
          set((state) => ({
            filters: { ...state.filters, ...filters },
          }));
        },

        setSortConfig: (sortConfig) => set({ sortConfig }),

        setRackViewOptions: (options) => {
          set((state) => ({
            rackViewOptions: { ...state.rackViewOptions, ...options },
          }));
        },

        setPreferences: (preferences) => {
          set((state) => ({
            preferences: { ...state.preferences, ...preferences },
          }));
        },
      }),
      {
        name: 'homerack-storage',
        partialize: (state) => ({
          preferences: state.preferences,
          rackViewOptions: state.rackViewOptions,
        }),
      }
    )
  )
);
