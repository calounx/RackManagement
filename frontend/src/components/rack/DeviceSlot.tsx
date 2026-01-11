import React from 'react';
import { motion } from 'framer-motion';
import type { Device } from '../../types';
import { StatusIndicator } from '../ui/status-badge';
import { cn, formatPower, formatTemperature, getThermalStatus } from '../../lib/utils';
import {
  getDeviceIcon,
  getDeviceColor,
  getDeviceBorderColor,
  getDeviceGlowColor,
} from '../../lib/device-icons';
import { Zap, Thermometer, Globe } from 'lucide-react';

interface DeviceSlotProps {
  device: Device;
  onClick?: () => void;
  isDragging?: boolean;
}

const getStatusType = (status: string): 'active' | 'error' | 'warning' | 'inactive' => {
  switch (status) {
    case 'active':
      return 'active';
    case 'maintenance':
      return 'warning';
    case 'error':
      return 'error';
    default:
      return 'inactive';
  }
};

export const DeviceSlot: React.FC<DeviceSlotProps> = ({ device, onClick, isDragging = false }) => {
  const thermalStatus = getThermalStatus(device.temperature_celsius);
  const heightPx = device.height_units * 44.45; // 44.45px per U
  const DeviceIcon = getDeviceIcon(device.device_type);
  const deviceColor = getDeviceColor(device.device_type);
  const borderColor = getDeviceBorderColor(device.device_type);
  const glowColor = getDeviceGlowColor(device.device_type);
  const statusType = getStatusType(device.status);

  return (
    <motion.div
      className={cn(
        'absolute left-8 right-8 border-2 rounded-lg overflow-hidden cursor-pointer',
        'transition-all duration-200',
        borderColor,
        glowColor,
        'hover:shadow-xl',
        isDragging && 'opacity-50 scale-95'
      )}
      style={{
        height: `${heightPx}px`,
        top: 0,
      }}
      onClick={onClick}
      whileHover={{ scale: 1.02, zIndex: 10 }}
      whileTap={{ scale: 0.98 }}
      layout
    >
      {/* Device Content */}
      <div className="h-full p-2 flex flex-col justify-between relative overflow-hidden glass">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-5">
          <div className="grid-lines h-full" />
        </div>

        {/* Header with Device Icon */}
        <div className="relative z-10 flex items-start gap-2">
          {/* Device Type Icon */}
          <div className={cn('p-1.5 rounded-lg glass border', borderColor)}>
            <DeviceIcon className={cn('h-4 w-4', deviceColor)} />
          </div>

          <div className="flex-1 min-w-0">
            <h4 className="font-semibold text-sm text-foreground truncate leading-tight">
              {device.name}
            </h4>
            {device.height_units >= 2 && (
              <p className="text-xs text-muted-foreground font-mono truncate leading-tight mt-0.5">
                {device.manufacturer}
              </p>
            )}
          </div>

          {/* Status Indicator */}
          <StatusIndicator status={statusType} pulse={statusType === 'active'} size="sm" />
        </div>

        {/* Device Info - Show more details for taller devices */}
        {device.height_units >= 2 && (
          <div className="relative z-10 space-y-1 mt-1">
            <div className="flex items-center gap-1.5 text-xs">
              <Zap className="w-3 h-3 text-amber" />
              <span className="text-amber font-mono font-medium">
                {formatPower(device.power_consumption_watts)}
              </span>
            </div>

            <div className="flex items-center gap-1.5 text-xs">
              <Thermometer className={cn('w-3 h-3', thermalStatus.color)} />
              <span className={cn('font-mono font-medium', thermalStatus.color)}>
                {formatTemperature(device.temperature_celsius)}
              </span>
            </div>

            {device.ip_address && device.height_units >= 3 && (
              <div className="flex items-center gap-1.5 text-xs">
                <Globe className="w-3 h-3 text-cyan-500" />
                <span className="text-muted-foreground font-mono truncate">
                  {device.ip_address}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Compact info for 1U devices */}
        {device.height_units === 1 && (
          <div className="relative z-10 flex items-center gap-2 text-xs mt-1">
            <div className="flex items-center gap-1">
              <Zap className="w-3 h-3 text-amber" />
              <span className="text-amber font-mono text-xs">
                {formatPower(device.power_consumption_watts)}
              </span>
            </div>
            <div className="flex items-center gap-1">
              <Thermometer className={cn('w-3 h-3', thermalStatus.color)} />
              <span className={cn('font-mono text-xs', thermalStatus.color)}>
                {device.temperature_celsius.toFixed(0)}°C
              </span>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="relative z-10 flex items-center justify-between mt-auto">
          <div className="text-xs font-mono text-electric font-medium">
            U{device.start_unit}
            {device.height_units > 1 && `-U${device.start_unit! + device.height_units - 1}`}
          </div>

          <div className={cn('text-xs font-mono font-medium px-1.5 py-0.5 rounded-full glass border', borderColor, deviceColor)}>
            {device.height_units}U
          </div>
        </div>
      </div>
    </motion.div>
  );
};
