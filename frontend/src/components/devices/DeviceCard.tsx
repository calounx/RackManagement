import React from 'react';
import type { Device } from '../../types';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../ui/card';
import { IconButton } from '../ui/icon-button';
import { StatusBadge } from '../ui/status-badge';
import { formatPower, formatTemperature, getThermalStatus } from '../../lib/utils';
import {
  getDeviceIcon,
  getDeviceColor,
  getDeviceBorderColor,
  getDeviceGlowColor,
  formatDeviceType,
} from '../../lib/device-icons';
import {
  Pencil,
  Trash2,
  Zap,
  Thermometer,
  Globe,
  Warehouse,
  MapPin,
  Ruler,
} from 'lucide-react';

interface DeviceCardProps {
  device: Device;
  onEdit?: (device: Device) => void;
  onDelete?: (device: Device) => void;
  onView?: (device: Device) => void;
}

export const DeviceCard: React.FC<DeviceCardProps> = ({
  device,
  onEdit,
  onDelete,
  onView,
}) => {
  const thermalStatus = getThermalStatus(device.temperature_celsius);
  const DeviceIcon = getDeviceIcon(device.device_type);
  const deviceColor = getDeviceColor(device.device_type);
  const borderColor = getDeviceBorderColor(device.device_type);
  const glowColor = getDeviceGlowColor(device.device_type);

  const getStatusType = (): 'active' | 'error' | 'warning' | 'inactive' => {
    switch (device.status) {
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

  return (
    <Card
      interactive
      className={`group hover:border-electric/30 transition-all duration-200 ${borderColor} ${glowColor} hover:shadow-2xl hover:scale-[1.02]`}
      onClick={() => onView && onView(device)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start gap-4">
          {/* Large Device Icon */}
          <div className={`p-3 rounded-lg glass border ${borderColor} ${glowColor} group-hover:scale-110 transition-transform duration-200`}>
            <DeviceIcon className={`h-8 w-8 ${deviceColor}`} />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <CardTitle className="text-lg truncate">{device.name}</CardTitle>
                <p className="text-sm text-muted-foreground font-mono mt-0.5 truncate">
                  {device.manufacturer} {device.model}
                </p>
              </div>
              <StatusBadge
                status={getStatusType()}
                label={device.status}
                pulse={device.status === 'active'}
                size="sm"
              />
            </div>

            {/* Device Type Badge */}
            <div className="flex items-center gap-1.5 mt-2">
              <div className={`px-2 py-0.5 rounded-full glass border ${borderColor} text-xs font-medium ${deviceColor}`}>
                {formatDeviceType(device.device_type)}
              </div>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Rack Location */}
        {device.rack_id && device.start_unit ? (
          <div className="flex items-center gap-2 px-3 py-2 glass rounded-lg border border-electric/20">
            <Warehouse className="h-4 w-4 text-electric" />
            <span className="text-sm text-muted-foreground">Rack {device.rack_id}</span>
            <MapPin className="h-3.5 w-3.5 text-electric/70 ml-auto" />
            <span className="text-sm font-mono text-electric">U{device.start_unit}</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 px-3 py-2 glass rounded-lg border border-border">
            <Warehouse className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Unassigned</span>
          </div>
        )}

        {/* Specifications Grid */}
        <div className="grid grid-cols-3 gap-2">
          <div className="glass rounded-lg p-2.5 border border-border hover:border-electric/30 transition-colors">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <Ruler className="h-3.5 w-3.5 text-muted-foreground" />
              <p className="text-xs text-muted-foreground font-medium">Height</p>
            </div>
            <p className="font-mono text-foreground font-bold text-center text-lg">
              {device.height_units}U
            </p>
          </div>

          <div className="glass rounded-lg p-2.5 border border-border hover:border-amber/30 transition-colors">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <Zap className="h-3.5 w-3.5 text-amber" />
              <p className="text-xs text-muted-foreground font-medium">Power</p>
            </div>
            <p className="font-mono text-amber font-bold text-center text-sm">
              {formatPower(device.power_consumption_watts)}
            </p>
          </div>

          <div className="glass rounded-lg p-2.5 border border-border hover:border-red-500/30 transition-colors">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <Thermometer className="h-3.5 w-3.5 text-muted-foreground" />
              <p className="text-xs text-muted-foreground font-medium">Temp</p>
            </div>
            <p className={`font-mono font-bold text-center text-sm ${thermalStatus.color}`}>
              {formatTemperature(device.temperature_celsius)}
            </p>
          </div>
        </div>

        {/* Network Info */}
        {device.ip_address && (
          <div className="flex items-center gap-2 px-3 py-2 glass rounded-lg border border-border">
            <Globe className="h-4 w-4 text-cyan-500" />
            <span className="text-sm text-muted-foreground font-mono">{device.ip_address}</span>
          </div>
        )}
      </CardContent>

      <CardFooter className="pt-3">
        <div className="flex gap-2 w-full">
          {onEdit && (
            <IconButton
              icon={Pencil}
              variant="outline"
              size="md"
              tooltip="Edit Device"
              onClick={(e) => {
                e.stopPropagation();
                onEdit(device);
              }}
              className="flex-1"
            />
          )}
          {onDelete && (
            <IconButton
              icon={Trash2}
              variant="danger"
              size="md"
              tooltip="Delete Device"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(device);
              }}
            />
          )}
        </div>
      </CardFooter>
    </Card>
  );
};
