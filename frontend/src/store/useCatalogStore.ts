/**
 * Zustand store for device catalog management
 * Handles DeviceTypes, Brands, Models, and DCIM Connections
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type {
  DeviceTypeResponse,
  DeviceTypeCreate,
  DeviceTypeUpdate,
  DeviceTypeFilters,
  BrandResponse,
  BrandCreate,
  BrandUpdate,
  BrandFilters,
  ModelResponse,
  ModelCreate,
  ModelUpdate,
  ModelFilters,
  DCIMConnectionResponse,
  DCIMConnectionCreate,
  DCIMConnectionUpdate,
  DCIMConnectionTestResult,
  DCIMConnectionFilters,
  PaginationMetadata,
} from '../types/catalog';
import { catalogAPI, getCatalogErrorMessage } from '../lib/api-catalog';

// ============================================================================
// State Interface
// ============================================================================

interface CatalogState {
  // ==================== Device Types ====================
  deviceTypes: DeviceTypeResponse[];
  deviceTypesLoading: boolean;
  deviceTypesError: string | null;
  deviceTypesPagination: PaginationMetadata | null;

  // ==================== Brands ====================
  brands: BrandResponse[];
  brandsLoading: boolean;
  brandsError: string | null;
  brandsPagination: PaginationMetadata | null;

  // ==================== Models ====================
  models: ModelResponse[];
  modelsLoading: boolean;
  modelsError: string | null;
  modelsPagination: PaginationMetadata | null;

  // ==================== DCIM Connections ====================
  dcimConnections: DCIMConnectionResponse[];
  dcimConnectionsLoading: boolean;
  dcimConnectionsError: string | null;
  dcimConnectionsPagination: PaginationMetadata | null;

  // ==================== Actions ====================

  // Device Types
  fetchDeviceTypes: (filters?: DeviceTypeFilters) => Promise<void>;
  getDeviceType: (id: number) => Promise<DeviceTypeResponse>;
  createDeviceType: (data: DeviceTypeCreate) => Promise<DeviceTypeResponse>;
  updateDeviceType: (id: number, data: DeviceTypeUpdate) => Promise<DeviceTypeResponse>;
  deleteDeviceType: (id: number) => Promise<void>;

  // Brands
  fetchBrands: (filters?: BrandFilters) => Promise<void>;
  getBrand: (id: number) => Promise<BrandResponse>;
  createBrand: (data: BrandCreate) => Promise<BrandResponse>;
  updateBrand: (id: number, data: BrandUpdate) => Promise<BrandResponse>;
  deleteBrand: (id: number) => Promise<void>;
  fetchBrandInfo: (brandName: string) => Promise<BrandResponse>;
  validateBrand: (id: number) => Promise<any>;

  // Models
  fetchModels: (filters?: ModelFilters) => Promise<void>;
  getModel: (id: number) => Promise<ModelResponse>;
  searchModels: (query: string, filters?: ModelFilters) => Promise<ModelResponse[]>;
  createModel: (data: ModelCreate) => Promise<ModelResponse>;
  updateModel: (id: number, data: ModelUpdate) => Promise<ModelResponse>;
  deleteModel: (id: number) => Promise<void>;
  fetchModelSpecs: (brand: string, model: string) => Promise<ModelResponse>;
  importModels: (connectionId: number, modelIds: number[]) => Promise<ModelResponse[]>;

  // DCIM Connections
  fetchDCIMConnections: (filters?: DCIMConnectionFilters) => Promise<void>;
  getDCIMConnection: (id: number) => Promise<DCIMConnectionResponse>;
  createDCIMConnection: (data: DCIMConnectionCreate) => Promise<DCIMConnectionResponse>;
  updateDCIMConnection: (
    id: number,
    data: DCIMConnectionUpdate
  ) => Promise<DCIMConnectionResponse>;
  deleteDCIMConnection: (id: number) => Promise<void>;
  testDCIMConnection: (id: number) => Promise<DCIMConnectionTestResult>;
  syncDCIMConnection: (id: number) => Promise<any>;

  // Utility
  clearErrors: () => void;
  reset: () => void;
}

// ============================================================================
// Initial State
// ============================================================================

const initialState = {
  deviceTypes: [],
  deviceTypesLoading: false,
  deviceTypesError: null,
  deviceTypesPagination: null,

  brands: [],
  brandsLoading: false,
  brandsError: null,
  brandsPagination: null,

  models: [],
  modelsLoading: false,
  modelsError: null,
  modelsPagination: null,

  dcimConnections: [],
  dcimConnectionsLoading: false,
  dcimConnectionsError: null,
  dcimConnectionsPagination: null,
};

// ============================================================================
// Store Implementation
// ============================================================================

export const useCatalogStore = create<CatalogState>()(
  devtools(
    (set, get) => ({
      ...initialState,

      // ==================== Device Types ====================

      fetchDeviceTypes: async (filters?: DeviceTypeFilters) => {
        set({ deviceTypesLoading: true, deviceTypesError: null });
        try {
          const response = await catalogAPI.getDeviceTypes(filters);
          set({
            deviceTypes: response.items,
            deviceTypesPagination: response.pagination,
            deviceTypesLoading: false,
          });
        } catch (error) {
          set({
            deviceTypesError: getCatalogErrorMessage(error),
            deviceTypesLoading: false,
          });
          throw error;
        }
      },

      getDeviceType: async (id: number) => {
        try {
          return await catalogAPI.getDeviceType(id);
        } catch (error) {
          set({ deviceTypesError: getCatalogErrorMessage(error) });
          throw error;
        }
      },

      createDeviceType: async (data: DeviceTypeCreate) => {
        set({ deviceTypesLoading: true, deviceTypesError: null });
        try {
          const newDeviceType = await catalogAPI.createDeviceType(data);
          set((state) => ({
            deviceTypes: [...state.deviceTypes, newDeviceType],
            deviceTypesLoading: false,
          }));
          return newDeviceType;
        } catch (error) {
          set({
            deviceTypesError: getCatalogErrorMessage(error),
            deviceTypesLoading: false,
          });
          throw error;
        }
      },

      updateDeviceType: async (id: number, data: DeviceTypeUpdate) => {
        set({ deviceTypesLoading: true, deviceTypesError: null });
        try {
          const updatedDeviceType = await catalogAPI.updateDeviceType(id, data);
          set((state) => ({
            deviceTypes: state.deviceTypes.map((dt) =>
              dt.id === id ? updatedDeviceType : dt
            ),
            deviceTypesLoading: false,
          }));
          return updatedDeviceType;
        } catch (error) {
          set({
            deviceTypesError: getCatalogErrorMessage(error),
            deviceTypesLoading: false,
          });
          throw error;
        }
      },

      deleteDeviceType: async (id: number) => {
        set({ deviceTypesLoading: true, deviceTypesError: null });
        try {
          await catalogAPI.deleteDeviceType(id);
          set((state) => ({
            deviceTypes: state.deviceTypes.filter((dt) => dt.id !== id),
            deviceTypesLoading: false,
          }));
        } catch (error) {
          set({
            deviceTypesError: getCatalogErrorMessage(error),
            deviceTypesLoading: false,
          });
          throw error;
        }
      },

      // ==================== Brands ====================

      fetchBrands: async (filters?: BrandFilters) => {
        set({ brandsLoading: true, brandsError: null });
        try {
          const response = await catalogAPI.getBrands(filters);
          set({
            brands: response.items,
            brandsPagination: response.pagination,
            brandsLoading: false,
          });
        } catch (error) {
          set({
            brandsError: getCatalogErrorMessage(error),
            brandsLoading: false,
          });
          throw error;
        }
      },

      getBrand: async (id: number) => {
        try {
          return await catalogAPI.getBrand(id);
        } catch (error) {
          set({ brandsError: getCatalogErrorMessage(error) });
          throw error;
        }
      },

      createBrand: async (data: BrandCreate) => {
        set({ brandsLoading: true, brandsError: null });
        try {
          const newBrand = await catalogAPI.createBrand(data);
          set((state) => ({
            brands: [...state.brands, newBrand],
            brandsLoading: false,
          }));
          return newBrand;
        } catch (error) {
          set({
            brandsError: getCatalogErrorMessage(error),
            brandsLoading: false,
          });
          throw error;
        }
      },

      updateBrand: async (id: number, data: BrandUpdate) => {
        set({ brandsLoading: true, brandsError: null });
        try {
          const updatedBrand = await catalogAPI.updateBrand(id, data);
          set((state) => ({
            brands: state.brands.map((b) => (b.id === id ? updatedBrand : b)),
            brandsLoading: false,
          }));
          return updatedBrand;
        } catch (error) {
          set({
            brandsError: getCatalogErrorMessage(error),
            brandsLoading: false,
          });
          throw error;
        }
      },

      deleteBrand: async (id: number) => {
        set({ brandsLoading: true, brandsError: null });
        try {
          await catalogAPI.deleteBrand(id);
          set((state) => ({
            brands: state.brands.filter((b) => b.id !== id),
            brandsLoading: false,
          }));
        } catch (error) {
          set({
            brandsError: getCatalogErrorMessage(error),
            brandsLoading: false,
          });
          throw error;
        }
      },

      fetchBrandInfo: async (brandName: string) => {
        set({ brandsLoading: true, brandsError: null });
        try {
          const brand = await catalogAPI.fetchBrandInfo(brandName);
          set({ brandsLoading: false });
          return brand;
        } catch (error) {
          set({
            brandsError: getCatalogErrorMessage(error),
            brandsLoading: false,
          });
          throw error;
        }
      },

      validateBrand: async (id: number) => {
        set({ brandsLoading: true, brandsError: null });
        try {
          const result = await catalogAPI.validateBrand(id);
          set({ brandsLoading: false });
          return result;
        } catch (error) {
          set({
            brandsError: getCatalogErrorMessage(error),
            brandsLoading: false,
          });
          throw error;
        }
      },

      // ==================== Models ====================

      fetchModels: async (filters?: ModelFilters) => {
        set({ modelsLoading: true, modelsError: null });
        try {
          const response = await catalogAPI.getModels(filters);
          set({
            models: response.items,
            modelsPagination: response.pagination,
            modelsLoading: false,
          });
        } catch (error) {
          set({
            modelsError: getCatalogErrorMessage(error),
            modelsLoading: false,
          });
          throw error;
        }
      },

      getModel: async (id: number) => {
        try {
          return await catalogAPI.getModel(id);
        } catch (error) {
          set({ modelsError: getCatalogErrorMessage(error) });
          throw error;
        }
      },

      searchModels: async (query: string, filters?: ModelFilters) => {
        set({ modelsLoading: true, modelsError: null });
        try {
          const response = await catalogAPI.searchModels(query, filters);
          set({ modelsLoading: false });
          return response.items;
        } catch (error) {
          set({
            modelsError: getCatalogErrorMessage(error),
            modelsLoading: false,
          });
          throw error;
        }
      },

      createModel: async (data: ModelCreate) => {
        set({ modelsLoading: true, modelsError: null });
        try {
          const newModel = await catalogAPI.createModel(data);
          set((state) => ({
            models: [...state.models, newModel],
            modelsLoading: false,
          }));
          return newModel;
        } catch (error) {
          set({
            modelsError: getCatalogErrorMessage(error),
            modelsLoading: false,
          });
          throw error;
        }
      },

      updateModel: async (id: number, data: ModelUpdate) => {
        set({ modelsLoading: true, modelsError: null });
        try {
          const updatedModel = await catalogAPI.updateModel(id, data);
          set((state) => ({
            models: state.models.map((m) => (m.id === id ? updatedModel : m)),
            modelsLoading: false,
          }));
          return updatedModel;
        } catch (error) {
          set({
            modelsError: getCatalogErrorMessage(error),
            modelsLoading: false,
          });
          throw error;
        }
      },

      deleteModel: async (id: number) => {
        set({ modelsLoading: true, modelsError: null });
        try {
          await catalogAPI.deleteModel(id);
          set((state) => ({
            models: state.models.filter((m) => m.id !== id),
            modelsLoading: false,
          }));
        } catch (error) {
          set({
            modelsError: getCatalogErrorMessage(error),
            modelsLoading: false,
          });
          throw error;
        }
      },

      fetchModelSpecs: async (brand: string, model: string) => {
        set({ modelsLoading: true, modelsError: null });
        try {
          const modelData = await catalogAPI.fetchModelSpecs(brand, model);
          set({ modelsLoading: false });
          return modelData;
        } catch (error) {
          set({
            modelsError: getCatalogErrorMessage(error),
            modelsLoading: false,
          });
          throw error;
        }
      },

      importModels: async (connectionId: number, modelIds: number[]) => {
        set({ modelsLoading: true, modelsError: null });
        try {
          const importedModels = await catalogAPI.importModels(connectionId, modelIds);
          set((state) => ({
            models: [...state.models, ...importedModels],
            modelsLoading: false,
          }));
          return importedModels;
        } catch (error) {
          set({
            modelsError: getCatalogErrorMessage(error),
            modelsLoading: false,
          });
          throw error;
        }
      },

      // ==================== DCIM Connections ====================

      fetchDCIMConnections: async (filters?: DCIMConnectionFilters) => {
        set({ dcimConnectionsLoading: true, dcimConnectionsError: null });
        try {
          const response = await catalogAPI.getDCIMConnections(filters);
          set({
            dcimConnections: response.items,
            dcimConnectionsPagination: response.pagination,
            dcimConnectionsLoading: false,
          });
        } catch (error) {
          set({
            dcimConnectionsError: getCatalogErrorMessage(error),
            dcimConnectionsLoading: false,
          });
          throw error;
        }
      },

      getDCIMConnection: async (id: number) => {
        try {
          return await catalogAPI.getDCIMConnection(id);
        } catch (error) {
          set({ dcimConnectionsError: getCatalogErrorMessage(error) });
          throw error;
        }
      },

      createDCIMConnection: async (data: DCIMConnectionCreate) => {
        set({ dcimConnectionsLoading: true, dcimConnectionsError: null });
        try {
          const newConnection = await catalogAPI.createDCIMConnection(data);
          set((state) => ({
            dcimConnections: [...state.dcimConnections, newConnection],
            dcimConnectionsLoading: false,
          }));
          return newConnection;
        } catch (error) {
          set({
            dcimConnectionsError: getCatalogErrorMessage(error),
            dcimConnectionsLoading: false,
          });
          throw error;
        }
      },

      updateDCIMConnection: async (id: number, data: DCIMConnectionUpdate) => {
        set({ dcimConnectionsLoading: true, dcimConnectionsError: null });
        try {
          const updatedConnection = await catalogAPI.updateDCIMConnection(id, data);
          set((state) => ({
            dcimConnections: state.dcimConnections.map((c) =>
              c.id === id ? updatedConnection : c
            ),
            dcimConnectionsLoading: false,
          }));
          return updatedConnection;
        } catch (error) {
          set({
            dcimConnectionsError: getCatalogErrorMessage(error),
            dcimConnectionsLoading: false,
          });
          throw error;
        }
      },

      deleteDCIMConnection: async (id: number) => {
        set({ dcimConnectionsLoading: true, dcimConnectionsError: null });
        try {
          await catalogAPI.deleteDCIMConnection(id);
          set((state) => ({
            dcimConnections: state.dcimConnections.filter((c) => c.id !== id),
            dcimConnectionsLoading: false,
          }));
        } catch (error) {
          set({
            dcimConnectionsError: getCatalogErrorMessage(error),
            dcimConnectionsLoading: false,
          });
          throw error;
        }
      },

      testDCIMConnection: async (id: number) => {
        set({ dcimConnectionsLoading: true, dcimConnectionsError: null });
        try {
          const result = await catalogAPI.testDCIMConnection(id);
          set({ dcimConnectionsLoading: false });
          return result;
        } catch (error) {
          set({
            dcimConnectionsError: getCatalogErrorMessage(error),
            dcimConnectionsLoading: false,
          });
          throw error;
        }
      },

      syncDCIMConnection: async (id: number) => {
        set({ dcimConnectionsLoading: true, dcimConnectionsError: null });
        try {
          const result = await catalogAPI.syncDCIMConnection(id);
          set({ dcimConnectionsLoading: false });
          return result;
        } catch (error) {
          set({
            dcimConnectionsError: getCatalogErrorMessage(error),
            dcimConnectionsLoading: false,
          });
          throw error;
        }
      },

      // ==================== Utility ====================

      clearErrors: () => {
        set({
          deviceTypesError: null,
          brandsError: null,
          modelsError: null,
          dcimConnectionsError: null,
        });
      },

      reset: () => {
        set(initialState);
      },
    }),
    { name: 'CatalogStore' }
  )
);
