import React, { useState } from 'react';
import { motion } from 'framer-motion';
import type { Rack, Device } from '../../types';
import { DeviceSlot } from './DeviceSlot';
import { ThermalOverlay } from './ThermalOverlay';
import { useStore } from '../../store/useStore';
import { cn, formatPower } from '../../lib/utils';
import {
  Warehouse,
  Boxes,
  BarChart3,
  PieChart,
  Zap,
  Plus,
  MapPin,
} from 'lucide-react';

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

  // Calculate statistics
  const assignedDevices = devices.filter((d) => d.start_unit !== null && d.start_unit !== undefined);
  const usedUnits = assignedDevices.reduce((sum, d) => sum + d.height_units, 0);
  const utilizationPercent = Math.round((usedUnits / rack.units) * 100);
  const totalPower = assignedDevices.reduce((sum, d) => sum + d.power_consumption_watts, 0);
  const powerPercent = Math.round((totalPower / rack.max_power_watts) * 100);

  // Get power color based on percentage
  const getPowerColor = (percent: number): string => {
    if (percent >= 90) return 'text-red-500';
    if (percent >= 75) return 'text-amber';
    if (percent >= 50) return 'text-lime';
    return 'text-green-500';
  };

  // Get utilization color
  const getUtilizationColor = (percent: number): string => {
    if (percent >= 90) return 'text-red-500';
    if (percent >= 75) return 'text-amber';
    return 'text-cyan';
  };

  return (
    <div className="relative">
      {/* Rack Info Header */}
      <div className="mb-4 p-5 glass rounded-lg border border-electric/20 shadow-lg">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-lg glass border border-electric/30 shadow-lg shadow-electric/20">
              <Warehouse className="h-8 w-8 text-electric" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-foreground flex items-center gap-2">
                {rack.name}
              </h2>
              <div className="flex items-center gap-2 mt-1">
                <MapPin className="h-4 w-4 text-muted-foreground" />
                <p className="text-sm text-muted-foreground font-mono">
                  {rack.location}
                </p>
                <span className="text-muted-foreground">•</span>
                <p className="text-sm text-muted-foreground font-mono">
                  {rack.units}U Capacity
                </p>
              </div>
            </div>
          </div>
          <div className="text-right glass rounded-lg p-3 border border-amber/30">
            <div className="flex items-center gap-2 justify-end mb-1">
              <Zap className="h-4 w-4 text-amber" />
              <p className="text-xs text-muted-foreground font-medium">Max Power</p>
            </div>
            <p className="text-xl font-mono font-bold text-amber">
              {formatPower(rack.max_power_watts)}
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
                        className="absolute inset-0 border-2 border-dashed border-electric/50 rounded glass"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                      >
                        <div className="absolute inset-0 flex items-center justify-center gap-2">
                          <Plus className="h-4 w-4 text-electric" />
                          <span className="text-xs text-electric font-mono font-medium">
                            Add Device
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
          <div className="mt-4 grid grid-cols-4 gap-3">
            {/* Devices Count */}
            <motion.div
              className="glass rounded-lg p-4 border border-border hover:border-electric/30 transition-all duration-200 hover:shadow-lg hover:shadow-electric/10"
              whileHover={{ scale: 1.02, y: -2 }}
            >
              <div className="flex items-center justify-center gap-2 mb-2">
                <Boxes className="h-5 w-5 text-electric" />
                <p className="text-xs text-muted-foreground font-medium">Devices</p>
              </div>
              <p className="text-3xl font-bold text-electric text-center">
                {assignedDevices.length}
              </p>
            </motion.div>

            {/* Used Units */}
            <motion.div
              className="glass rounded-lg p-4 border border-border hover:border-amber/30 transition-all duration-200 hover:shadow-lg hover:shadow-amber/10"
              whileHover={{ scale: 1.02, y: -2 }}
            >
              <div className="flex items-center justify-center gap-2 mb-2">
                <BarChart3 className="h-5 w-5 text-amber" />
                <p className="text-xs text-muted-foreground font-medium">Used Units</p>
              </div>
              <p className="text-2xl font-bold text-amber text-center">
                {usedUnits}
                <span className="text-lg text-muted-foreground">/{rack.units}</span>
              </p>
            </motion.div>

            {/* Utilization */}
            <motion.div
              className="glass rounded-lg p-4 border border-border hover:border-cyan/30 transition-all duration-200 hover:shadow-lg hover:shadow-cyan/10"
              whileHover={{ scale: 1.02, y: -2 }}
            >
              <div className="flex items-center justify-center gap-2 mb-2">
                <PieChart className="h-5 w-5 text-cyan" />
                <p className="text-xs text-muted-foreground font-medium">Utilization</p>
              </div>
              <div className="space-y-2">
                <p className={cn('text-3xl font-bold text-center', getUtilizationColor(utilizationPercent))}>
                  {utilizationPercent}%
                </p>
                {/* Progress Bar */}
                <div className="w-full h-1.5 bg-secondary rounded-full overflow-hidden">
                  <motion.div
                    className={cn(
                      'h-full rounded-full',
                      utilizationPercent >= 90 ? 'bg-red-500' : utilizationPercent >= 75 ? 'bg-amber' : 'bg-cyan'
                    )}
                    initial={{ width: 0 }}
                    animate={{ width: `${utilizationPercent}%` }}
                    transition={{ duration: 0.8, ease: 'easeOut' }}
                  />
                </div>
              </div>
            </motion.div>

            {/* Power Draw */}
            <motion.div
              className="glass rounded-lg p-4 border border-border hover:border-lime/30 transition-all duration-200 hover:shadow-lg hover:shadow-lime/10"
              whileHover={{ scale: 1.02, y: -2 }}
            >
              <div className="flex items-center justify-center gap-2 mb-2">
                <Zap className="h-5 w-5 text-lime" />
                <p className="text-xs text-muted-foreground font-medium">Power Draw</p>
              </div>
              <div className="space-y-2">
                <p className={cn('text-2xl font-bold text-center', getPowerColor(powerPercent))}>
                  {formatPower(totalPower)}
                </p>
                <p className="text-xs text-center text-muted-foreground">
                  {powerPercent}% of capacity
                </p>
                {/* Power Bar */}
                <div className="w-full h-1.5 bg-secondary rounded-full overflow-hidden">
                  <motion.div
                    className={cn(
                      'h-full rounded-full',
                      powerPercent >= 90 ? 'bg-red-500' : powerPercent >= 75 ? 'bg-amber' : powerPercent >= 50 ? 'bg-lime' : 'bg-green-500'
                    )}
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(powerPercent, 100)}%` }}
                    transition={{ duration: 0.8, ease: 'easeOut' }}
                  />
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};
