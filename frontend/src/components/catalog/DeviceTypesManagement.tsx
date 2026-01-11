import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Search, AlertCircle, Database, Loader2 } from 'lucide-react';
import { Button } from '../ui/button';
import { DeviceTypeCard } from './DeviceTypeCard';
import { DeviceTypeDialog } from './DeviceTypeDialog';
import { useCatalogStore } from '../../store/useCatalogStore';
import { useStore } from '../../store/useStore';
import type { DeviceTypeResponse, DeviceTypeCreate, DeviceTypeUpdate } from '../../types/catalog';
import {
  StatsDashboard,
  SearchFilterBar,
  EmptyState,
  ConfirmDialog,
} from './shared';

export const DeviceTypesManagement: React.FC = () => {
  const {
    deviceTypes,
    deviceTypesLoading,
    deviceTypesError,
    fetchDeviceTypes,
    createDeviceType,
    updateDeviceType,
    deleteDeviceType,
  } = useCatalogStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');
  const [selectedDeviceType, setSelectedDeviceType] = useState<DeviceTypeResponse | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<DeviceTypeResponse | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const addToast = useStore((state) => state.addToast);

  useEffect(() => {
    fetchDeviceTypes();
  }, [fetchDeviceTypes]);

  // Filter device types by search query
  const filteredDeviceTypes = useMemo(() => {
    if (!searchQuery.trim()) return deviceTypes;

    const query = searchQuery.toLowerCase();
    return deviceTypes.filter(
      (dt) =>
        dt.name.toLowerCase().includes(query) ||
        dt.slug.toLowerCase().includes(query) ||
        dt.description?.toLowerCase().includes(query)
    );
  }, [deviceTypes, searchQuery]);

  const handleCreate = () => {
    setSelectedDeviceType(null);
    setDialogMode('create');
    setDialogOpen(true);
  };

  const handleEdit = (deviceType: DeviceTypeResponse) => {
    setSelectedDeviceType(deviceType);
    setDialogMode('edit');
    setDialogOpen(true);
  };

  const handleDelete = (deviceType: DeviceTypeResponse) => {
    setDeleteTarget(deviceType);
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;

    setIsDeleting(true);
    try {
      await deleteDeviceType(deleteTarget.id);
      addToast({
        type: 'success',
        title: 'Device type deleted',
        description: `${deleteTarget.name} has been removed successfully`,
      });
      setDeleteTarget(null);
    } catch (error) {
      addToast({
        type: 'error',
        title: 'Failed to delete device type',
        description: error instanceof Error ? error.message : 'An error occurred',
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const handleSave = async (data: DeviceTypeCreate | DeviceTypeUpdate) => {
    try {
      if (dialogMode === 'create') {
        await createDeviceType(data as DeviceTypeCreate);
        addToast({
          type: 'success',
          title: 'Device type created',
          description: `${data.name} has been added successfully`,
        });
      } else if (selectedDeviceType) {
        await updateDeviceType(selectedDeviceType.id, data as DeviceTypeUpdate);
        addToast({
          type: 'success',
          title: 'Device type updated',
          description: `${data.name} has been updated successfully`,
        });
      }
      setDialogOpen(false);
    } catch (error) {
      addToast({
        type: 'error',
        title: `Failed to ${dialogMode} device type`,
        description: error instanceof Error ? error.message : 'An error occurred',
      });
      throw error;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-foreground">Device Types</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Manage device categories and their visual appearance
          </p>
        </div>
        <Button
          variant="primary"
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={handleCreate}
        >
          Add Device Type
        </Button>
      </div>

      {/* Search Bar */}
      <SearchFilterBar
        searchValue={searchQuery}
        onSearchChange={setSearchQuery}
        searchPlaceholder="Search device types by name, slug, or description..."
        onClearFilters={() => setSearchQuery('')}
      />

      {/* Stats */}
      <StatsDashboard
        stats={[
          {
            icon: Database,
            label: 'Total Types',
            value: deviceTypes.length,
            color: '#00eaff',
          },
          {
            icon: Database,
            label: 'Total Models',
            value: deviceTypes.reduce((sum, dt) => sum + dt.model_count, 0),
            color: '#00eaff',
          },
          {
            icon: Search,
            label: 'Filtered Results',
            value: filteredDeviceTypes.length,
            color: '#00eaff',
          },
        ]}
        columns={3}
      />

      {/* Error Message */}
      {deviceTypesError && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3"
        >
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="font-medium text-red-500 mb-1">Error Loading Device Types</h4>
            <p className="text-sm text-red-400">{deviceTypesError}</p>
          </div>
        </motion.div>
      )}

      {/* Loading State */}
      {deviceTypesLoading && deviceTypes.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12">
          <Loader2 className="w-12 h-12 text-electric animate-spin mb-4" />
          <p className="text-sm text-muted-foreground">Loading device types...</p>
        </div>
      )}

      {/* Empty State */}
      {!deviceTypesLoading && filteredDeviceTypes.length === 0 && (
        <EmptyState
          icon={Database}
          title={searchQuery ? 'No device types found' : 'No device types yet'}
          description={
            searchQuery
              ? 'Try adjusting your search criteria'
              : 'Get started by creating your first device type category'
          }
          variant={searchQuery ? 'no-results' : 'no-data'}
          actionButton={
            !searchQuery
              ? {
                  label: 'Add Your First Device Type',
                  onClick: handleCreate,
                  icon: Plus,
                }
              : undefined
          }
        />
      )}

      {/* Device Types Grid */}
      {!deviceTypesLoading && filteredDeviceTypes.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          <AnimatePresence mode="popLayout">
            {filteredDeviceTypes.map((deviceType) => (
              <DeviceTypeCard
                key={deviceType.id}
                deviceType={deviceType}
                onEdit={handleEdit}
                onDelete={() => handleDelete(deviceType)}
              />
            ))}
          </AnimatePresence>
        </motion.div>
      )}

      {/* Info Box */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="p-4 bg-muted/30 border border-border rounded-lg flex items-start gap-3"
      >
        <AlertCircle className="w-5 h-5 text-muted-foreground mt-0.5 flex-shrink-0" />
        <div>
          <h4 className="font-medium text-foreground mb-1">About Device Types</h4>
          <p className="text-sm text-muted-foreground">
            Device types are categories used to organize your equipment models (e.g., Servers, Switches, Routers).
            Each type can have a custom icon, color, and description for easy identification. The model count shows
            how many equipment models are associated with each type.
          </p>
        </div>
      </motion.div>

      {/* Dialogs */}
      <DeviceTypeDialog
        isOpen={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSave={handleSave}
        deviceType={selectedDeviceType}
        mode={dialogMode}
      />

      <ConfirmDialog
        isOpen={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleConfirmDelete}
        title="Delete Device Type?"
        message={`Are you sure you want to delete "${deleteTarget?.name}"? This action cannot be undone.${
          deleteTarget && deleteTarget.model_count > 0
            ? ` This device type has ${deleteTarget.model_count} associated model(s).`
            : ''
        }`}
        confirmText="Delete"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  );
};
