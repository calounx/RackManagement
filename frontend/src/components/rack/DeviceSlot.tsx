import React from 'react';
import { motion } from 'framer-motion';
import type { Device } from '../../types';
import { Badge } from '../ui/badge';
import { cn, formatPower, formatTemperature, getThermalStatus } from '../../lib/utils';

interface DeviceSlotProps {
  device: Device;
  onClick?: () => void;
  isDragging?: boolean;
}

const getDeviceTypeColor = (_deviceType: string): string => {
  const colors: Record<string, string> = {
    server: 'border-blue-500/50 bg-blue-500/10',
    switch: 'border-electric/50 bg-electric/10',
    router: 'border-purple-500/50 bg-purple-500/10',
    firewall: 'border-red-500/50 bg-red-500/10',
    storage: 'border-green-500/50 bg-green-500/10',
    pdu: 'border-amber/50 bg-amber/10',
    ups: 'border-orange-500/50 bg-orange-500/10',
    patch_panel: 'border-slate-500/50 bg-slate-500/10',
  };
  return colors[_deviceType] || 'border-border bg-card';
};

const getStatusVariant = (status: string): 'success' | 'warning' | 'error' | 'default' => {
  switch (status) {
    case 'active':
      return 'success';
    case 'maintenance':
      return 'warning';
    case 'error':
      return 'error';
    default:
      return 'default';
  }
};

export const DeviceSlot: React.FC<DeviceSlotProps> = ({ device, onClick, isDragging = false }) => {
  const thermalStatus = getThermalStatus(device.temperature_celsius);
  const heightPx = device.height_units * 44.45; // 44.45px per U

  return (
    <motion.div
      className={cn(
        'absolute left-8 right-8 border-2 rounded-lg overflow-hidden cursor-pointer',
        'transition-all duration-200',
        getDeviceTypeColor(device.device_type),
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
      <div className="h-full p-2 flex flex-col justify-between relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-5">
          <div className="grid-lines h-full" />
        </div>

        {/* Header */}
        <div className="relative z-10 flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h4 className="font-semibold text-sm text-foreground truncate">
              {device.name}
            </h4>
            <p className="text-xs text-muted-foreground font-mono truncate">
              {device.manufacturer} {device.model}
            </p>
          </div>
          <Badge variant={getStatusVariant(device.status)} pulse>
            {device.status}
          </Badge>
        </div>

        {/* Device Info - Show more details for taller devices */}
        {device.height_units >= 2 && (
          <div className="relative z-10 space-y-1">
            <div className="flex items-center gap-2 text-xs">
              <svg className="w-3 h-3 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span className="text-muted-foreground font-mono">
                {formatPower(device.power_consumption_watts)}
              </span>
            </div>

            <div className="flex items-center gap-2 text-xs">
              <svg className="w-3 h-3 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span className={cn('font-mono', thermalStatus.color)}>
                {formatTemperature(device.temperature_celsius)}
              </span>
            </div>

            {device.ip_address && (
              <div className="flex items-center gap-2 text-xs">
                <svg className="w-3 h-3 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                </svg>
                <span className="text-muted-foreground font-mono">
                  {device.ip_address}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="relative z-10 flex items-center justify-between">
          <div className="flex items-center gap-1">
            <div className="text-xs font-mono text-muted-foreground">
              U{device.start_unit}
              {device.height_units > 1 && `-U${device.start_unit! + device.height_units - 1}`}
            </div>
          </div>

          <div className="text-xs font-mono text-muted-foreground">
            {device.height_units}U
          </div>
        </div>

        {/* Status Indicator LED */}
        <div className="absolute top-2 right-2">
          {device.status === 'active' && (
            <div className="w-2 h-2 bg-lime rounded-full animate-pulse-glow glow-lime" />
          )}
          {device.status === 'error' && (
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse-glow" />
          )}
          {device.status === 'maintenance' && (
            <div className="w-2 h-2 bg-amber rounded-full animate-pulse-glow glow-amber" />
          )}
        </div>
      </div>
    </motion.div>
  );
};
