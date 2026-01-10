import React, { useState } from 'react';
import { motion } from 'framer-motion';
import type { Rack, Device } from '../../types';
import { DeviceSlot } from './DeviceSlot';
import { ThermalOverlay } from './ThermalOverlay';
import { useStore } from '../../store/useStore';
import { cn } from '../../lib/utils';

interface RackVisualizerProps {
  rack: Rack;
  devices: Device[];
  onDeviceClick?: (device: Device) => void;
  onUnitClick?: (unitNumber: number) => void;
}

export const RackVisualizer: React.FC<RackVisualizerProps> = ({
  rack,
  devices,
  onDeviceClick,
  onUnitClick,
}) => {
  const rackViewOptions = useStore((state) => state.rackViewOptions);
  const [hoveredUnit, setHoveredUnit] = useState<number | null>(null);

  // Create array of rack units (42U standard, numbered from bottom to top)
  const rackUnits = Array.from({ length: rack.units || 42 }, (_, i) => rack.units - i);

  // Check if a unit is occupied
  const getDeviceAtUnit = (unitNumber: number): Device | null => {
    return devices.find((device) => {
      if (!device.start_unit) return false;
      const endUnit = device.start_unit + device.height_units - 1;
      return unitNumber >= device.start_unit && unitNumber <= endUnit;
    }) || null;
  };

  // Check if a unit is the start of a device
  const isDeviceStart = (unitNumber: number): boolean => {
    return devices.some((device) => device.start_unit === unitNumber);
  };

  const handleUnitClick = (unitNumber: number) => {
    const device = getDeviceAtUnit(unitNumber);
    if (device && onDeviceClick) {
      onDeviceClick(device);
    } else if (onUnitClick) {
      onUnitClick(unitNumber);
    }
  };

  return (
    <div className="relative">
      {/* Rack Info Header */}
      <div className="mb-4 p-4 glass rounded-lg border border-border">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-semibold text-foreground">{rack.name}</h2>
            <p className="text-sm text-muted-foreground font-mono mt-1">
              {rack.location} • {rack.units}U Capacity
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-muted-foreground">Power Capacity</p>
            <p className="text-lg font-mono text-electric">
              {rack.max_power_watts}W
            </p>
          </div>
        </div>
      </div>

      {/* Rack Visualization */}
      <div className="relative">
        <div className="glass rounded-lg border border-electric/20 p-6">
          {/* Rack Frame */}
          <div className="relative border-2 border-electric/30 rounded-lg overflow-hidden">
            {/* Side Rails */}
            <div className="absolute left-0 top-0 bottom-0 w-6 bg-gradient-to-r from-secondary to-transparent" />
            <div className="absolute right-0 top-0 bottom-0 w-6 bg-gradient-to-l from-secondary to-transparent" />

            {/* Units Container */}
            <div className="relative px-8 py-4 grid-lines">
              {rackUnits.map((unitNumber) => {
                const device = getDeviceAtUnit(unitNumber);
                const isStart = isDeviceStart(unitNumber);
                const isOccupied = device !== null;
                const isHovered = hoveredUnit === unitNumber;

                return (
                  <motion.div
                    key={unitNumber}
                    className={cn(
                      'rack-unit relative cursor-pointer group',
                      !isOccupied && 'hover:bg-electric/5'
                    )}
                    onMouseEnter={() => setHoveredUnit(unitNumber)}
                    onMouseLeave={() => setHoveredUnit(null)}
                    onClick={() => handleUnitClick(unitNumber)}
                    whileHover={!isOccupied ? { scale: 1.01 } : {}}
                  >
                    {/* Unit Number Label */}
                    <div
                      className={cn(
                        'absolute left-1 top-1/2 -translate-y-1/2',
                        'text-xs font-mono text-muted-foreground',
                        isHovered && 'text-electric'
                      )}
                    >
                      {unitNumber.toString().padStart(2, '0')}
                    </div>

                    {/* Device Slot */}
                    {isStart && device && (
                      <DeviceSlot
                        device={device}
                        onClick={() => onDeviceClick && onDeviceClick(device)}
                      />
                    )}

                    {/* Empty Slot Indicator */}
                    {!isOccupied && isHovered && (
                      <motion.div
                        className="absolute inset-0 border-2 border-dashed border-electric/50 rounded"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                      >
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-xs text-electric font-mono">
                            + Add Device
                          </span>
                        </div>
                      </motion.div>
                    )}
                  </motion.div>
                );
              })}
            </div>

            {/* Thermal Overlay */}
            {rackViewOptions.showThermal && (
              <ThermalOverlay rackId={rack.id} devices={devices} />
            )}
          </div>

          {/* Rack Stats */}
          <div className="mt-4 grid grid-cols-3 gap-4 text-center">
            <div className="glass rounded p-3 border border-border">
              <p className="text-xs text-muted-foreground font-mono">Devices</p>
              <p className="text-2xl font-bold text-electric mt-1">
                {devices.filter((d) => d.rack_id === rack.id).length}
              </p>
            </div>
            <div className="glass rounded p-3 border border-border">
              <p className="text-xs text-muted-foreground font-mono">Used Units</p>
              <p className="text-2xl font-bold text-amber mt-1">
                {devices
                  .filter((d) => d.rack_id === rack.id)
                  .reduce((sum, d) => sum + d.height_units, 0)}
                /{rack.units}
              </p>
            </div>
            <div className="glass rounded p-3 border border-border">
              <p className="text-xs text-muted-foreground font-mono">Power Draw</p>
              <p className="text-2xl font-bold text-lime mt-1">
                {devices
                  .filter((d) => d.rack_id === rack.id)
                  .reduce((sum, d) => sum + d.power_consumption_watts, 0)}
                W
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
