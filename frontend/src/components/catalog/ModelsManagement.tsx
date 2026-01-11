import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ModelCard } from './ModelCard';
import { ModelDialog } from './ModelDialog';
import { ModelFetchDialog } from './ModelFetchDialog';
import { Button } from '../ui/button';
import { useCatalogStore } from '../../store/useCatalogStore';
import type { ModelResponse, ModelFilters } from '../../types/catalog';
import {
  Plus,
  Download,
  Database,
  AlertCircle,
} from 'lucide-react';
import {
  SearchFilterBar,
  PaginationControls,
  EmptyState,
  ConfirmDialog,
} from './shared';

export const ModelsManagement: React.FC = () => {
  const {
    models,
    brands,
    deviceTypes,
    modelsLoading,
    modelsError,
    modelsPagination,
    fetchModels,
    fetchBrands,
    fetchDeviceTypes,
    deleteModel,
  } = useCatalogStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedBrandId, setSelectedBrandId] = useState<number | undefined>(undefined);
  const [selectedDeviceTypeId, setSelectedDeviceTypeId] = useState<number | undefined>(undefined);
  const [currentPage, setCurrentPage] = useState(1);

  // Dialog states
  const [isModelDialogOpen, setIsModelDialogOpen] = useState(false);
  const [isFetchDialogOpen, setIsFetchDialogOpen] = useState(false);
  const [editingModel, setEditingModel] = useState<ModelResponse | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<ModelResponse | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const pageSize = 12;

  // Load initial data
  useEffect(() => {
    fetchBrands({ page_size: 1000 });
    fetchDeviceTypes({ page_size: 1000 });
  }, [fetchBrands, fetchDeviceTypes]);

  // Fetch models when filters change
  useEffect(() => {
    const filters: ModelFilters = {
      page: currentPage,
      page_size: pageSize,
    };

    if (searchQuery.trim()) {
      filters.search = searchQuery;
    }
    if (selectedBrandId) {
      filters.brand_id = selectedBrandId;
    }
    if (selectedDeviceTypeId) {
      filters.device_type_id = selectedDeviceTypeId;
    }

    fetchModels(filters);
  }, [searchQuery, selectedBrandId, selectedDeviceTypeId, currentPage, fetchModels]);

  const handleAddModel = () => {
    setEditingModel(null);
    setIsModelDialogOpen(true);
  };

  const handleEditModel = (model: ModelResponse) => {
    setEditingModel(model);
    setIsModelDialogOpen(true);
  };

  const handleDeleteModel = (model: ModelResponse) => {
    setDeleteTarget(model);
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;

    setIsDeleting(true);
    try {
      await deleteModel(deleteTarget.id);
      // Refresh current page
      fetchModels({
        page: currentPage,
        page_size: pageSize,
        search: searchQuery || undefined,
        brand_id: selectedBrandId,
        device_type_id: selectedDeviceTypeId,
      });
      setDeleteTarget(null);
    } catch (error) {
      console.error('Failed to delete model:', error);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDialogSuccess = () => {
    // Refresh models list
    fetchModels({
      page: currentPage,
      page_size: pageSize,
      search: searchQuery || undefined,
      brand_id: selectedBrandId,
      device_type_id: selectedDeviceTypeId,
    });
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedBrandId(undefined);
    setSelectedDeviceTypeId(undefined);
    setCurrentPage(1);
  };

  const hasActiveFilters = searchQuery || selectedBrandId || selectedDeviceTypeId;

  const totalPages = modelsPagination?.total_pages || 1;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-6"
    >
      {/* Header Actions */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Search and Filters */}
        <div className="flex-1">
          <SearchFilterBar
            searchValue={searchQuery}
            onSearchChange={(value) => {
              setSearchQuery(value);
              setCurrentPage(1);
            }}
            searchPlaceholder="Search models by name, brand, or specifications..."
            filters={[
              {
                id: 'brand',
                label: 'Brand',
                value: selectedBrandId?.toString() || 'all',
                options: brands.map((brand) => ({
                  value: brand.id.toString(),
                  label: brand.name,
                })),
              },
              {
                id: 'deviceType',
                label: 'Device Type',
                value: selectedDeviceTypeId?.toString() || 'all',
                options: deviceTypes.map((type) => ({
                  value: type.id.toString(),
                  label: `${type.icon} ${type.name}`,
                })),
              },
            ]}
            onFilterChange={(filterId, value) => {
              if (filterId === 'brand') {
                setSelectedBrandId(value === 'all' ? undefined : parseInt(value));
                setCurrentPage(1);
              } else if (filterId === 'deviceType') {
                setSelectedDeviceTypeId(value === 'all' ? undefined : parseInt(value));
                setCurrentPage(1);
              }
            }}
            onClearFilters={clearFilters}
          />
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="md"
            onClick={() => setIsFetchDialogOpen(true)}
            leftIcon={<Download className="w-4 h-4" />}
          >
            Fetch Specs
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={handleAddModel}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Add Model
          </Button>
        </div>
      </div>

      {/* Results Count */}
      {modelsPagination && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <div>
            Showing {models.length > 0 ? (currentPage - 1) * pageSize + 1 : 0} -{' '}
            {Math.min(currentPage * pageSize, modelsPagination.total)} of{' '}
            {modelsPagination.total} models
          </div>
          {hasActiveFilters && (
            <div className="text-electric">
              {modelsPagination.total} filtered results
            </div>
          )}
        </div>
      )}

      {/* Error State */}
      {modelsError && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-400 mb-1">Error loading models</p>
            <p className="text-xs text-red-400/80">{modelsError}</p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {modelsLoading && models.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-electric border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-sm text-muted-foreground">Loading models...</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!modelsLoading && models.length === 0 && !modelsError && (
        <EmptyState
          icon={Database}
          title="No models found"
          description={
            hasActiveFilters
              ? 'Try adjusting your filters or search criteria'
              : 'Get started by adding your first device model'
          }
          variant={hasActiveFilters ? 'no-results' : 'no-data'}
          actionButton={
            !hasActiveFilters
              ? {
                  label: 'Add Model',
                  onClick: handleAddModel,
                  icon: Plus,
                }
              : undefined
          }
        />
      )}

      {/* Models Grid */}
      {!modelsLoading && models.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {models.map((model) => (
            <ModelCard
              key={model.id}
              model={model}
              onEdit={handleEditModel}
              onDelete={handleDeleteModel}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {!modelsLoading && models.length > 0 && totalPages > 1 && modelsPagination && (
        <PaginationControls
          currentPage={currentPage}
          totalPages={totalPages}
          totalItems={modelsPagination.total}
          pageSize={pageSize}
          onPageChange={setCurrentPage}
          className="pt-4 border-t border-border"
        />
      )}

      {/* Dialogs */}
      <ModelDialog
        isOpen={isModelDialogOpen}
        onClose={() => {
          setIsModelDialogOpen(false);
          setEditingModel(null);
        }}
        model={editingModel}
        onSuccess={handleDialogSuccess}
      />

      <ModelFetchDialog
        isOpen={isFetchDialogOpen}
        onClose={() => setIsFetchDialogOpen(false)}
        onSuccess={handleDialogSuccess}
      />

      <ConfirmDialog
        isOpen={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
        title="Delete Model?"
        message={`Are you sure you want to delete "${deleteTarget?.brand.name} ${deleteTarget?.name}"? This action cannot be undone.`}
        confirmText="Delete"
        variant="danger"
        isLoading={isDeleting}
      />
    </motion.div>
  );
};
