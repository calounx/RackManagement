import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Globe, AlertCircle, Loader2, Package } from 'lucide-react';
import { Button } from '../ui/button';
import { BrandCard } from './BrandCard';
import { BrandDialog } from './BrandDialog';
import { BrandFetchDialog } from './BrandFetchDialog';
import type { BrandResponse } from '../../types/catalog';
import { useCatalogStore } from '../../store/useCatalogStore';
import { getCatalogErrorMessage } from '../../lib/api-catalog';
// import { cn } from '../../lib/utils'; // Removed unused import
import { useStore } from '../../store/useStore';
import {
  SearchFilterBar,
  PaginationControls,
  EmptyState,
  ConfirmDialog,
} from './shared';

export const BrandsManagement: React.FC = () => {
  const {
    brands,
    brandsLoading,
    brandsError,
    brandsPagination,
    fetchBrands,
    deleteBrand,
    fetchDeviceTypes,
    deviceTypes,
  } = useCatalogStore();

  const addToast = useStore((state) => state.addToast);

  // Dialog states
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isFetchDialogOpen, setIsFetchDialogOpen] = useState(false);
  const [editingBrand, setEditingBrand] = useState<BrandResponse | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<BrandResponse | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDeviceTypeId, setSelectedDeviceTypeId] = useState<number | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 12;

  // Load brands and device types on mount
  useEffect(() => {
    loadBrands();
    fetchDeviceTypes();
  }, []);

  // Reload when filters change
  useEffect(() => {
    loadBrands();
  }, [searchQuery, selectedDeviceTypeId, currentPage]);

  const loadBrands = async () => {
    try {
      await fetchBrands({
        search: searchQuery || undefined,
        device_type_id: selectedDeviceTypeId || undefined,
        page: currentPage,
        page_size: pageSize,
      });
    } catch (error) {
      console.error('Failed to load brands:', error);
    }
  };

  // Filter brands on client side for instant feedback
  const filteredBrands = useMemo(() => {
    return brands.filter((brand) => {
      const matchesSearch =
        !searchQuery ||
        brand.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        brand.slug.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesSearch;
    });
  }, [brands, searchQuery]);

  const handleEdit = (brand: BrandResponse) => {
    setEditingBrand(brand);
  };

  const handleDelete = (brand: BrandResponse) => {
    setDeleteTarget(brand);
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;

    setIsDeleting(true);
    try {
      await deleteBrand(deleteTarget.id);
      addToast({
        type: 'success',
        title: 'Brand deleted',
        description: `${deleteTarget.name} has been removed successfully`,
      });
      await loadBrands();
      setDeleteTarget(null);
    } catch (error) {
      const errorMsg = getCatalogErrorMessage(error);
      addToast({
        type: 'error',
        title: 'Failed to delete brand',
        description: errorMsg.toLowerCase().includes('models')
          ? `Cannot delete ${deleteTarget.name} because it has associated models. Delete the models first.`
          : errorMsg,
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const handleViewModels = (brand: BrandResponse) => {
    // TODO: Navigate to models page with brand filter
    console.log('View models for brand:', brand.name);
    addToast({
      type: 'info',
      title: 'Feature coming soon',
      description: `Models view for "${brand.name}" will be available soon`,
    });
  };

  const handleSuccess = () => {
    loadBrands();
  };

  const handleClearFilters = () => {
    setSearchQuery('');
    setSelectedDeviceTypeId(null);
    setCurrentPage(1);
  };

  const hasActiveFilters = searchQuery || selectedDeviceTypeId !== null;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-foreground">Brands</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Manage device manufacturers and their catalogs
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              onClick={() => setIsFetchDialogOpen(true)}
              leftIcon={<Globe className="w-4 h-4" />}
            >
              Fetch from Web
            </Button>
            <Button
              variant="primary"
              onClick={() => setIsAddDialogOpen(true)}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              Add Brand
            </Button>
          </div>
        </div>

        {/* Search and Filters */}
        <SearchFilterBar
          searchValue={searchQuery}
          onSearchChange={(value) => {
            setSearchQuery(value);
            setCurrentPage(1);
          }}
          searchPlaceholder="Search brands by name or slug..."
          filters={[
            {
              id: 'deviceType',
              label: 'Device Type',
              value: selectedDeviceTypeId?.toString() || 'all',
              options: deviceTypes.map((type) => ({
                value: type.id.toString(),
                label: type.name,
              })),
            },
          ]}
          onFilterChange={(filterId, value) => {
            if (filterId === 'deviceType') {
              setSelectedDeviceTypeId(value === 'all' ? null : parseInt(value));
              setCurrentPage(1);
            }
          }}
          onClearFilters={handleClearFilters}
        />

        {/* Results Count */}
        <div className="flex items-center justify-between mt-4">
          <p className="text-sm text-muted-foreground">
            {brandsLoading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Loading brands...
              </span>
            ) : (
              <>
                Showing {filteredBrands.length} of {brandsPagination?.total || 0} brands
                {hasActiveFilters && ' (filtered)'}
              </>
            )}
          </p>
        </div>
      </div>

      {/* Error Display */}
      {brandsError && (
        <div className="mb-4 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-red-400 mb-1">Error Loading Brands</h4>
            <p className="text-sm text-red-300">{brandsError}</p>
          </div>
        </div>
      )}

      {/* Brands Grid */}
      <div className="flex-1 overflow-y-auto">
        {brandsLoading && brands.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <Loader2 className="w-12 h-12 text-electric mx-auto mb-4 animate-spin" />
              <p className="text-sm text-muted-foreground">Loading brands...</p>
            </div>
          </div>
        ) : filteredBrands.length === 0 ? (
          <EmptyState
            icon={Package}
            title="No Brands Found"
            description={
              hasActiveFilters
                ? 'Try adjusting your search or filters to find what you are looking for.'
                : 'Get started by adding your first brand to the catalog.'
            }
            variant={hasActiveFilters ? 'no-results' : 'no-data'}
            actionButton={
              !hasActiveFilters
                ? {
                    label: 'Add Brand',
                    onClick: () => setIsAddDialogOpen(true),
                    icon: Plus,
                  }
                : undefined
            }
          />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <AnimatePresence mode="popLayout">
              {filteredBrands.map((brand) => (
                <motion.div
                  key={brand.id}
                  layout
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ duration: 0.2 }}
                >
                  <BrandCard
                    brand={brand}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                    onViewModels={handleViewModels}
                  />
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>

      {/* Pagination */}
      {brandsPagination && brandsPagination.total_pages > 1 && (
        <PaginationControls
          currentPage={currentPage}
          totalPages={brandsPagination.total_pages}
          totalItems={brandsPagination.total}
          pageSize={pageSize}
          onPageChange={setCurrentPage}
          className="mt-6 pt-4 border-t border-border"
        />
      )}

      {/* Dialogs */}
      <BrandDialog
        isOpen={isAddDialogOpen}
        onClose={() => setIsAddDialogOpen(false)}
        onSuccess={handleSuccess}
      />

      <BrandDialog
        isOpen={!!editingBrand}
        onClose={() => setEditingBrand(null)}
        brand={editingBrand}
        onSuccess={handleSuccess}
      />

      <BrandFetchDialog
        isOpen={isFetchDialogOpen}
        onClose={() => setIsFetchDialogOpen(false)}
        onSuccess={handleSuccess}
      />

      <ConfirmDialog
        isOpen={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
        title="Delete Brand?"
        message={`Are you sure you want to delete "${deleteTarget?.name}"? This action cannot be undone.${
          deleteTarget && deleteTarget.model_count > 0
            ? ` This brand has ${deleteTarget.model_count} associated model(s).`
            : ''
        }`}
        confirmText="Delete"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  );
};
