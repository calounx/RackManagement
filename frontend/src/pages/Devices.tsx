import React, { useEffect, useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useStore } from '../store/useStore';
import { DeviceCard } from '../components/devices/DeviceCard';
import { DeviceDialog } from '../components/devices/DeviceDialog';
import { Button } from '../components/ui/button';
import { Dialog, DialogFooter } from '../components/ui/dialog';
import { Card } from '../components/ui/card';
import { Input } from '../components/ui/input';
import type { Device } from '../types';
import {
  Plus,
  Server,
  Search,
  SlidersHorizontal,
  ArrowUpDown,
  Grid3x3,
  List,
  X,
} from 'lucide-react';
import { formatDeviceType } from '../lib/device-icons';

export const Devices: React.FC = () => {
  const { devices, fetchDevices, createDevice, updateDevice, deleteDevice } = useStore();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');
  const [editingDevice, setEditingDevice] = useState<Device | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deviceToDelete, setDeviceToDelete] = useState<Device | null>(null);

  // Filter and sort state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'name' | 'type' | 'status' | 'power'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  useEffect(() => {
    fetchDevices();
  }, []);

  // Filter and sort devices
  const filteredAndSortedDevices = useMemo(() => {
    let filtered = [...devices];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (device) =>
          device.name.toLowerCase().includes(query) ||
          device.manufacturer.toLowerCase().includes(query) ||
          device.model.toLowerCase().includes(query) ||
          device.device_type.toLowerCase().includes(query)
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter((device) => device.status === statusFilter);
    }

    // Type filter
    if (typeFilter !== 'all') {
      filtered = filtered.filter((device) => device.device_type === typeFilter);
    }

    // Sort
    filtered.sort((a, b) => {
      let aValue: string | number = '';
      let bValue: string | number = '';

      if (sortBy === 'name') {
        aValue = a.name.toLowerCase();
        bValue = b.name.toLowerCase();
      } else if (sortBy === 'type') {
        aValue = a.device_type.toLowerCase();
        bValue = b.device_type.toLowerCase();
      } else if (sortBy === 'status') {
        aValue = a.status.toLowerCase();
        bValue = b.status.toLowerCase();
      } else if (sortBy === 'power') {
        aValue = a.power_consumption_watts;
        bValue = b.power_consumption_watts;
      }

      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [devices, searchQuery, statusFilter, typeFilter, sortBy, sortOrder]);

  // Get unique device types and statuses
  const deviceTypes = useMemo(() => {
    const types = new Set(devices.map((d) => d.device_type));
    return Array.from(types);
  }, [devices]);

  const deviceStatuses = useMemo(() => {
    const statuses = new Set(devices.map((d) => d.status));
    return Array.from(statuses);
  }, [devices]);

  const handleAddDevice = () => {
    setDialogMode('create');
    setEditingDevice(null);
    setDialogOpen(true);
  };

  const handleEditDevice = (device: Device) => {
    setDialogMode('edit');
    setEditingDevice(device);
    setDialogOpen(true);
  };

  const handleDeleteDevice = (device: Device) => {
    setDeviceToDelete(device);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (deviceToDelete) {
      await deleteDevice(deviceToDelete.id);
      setDeleteDialogOpen(false);
      setDeviceToDelete(null);
      await fetchDevices();
    }
  };

  const handleSaveDevice = async (data: any) => {
    if (dialogMode === 'create') {
      await createDevice(data);
    } else if (editingDevice) {
      await updateDevice(editingDevice.id, data);
    }
    await fetchDevices();
  };

  const clearFilters = () => {
    setSearchQuery('');
    setStatusFilter('all');
    setTypeFilter('all');
  };

  const hasActiveFilters = searchQuery || statusFilter !== 'all' || typeFilter !== 'all';

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-lg glass border border-electric/30 shadow-lg shadow-electric/20">
            <Server className="h-8 w-8 text-electric" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-foreground">Device Library</h1>
            <p className="text-muted-foreground text-sm mt-1">
              Manage your hardware inventory ({devices.length} devices)
            </p>
          </div>
        </div>
        <Button variant="primary" onClick={handleAddDevice} className="gap-2">
          <Plus className="w-5 h-5" />
          Add Device
        </Button>
      </div>

      {devices.length === 0 ? (
        <Card className="p-16 text-center glass border-2 border-dashed border-border">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
          >
            <div className="p-6 rounded-full glass border border-electric/30 w-32 h-32 mx-auto flex items-center justify-center shadow-lg shadow-electric/10">
              <Server className="w-20 h-20 text-electric/50" />
            </div>
            <h3 className="text-2xl font-bold text-foreground mt-6">No devices yet</h3>
            <p className="text-muted-foreground mt-2 max-w-md mx-auto">
              Get started by adding your first device. You can manually create devices or fetch specifications from our database.
            </p>
            <Button variant="primary" size="lg" className="mt-8 gap-2" onClick={handleAddDevice}>
              <Plus className="w-5 h-5" />
              Add First Device
            </Button>
          </motion.div>
        </Card>
      ) : (
        <>
          {/* Filter Bar */}
          <Card className="p-4 glass border border-electric/20">
            <div className="flex flex-col gap-4">
              {/* Search and View Mode */}
              <div className="flex items-center gap-3">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="Search devices by name, manufacturer, model, or type..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 pr-10"
                  />
                  {searchQuery && (
                    <button
                      onClick={() => setSearchQuery('')}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>

                {/* View Mode Toggle */}
                <div className="flex items-center gap-1 glass rounded-lg p-1 border border-border">
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`p-2 rounded transition-colors ${
                      viewMode === 'grid'
                        ? 'bg-electric/20 text-electric'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                    title="Grid view"
                  >
                    <Grid3x3 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => setViewMode('list')}
                    className={`p-2 rounded transition-colors ${
                      viewMode === 'list'
                        ? 'bg-electric/20 text-electric'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                    title="List view"
                  >
                    <List className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Filters and Sort */}
              <div className="flex items-center gap-3 flex-wrap">
                <div className="flex items-center gap-2">
                  <SlidersHorizontal className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium text-muted-foreground">Filters:</span>
                </div>

                {/* Status Filter */}
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-3 py-1.5 rounded-lg glass border border-border text-sm font-medium focus:outline-none focus:ring-2 focus:ring-electric/50"
                >
                  <option value="all">All Status</option>
                  {deviceStatuses.map((status) => (
                    <option key={status} value={status}>
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </option>
                  ))}
                </select>

                {/* Type Filter */}
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="px-3 py-1.5 rounded-lg glass border border-border text-sm font-medium focus:outline-none focus:ring-2 focus:ring-electric/50"
                >
                  <option value="all">All Types</option>
                  {deviceTypes.map((type) => (
                    <option key={type} value={type}>
                      {formatDeviceType(type)}
                    </option>
                  ))}
                </select>

                {/* Sort */}
                <div className="flex items-center gap-2 ml-auto">
                  <ArrowUpDown className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium text-muted-foreground">Sort:</span>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as any)}
                    className="px-3 py-1.5 rounded-lg glass border border-border text-sm font-medium focus:outline-none focus:ring-2 focus:ring-electric/50"
                  >
                    <option value="name">Name</option>
                    <option value="type">Type</option>
                    <option value="status">Status</option>
                    <option value="power">Power</option>
                  </select>
                  <button
                    onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                    className="p-1.5 rounded-lg glass border border-border hover:border-electric/30 transition-colors"
                    title={`Sort ${sortOrder === 'asc' ? 'descending' : 'ascending'}`}
                  >
                    <ArrowUpDown className={`h-4 w-4 ${sortOrder === 'desc' ? 'rotate-180' : ''} transition-transform`} />
                  </button>
                </div>

                {/* Clear Filters */}
                {hasActiveFilters && (
                  <Button variant="ghost" size="sm" onClick={clearFilters} className="gap-2">
                    <X className="h-4 w-4" />
                    Clear Filters
                  </Button>
                )}
              </div>

              {/* Results Count */}
              <div className="text-sm text-muted-foreground">
                Showing {filteredAndSortedDevices.length} of {devices.length} devices
              </div>
            </div>
          </Card>

          {/* Device Grid */}
          {filteredAndSortedDevices.length === 0 ? (
            <Card className="p-12 text-center">
              <Server className="w-16 h-16 mx-auto text-muted-foreground opacity-50" />
              <h3 className="text-xl font-semibold text-foreground mt-4">No devices found</h3>
              <p className="text-muted-foreground mt-2">
                Try adjusting your filters or search query
              </p>
              <Button variant="outline" className="mt-6 gap-2" onClick={clearFilters}>
                <X className="h-4 w-4" />
                Clear Filters
              </Button>
            </Card>
          ) : (
            <div className={`grid gap-4 ${
              viewMode === 'grid'
                ? 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
                : 'grid-cols-1'
            }`}>
              {filteredAndSortedDevices.map((device, index) => (
                <motion.div
                  key={device.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2, delay: index * 0.03 }}
                >
                  <DeviceCard
                    device={device}
                    onEdit={handleEditDevice}
                    onDelete={handleDeleteDevice}
                  />
                </motion.div>
              ))}
            </div>
          )}
        </>
      )}

      <DeviceDialog
        isOpen={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSave={handleSaveDevice}
        device={editingDevice}
        mode={dialogMode}
      />

      <Dialog
        isOpen={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        title="Delete Device"
        description={`Are you sure you want to delete "${deviceToDelete?.name}"? This action cannot be undone.`}
      >
        <DialogFooter>
          <Button variant="ghost" onClick={() => setDeleteDialogOpen(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={confirmDelete}>
            Delete Device
          </Button>
        </DialogFooter>
      </Dialog>
    </div>
  );
};
