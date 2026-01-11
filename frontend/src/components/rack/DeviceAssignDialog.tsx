import React, { useState, useEffect } from 'react';
import { Dialog, DialogFooter } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { useStore } from '../../store/useStore';
import type { Rack } from '../../types';
import { motion, AnimatePresence } from 'framer-motion';
import { Package, Plus, Search } from 'lucide-react';

interface DeviceAssignDialogProps {
  isOpen: boolean;
  onClose: () => void;
  rack: Rack;
  suggestedUnit?: number | null;
}

type TabType = 'existing' | 'new';

export const DeviceAssignDialog: React.FC<DeviceAssignDialogProps> = ({
  isOpen,
  onClose,
  rack,
  suggestedUnit,
}) => {
  const { devices, deviceSpecs, fetchDevices, fetchDeviceSpecs, createDevice, moveDevice } = useStore();
  const [activeTab, setActiveTab] = useState<TabType>('existing');
  const [selectedDeviceId, setSelectedDeviceId] = useState<number | null>(null);
  const [targetUnit, setTargetUnit] = useState<number>(suggestedUnit || 1);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);

  // New device form data
  const [newDeviceForm, setNewDeviceForm] = useState({
    specification_id: '',
    custom_name: '',
    notes: '',
  });

  useEffect(() => {
    if (isOpen) {
      fetchDevices();
      fetchDeviceSpecs();
      setTargetUnit(suggestedUnit || 1);
      setSelectedDeviceId(null);
      setSearchQuery('');
      setNewDeviceForm({
        specification_id: '',
        custom_name: '',
        notes: '',
      });
    }
  }, [isOpen, suggestedUnit, fetchDevices, fetchDeviceSpecs]);

  // Get unassigned devices (not in any rack)
  const unassignedDevices = devices.filter(d => d.rack_id === null);

  // Filter devices based on search
  const filteredDevices = unassignedDevices.filter(device => {
    const query = searchQuery.toLowerCase();
    return (
      device.name.toLowerCase().includes(query) ||
      device.manufacturer.toLowerCase().includes(query) ||
      device.model.toLowerCase().includes(query)
    );
  });

  const selectedDevice = unassignedDevices.find(d => d.id === selectedDeviceId);
  const selectedSpec = deviceSpecs.find(s => s.id.toString() === newDeviceForm.specification_id);

  // Calculate which device will be assigned (existing or newly created height)
  const deviceHeightUnits = activeTab === 'existing'
    ? (selectedDevice?.height_units || 0)
    : (selectedSpec?.height_units || 0);

  // Check if placement is valid
  const getPlacementValidation = () => {
    if (targetUnit < 1 || targetUnit > rack.units) {
      return { valid: false, message: `Unit must be between 1 and ${rack.units}` };
    }

    if (deviceHeightUnits === 0) {
      return { valid: false, message: 'Select a device first' };
    }

    const endUnit = targetUnit + deviceHeightUnits - 1;
    if (endUnit > rack.units) {
      return {
        valid: false,
        message: `Device needs ${deviceHeightUnits}U but only ${rack.units - targetUnit + 1}U available`
      };
    }

    // Check for collisions with existing devices in this rack
    const rackDevices = devices.filter(d => d.rack_id === rack.id);
    for (const device of rackDevices) {
      if (!device.start_unit) continue;
      const deviceStart = device.start_unit;
      const deviceEnd = device.start_unit + device.height_units - 1;

      // Check if ranges overlap
      if (
        (targetUnit >= deviceStart && targetUnit <= deviceEnd) ||
        (endUnit >= deviceStart && endUnit <= deviceEnd) ||
        (targetUnit <= deviceStart && endUnit >= deviceEnd)
      ) {
        return {
          valid: false,
          message: `Units ${targetUnit}-${endUnit} overlap with ${device.name} at U${deviceStart}-U${deviceEnd}`
        };
      }
    }

    return { valid: true, message: `Will occupy units ${targetUnit}-${endUnit}` };
  };

  const validation = getPlacementValidation();

  const handleAssign = async () => {
    if (!validation.valid) return;

    setLoading(true);
    try {
      if (activeTab === 'existing' && selectedDeviceId) {
        // Move existing device to rack
        await moveDevice(selectedDeviceId, rack.id, targetUnit);
      } else if (activeTab === 'new' && newDeviceForm.specification_id) {
        // Create new device and assign to rack
        const deviceData = {
          specification_id: parseInt(newDeviceForm.specification_id),
          custom_name: newDeviceForm.custom_name || undefined,
          notes: newDeviceForm.notes || undefined,
          rack_id: rack.id,
          start_unit: targetUnit,
        };
        await createDevice(deviceData);
      }

      onClose();
    } catch (error) {
      console.error('Failed to assign device:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Add Device to Rack"
      description={`Assign a device to ${rack.name}`}
      size="lg"
    >
      <div className="space-y-4">
        {/* Tabs */}
        <div className="flex gap-2 p-1 bg-secondary/30 rounded-lg">
          <button
            onClick={() => setActiveTab('existing')}
            className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-all ${
              activeTab === 'existing'
                ? 'bg-electric text-electric-foreground shadow-lg shadow-electric/20'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <Package className="w-4 h-4" />
              Select Existing Device
            </div>
          </button>
          <button
            onClick={() => setActiveTab('new')}
            className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-all ${
              activeTab === 'new'
                ? 'bg-electric text-electric-foreground shadow-lg shadow-electric/20'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <Plus className="w-4 h-4" />
              Create New Device
            </div>
          </button>
        </div>

        <AnimatePresence mode="wait">
          {activeTab === 'existing' ? (
            <motion.div
              key="existing"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="space-y-4"
            >
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search devices..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* Device List */}
              <div className="max-h-64 overflow-y-auto space-y-2 border border-border rounded-lg p-2 bg-secondary/20">
                {filteredDevices.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Package className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">
                      {unassignedDevices.length === 0
                        ? 'No unassigned devices available'
                        : 'No devices match your search'
                      }
                    </p>
                  </div>
                ) : (
                  filteredDevices.map((device) => (
                    <motion.button
                      key={device.id}
                      onClick={() => setSelectedDeviceId(device.id)}
                      className={`w-full p-3 rounded-lg text-left transition-all border-2 ${
                        selectedDeviceId === device.id
                          ? 'bg-electric/10 border-electric'
                          : 'bg-card border-border hover:border-electric/50'
                      }`}
                      whileHover={{ scale: 1.01 }}
                      whileTap={{ scale: 0.99 }}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-foreground truncate">{device.name}</h4>
                          <p className="text-xs text-muted-foreground font-mono mt-1">
                            {device.manufacturer} {device.model}
                          </p>
                        </div>
                        <div className="ml-2 text-right">
                          <div className="text-xs font-mono text-electric">{device.height_units}U</div>
                          <div className="text-xs text-muted-foreground">{device.power_consumption_watts}W</div>
                        </div>
                      </div>
                    </motion.button>
                  ))
                )}
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="new"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="space-y-4"
            >
              {/* Device Specification */}
              <div className="space-y-2">
                <label htmlFor="spec" className="text-sm font-medium text-foreground">
                  Device Specification *
                </label>
                <select
                  id="spec"
                  value={newDeviceForm.specification_id}
                  onChange={(e) => setNewDeviceForm({ ...newDeviceForm, specification_id: e.target.value })}
                  className="w-full px-3 py-2 bg-secondary border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-electric"
                >
                  <option value="">Select device type...</option>
                  {deviceSpecs.map((spec) => (
                    <option key={spec.id} value={spec.id}>
                      {spec.manufacturer} {spec.model} - {spec.height_units}U, {spec.power_consumption_watts}W
                    </option>
                  ))}
                </select>
              </div>

              {/* Spec Preview */}
              {selectedSpec && (
                <div className="p-3 bg-electric/5 rounded-lg border border-electric/20">
                  <p className="text-xs font-semibold text-foreground mb-2">Specification Details:</p>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <span className="text-muted-foreground">Height:</span>
                      <span className="ml-1 text-electric font-mono">{selectedSpec.height_units}U</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Power:</span>
                      <span className="ml-1 text-electric font-mono">{selectedSpec.power_consumption_watts}W</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Weight:</span>
                      <span className="ml-1 text-electric font-mono">{selectedSpec.weight_kg}kg</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Custom Name */}
              <div className="space-y-2">
                <label htmlFor="custom_name" className="text-sm font-medium text-foreground">
                  Custom Name (Optional)
                </label>
                <Input
                  id="custom_name"
                  value={newDeviceForm.custom_name}
                  onChange={(e) => setNewDeviceForm({ ...newDeviceForm, custom_name: e.target.value })}
                  placeholder="e.g., Core Switch 1, Main Router"
                />
              </div>

              {/* Notes */}
              <div className="space-y-2">
                <label htmlFor="notes" className="text-sm font-medium text-foreground">
                  Notes (Optional)
                </label>
                <textarea
                  id="notes"
                  value={newDeviceForm.notes}
                  onChange={(e) => setNewDeviceForm({ ...newDeviceForm, notes: e.target.value })}
                  placeholder="Additional notes about this device..."
                  className="w-full px-3 py-2 bg-secondary border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-electric resize-none"
                  rows={2}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Unit Selection */}
        <div className="space-y-2 pt-4 border-t border-border">
          <label htmlFor="unit" className="text-sm font-medium text-foreground">
            Rack Unit Position
          </label>
          <div className="flex items-center gap-4">
            <Input
              id="unit"
              type="number"
              min="1"
              max={rack.units}
              value={targetUnit}
              onChange={(e) => setTargetUnit(parseInt(e.target.value) || 1)}
              className="w-32"
            />
            <div className={`flex-1 text-sm ${validation.valid ? 'text-muted-foreground' : 'text-red-500'}`}>
              {validation.message}
            </div>
          </div>

          {/* Visual Unit Selector */}
          <div className="max-h-48 overflow-y-auto border border-border rounded-lg p-2 bg-secondary/20">
            <div className="space-y-1">
              {Array.from({ length: rack.units }, (_, i) => rack.units - i).map((unitNumber) => {
                const rackDevices = devices.filter(d => d.rack_id === rack.id);
                const deviceAtUnit = rackDevices.find(d => {
                  if (!d.start_unit) return false;
                  return unitNumber >= d.start_unit && unitNumber < d.start_unit + d.height_units;
                });

                const isTargetRange = deviceHeightUnits > 0 &&
                  unitNumber >= targetUnit &&
                  unitNumber < targetUnit + deviceHeightUnits;

                return (
                  <button
                    key={unitNumber}
                    onClick={() => setTargetUnit(unitNumber)}
                    disabled={!!deviceAtUnit}
                    className={`w-full px-3 py-1.5 rounded text-left text-xs font-mono transition-all ${
                      deviceAtUnit
                        ? 'bg-secondary/50 text-muted-foreground cursor-not-allowed'
                        : isTargetRange
                        ? validation.valid
                          ? 'bg-electric/20 border border-electric text-electric'
                          : 'bg-red-500/20 border border-red-500 text-red-500'
                        : 'hover:bg-secondary/80 border border-transparent text-foreground'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span>U{unitNumber.toString().padStart(2, '0')}</span>
                      {deviceAtUnit && (
                        <span className="text-xs truncate ml-2">{deviceAtUnit.name}</span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      <DialogFooter>
        <Button variant="ghost" onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          variant="primary"
          onClick={handleAssign}
          disabled={!validation.valid || loading}
        >
          {loading ? 'Assigning...' : 'Assign to Rack'}
        </Button>
      </DialogFooter>
    </Dialog>
  );
};
