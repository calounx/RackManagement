import React, { useState } from 'react';
import { Dialog, DialogFooter } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { useStore } from '../../store/useStore';
import type { Device, Rack } from '../../types';
import { motion } from 'framer-motion';
import { Move, Trash2 } from 'lucide-react';

interface DeviceActionsMenuProps {
  isOpen: boolean;
  onClose: () => void;
  device: Device;
  currentRack: Rack;
}

type ActionType = 'move' | 'remove' | null;

export const DeviceActionsMenu: React.FC<DeviceActionsMenuProps> = ({
  isOpen,
  onClose,
  device,
  currentRack,
}) => {
  const { racks, devices, moveDevice } = useStore();
  const [action, setAction] = useState<ActionType>(null);
  const [targetRackId, setTargetRackId] = useState<number>(currentRack.id);
  const [targetUnit, setTargetUnit] = useState<number>(device.start_unit || 1);
  const [loading, setLoading] = useState(false);

  const targetRack = racks.find(r => r.id === targetRackId) || currentRack;

  // Check if placement is valid
  const getPlacementValidation = () => {
    if (targetUnit < 1 || targetUnit > targetRack.units) {
      return { valid: false, message: `Unit must be between 1 and ${targetRack.units}` };
    }

    const endUnit = targetUnit + device.height_units - 1;
    if (endUnit > targetRack.units) {
      return {
        valid: false,
        message: `Device needs ${device.height_units}U but only ${targetRack.units - targetUnit + 1}U available`
      };
    }

    // Check for collisions with existing devices in target rack (excluding current device)
    const rackDevices = devices.filter(d => d.rack_id === targetRackId && d.id !== device.id);
    for (const otherDevice of rackDevices) {
      if (!otherDevice.start_unit) continue;
      const deviceStart = otherDevice.start_unit;
      const deviceEnd = otherDevice.start_unit + otherDevice.height_units - 1;

      // Check if ranges overlap
      if (
        (targetUnit >= deviceStart && targetUnit <= deviceEnd) ||
        (endUnit >= deviceStart && endUnit <= deviceEnd) ||
        (targetUnit <= deviceStart && endUnit >= deviceEnd)
      ) {
        return {
          valid: false,
          message: `Units ${targetUnit}-${endUnit} overlap with ${otherDevice.name}`
        };
      }
    }

    return { valid: true, message: `Will occupy units ${targetUnit}-${endUnit}` };
  };

  const handleMove = async () => {
    if (!getPlacementValidation().valid) return;

    setLoading(true);
    try {
      await moveDevice(device.id, targetRackId, targetUnit);
      onClose();
    } catch (error) {
      console.error('Failed to move device:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async () => {
    setLoading(true);
    try {
      // Move device to null rack (unassign)
      await moveDevice(device.id, null, null);
      onClose();
    } catch (error) {
      console.error('Failed to remove device:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  // Action selection view
  if (!action) {
    return (
      <Dialog
        isOpen={isOpen}
        onClose={onClose}
        title="Device Actions"
        description={`Manage ${device.name}`}
        size="md"
      >
        <div className="space-y-3">
          <motion.button
            onClick={() => setAction('move')}
            className="w-full p-4 rounded-lg bg-secondary/50 border-2 border-border hover:border-electric transition-all text-left"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-electric/10 rounded-lg">
                <Move className="w-5 h-5 text-electric" />
              </div>
              <div>
                <h4 className="font-medium text-foreground">Move Device</h4>
                <p className="text-xs text-muted-foreground mt-1">
                  Move to different unit or different rack
                </p>
              </div>
            </div>
          </motion.button>

          <motion.button
            onClick={() => setAction('remove')}
            className="w-full p-4 rounded-lg bg-secondary/50 border-2 border-border hover:border-red-500/50 transition-all text-left"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-500/10 rounded-lg">
                <Trash2 className="w-5 h-5 text-red-500" />
              </div>
              <div>
                <h4 className="font-medium text-foreground">Remove from Rack</h4>
                <p className="text-xs text-muted-foreground mt-1">
                  Unassign device from this rack
                </p>
              </div>
            </div>
          </motion.button>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
        </DialogFooter>
      </Dialog>
    );
  }

  // Move device view
  if (action === 'move') {
    const validation = getPlacementValidation();

    return (
      <Dialog
        isOpen={isOpen}
        onClose={onClose}
        title="Move Device"
        description={`Move ${device.name} to a new location`}
        size="lg"
      >
        <div className="space-y-4">
          {/* Current Location Info */}
          <div className="p-3 bg-secondary/30 rounded-lg border border-border">
            <p className="text-xs text-muted-foreground mb-1">Current Location</p>
            <p className="text-sm font-medium text-foreground">
              {currentRack.name} - Unit {device.start_unit}
              {device.height_units > 1 && ` to ${device.start_unit! + device.height_units - 1}`}
            </p>
          </div>

          {/* Target Rack Selection */}
          <div className="space-y-2">
            <label htmlFor="targetRack" className="text-sm font-medium text-foreground">
              Target Rack
            </label>
            <select
              id="targetRack"
              value={targetRackId}
              onChange={(e) => setTargetRackId(parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-secondary border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-electric"
            >
              {racks.map((rack) => (
                <option key={rack.id} value={rack.id}>
                  {rack.name} ({rack.location})
                </option>
              ))}
            </select>
          </div>

          {/* Target Unit Selection */}
          <div className="space-y-2">
            <label htmlFor="targetUnit" className="text-sm font-medium text-foreground">
              Target Unit Position
            </label>
            <div className="flex items-center gap-4">
              <Input
                id="targetUnit"
                type="number"
                min="1"
                max={targetRack.units}
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
                {Array.from({ length: targetRack.units }, (_, i) => targetRack.units - i).map((unitNumber) => {
                  const rackDevices = devices.filter(d => d.rack_id === targetRackId && d.id !== device.id);
                  const deviceAtUnit = rackDevices.find(d => {
                    if (!d.start_unit) return false;
                    return unitNumber >= d.start_unit && unitNumber < d.start_unit + d.height_units;
                  });

                  const isTargetRange = unitNumber >= targetUnit && unitNumber < targetUnit + device.height_units;

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
          <Button variant="ghost" onClick={() => setAction(null)} disabled={loading}>
            Back
          </Button>
          <Button
            variant="primary"
            onClick={handleMove}
            disabled={!validation.valid || loading}
          >
            {loading ? 'Moving...' : 'Move Device'}
          </Button>
        </DialogFooter>
      </Dialog>
    );
  }

  // Remove device confirmation
  if (action === 'remove') {
    return (
      <Dialog
        isOpen={isOpen}
        onClose={onClose}
        title="Remove Device from Rack"
        description={`Are you sure you want to remove ${device.name} from ${currentRack.name}?`}
      >
        <div className="p-4 bg-amber/5 border border-amber/20 rounded-lg">
          <p className="text-sm text-foreground">
            The device will be unassigned from this rack and returned to the device library.
            You can assign it to a rack again later.
          </p>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => setAction(null)} disabled={loading}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleRemove} disabled={loading}>
            {loading ? 'Removing...' : 'Remove from Rack'}
          </Button>
        </DialogFooter>
      </Dialog>
    );
  }

  return null;
};
