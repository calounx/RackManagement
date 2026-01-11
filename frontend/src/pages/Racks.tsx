import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useStore } from '../store/useStore';
import { RackVisualizer } from '../components/rack/RackVisualizer';
import { RackDialog } from '../components/rack/RackDialog';
import { DeviceAssignDialog } from '../components/rack/DeviceAssignDialog';
import { DeviceActionsMenu } from '../components/rack/DeviceActionsMenu';
import { Button } from '../components/ui/button';
import { IconButton } from '../components/ui/icon-button';
import { Card } from '../components/ui/card';
import { Dialog, DialogFooter } from '../components/ui/dialog';
import type { Device, Rack } from '../types';
import {
  Pencil,
  Trash2,
  Plus,
  Warehouse,
  MapPin,
  Boxes,
  BarChart3,
  CheckCircle2,
} from 'lucide-react';

export const Racks: React.FC = () => {
  const { racks, devices, fetchRacks, fetchDevices, selectedRackId, selectRack, createRack, updateRack, deleteRack } = useStore();
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');
  const [editingRack, setEditingRack] = useState<Rack | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [rackToDelete, setRackToDelete] = useState<Rack | null>(null);
  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [assignDialogUnit, setAssignDialogUnit] = useState<number | null>(null);
  const [deviceActionsOpen, setDeviceActionsOpen] = useState(false);

  useEffect(() => {
    fetchRacks();
    fetchDevices();
  }, []);

  const currentRack = racks.find((r) => r.id === selectedRackId) || racks[0];
  const rackDevices = devices.filter((d) => d.rack_id === currentRack?.id);

  const handleAddRack = () => {
    setDialogMode('create');
    setEditingRack(null);
    setDialogOpen(true);
  };

  const handleEditRack = (rack: Rack) => {
    setDialogMode('edit');
    setEditingRack(rack);
    setDialogOpen(true);
  };

  const handleDeleteRack = (rack: Rack) => {
    setRackToDelete(rack);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (rackToDelete) {
      await deleteRack(rackToDelete.id);
      setDeleteDialogOpen(false);
      setRackToDelete(null);
    }
  };

  const handleSaveRack = async (data: any) => {
    if (dialogMode === 'create') {
      await createRack(data);
    } else if (editingRack) {
      await updateRack(editingRack.id, data);
    }
    await fetchRacks();
  };

  const handleAddDevice = (unitNumber?: number) => {
    setAssignDialogUnit(unitNumber || null);
    setAssignDialogOpen(true);
  };

  const handleDeviceClick = (device: Device) => {
    setSelectedDevice(device);
    setDeviceActionsOpen(true);
  };

  const handleUnitClick = (unitNumber: number) => {
    handleAddDevice(unitNumber);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-lg glass border border-electric/30 shadow-lg shadow-electric/20">
            <Warehouse className="h-8 w-8 text-electric" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-foreground">Rack Management</h1>
            <p className="text-muted-foreground text-sm mt-1 flex items-center gap-2">
              <MapPin className="h-4 w-4" />
              Visualize and manage your server racks
            </p>
          </div>
        </div>
        <Button variant="primary" onClick={handleAddRack} className="gap-2">
          <Plus className="w-5 h-5" />
          Add Rack
        </Button>
      </div>

      {racks.length === 0 ? (
        <Card className="p-16 text-center glass border-2 border-dashed border-border">
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
          >
            <div className="p-6 rounded-full glass border border-electric/30 w-32 h-32 mx-auto flex items-center justify-center shadow-lg shadow-electric/10">
              <Warehouse className="w-20 h-20 text-electric/50" />
            </div>
            <h3 className="text-2xl font-bold text-foreground mt-6">No racks yet</h3>
            <p className="text-muted-foreground mt-2 max-w-md mx-auto">
              Get started by creating your first server rack. You'll be able to visualize and manage all your equipment in one place.
            </p>
            <Button variant="primary" size="lg" className="mt-8 gap-2" onClick={handleAddRack}>
              <Plus className="w-5 h-5" />
              Create First Rack
            </Button>
          </motion.div>
        </Card>
      ) : (
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-3">
            <Card className="p-5 glass border border-electric/20">
              <div className="flex items-center gap-2 mb-4">
                <Boxes className="h-5 w-5 text-electric" />
                <h3 className="font-bold text-foreground">Available Racks</h3>
                <div className="ml-auto px-2 py-0.5 rounded-full glass border border-electric/30 text-xs font-mono text-electric">
                  {racks.length}
                </div>
              </div>
              <div className="space-y-2">
                {racks.map((rack) => {
                  const rackDevices = devices.filter((d) => d.rack_id === rack.id && d.start_unit !== null);
                  const usedUnits = rackDevices.reduce((sum, d) => sum + d.height_units, 0);
                  const utilization = Math.round((usedUnits / rack.total_height_u) * 100);
                  const isSelected = currentRack?.id === rack.id;

                  return (
                    <div key={rack.id} className="relative group">
                      <motion.button
                        onClick={() => selectRack(rack.id)}
                        className={`w-full p-4 rounded-lg text-left transition-all border-2 ${
                          isSelected
                            ? 'bg-electric/10 border-electric shadow-lg shadow-electric/20'
                            : 'glass border-border hover:border-electric/30 hover:shadow-lg'
                        }`}
                        whileHover={{ scale: 1.02, y: -2 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        <div className="flex items-start gap-3 pr-16">
                          <div className={`p-2 rounded-lg glass border ${
                            isSelected ? 'border-electric/50' : 'border-border'
                          }`}>
                            <Warehouse className={`h-4 w-4 ${
                              isSelected ? 'text-electric' : 'text-muted-foreground'
                            }`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className={`font-semibold truncate ${
                              isSelected ? 'text-electric' : 'text-foreground'
                            }`}>
                              {rack.name}
                            </p>
                            <div className="flex items-center gap-1.5 mt-1">
                              <MapPin className="h-3 w-3 text-muted-foreground" />
                              <p className="text-xs text-muted-foreground font-mono truncate">
                                {rack.location}
                              </p>
                            </div>
                            <div className="flex items-center gap-2 mt-2">
                              <div className="flex items-center gap-1">
                                <BarChart3 className="h-3 w-3 text-muted-foreground" />
                                <span className="text-xs font-mono text-muted-foreground">
                                  {rackDevices.length} devices
                                </span>
                              </div>
                              <span className="text-muted-foreground">•</span>
                              <span className={`text-xs font-mono font-medium ${
                                utilization >= 90 ? 'text-red-500' : utilization >= 75 ? 'text-amber' : 'text-lime'
                              }`}>
                                {utilization}%
                              </span>
                            </div>
                          </div>
                        </div>
                        {isSelected && (
                          <div className="absolute right-4 top-4">
                            <CheckCircle2 className="h-5 w-5 text-electric" />
                          </div>
                        )}
                      </motion.button>
                      <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1 z-10">
                        <IconButton
                          icon={Pencil}
                          variant="outline"
                          size="sm"
                          tooltip="Edit Rack"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEditRack(rack);
                          }}
                        />
                        <IconButton
                          icon={Trash2}
                          variant="danger"
                          size="sm"
                          tooltip="Delete Rack"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteRack(rack);
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          </div>

          <div className="col-span-9">
            {currentRack && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-foreground">Rack Layout</h2>
                    <p className="text-sm text-muted-foreground">
                      Click empty units to add devices, or click existing devices to manage them
                    </p>
                  </div>
                  <Button variant="primary" onClick={() => handleAddDevice()}>
                    <Plus className="w-4 h-4" />
                    Add Device
                  </Button>
                </div>
                <RackVisualizer
                  rack={currentRack}
                  devices={rackDevices}
                  onDeviceClick={handleDeviceClick}
                  onUnitClick={handleUnitClick}
                />
              </div>
            )}
          </div>
        </div>
      )}

      <RackDialog
        isOpen={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSave={handleSaveRack}
        rack={editingRack}
        mode={dialogMode}
      />

      <Dialog
        isOpen={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        title="Delete Rack"
        description={`Are you sure you want to delete "${rackToDelete?.name}"? This action cannot be undone. All devices in this rack will be removed.`}
      >
        <DialogFooter>
          <Button variant="ghost" onClick={() => setDeleteDialogOpen(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={confirmDelete}>
            Delete Rack
          </Button>
        </DialogFooter>
      </Dialog>

      {currentRack && (
        <>
          <DeviceAssignDialog
            isOpen={assignDialogOpen}
            onClose={() => {
              setAssignDialogOpen(false);
              setAssignDialogUnit(null);
            }}
            rack={currentRack}
            suggestedUnit={assignDialogUnit}
          />

          {selectedDevice && (
            <DeviceActionsMenu
              isOpen={deviceActionsOpen}
              onClose={() => {
                setDeviceActionsOpen(false);
                setSelectedDevice(null);
              }}
              device={selectedDevice}
              currentRack={currentRack}
            />
          )}
        </>
      )}
    </div>
  );
};
