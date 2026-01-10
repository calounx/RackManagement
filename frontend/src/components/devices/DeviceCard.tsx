import React from 'react';
import type { Device } from '../../types';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { formatPower, formatTemperature, getThermalStatus } from '../../lib/utils';

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

  const getStatusVariant = (): 'success' | 'warning' | 'error' | 'default' => {
    switch (device.status) {
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

  return (
    <Card
      interactive
      className="hover:border-electric/30"
      onClick={() => onView && onView(device)}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg">{device.name}</CardTitle>
            <p className="text-sm text-muted-foreground font-mono mt-1">
              {device.manufacturer} {device.model}
            </p>
          </div>
          <Badge variant={getStatusVariant()} pulse>
            {device.status}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-3">
          {/* Device Type */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Type</span>
            <span className="font-mono text-foreground capitalize">
              {device.device_type.replace('_', ' ')}
            </span>
          </div>

          {/* Rack Location */}
          {device.rack_id && device.start_unit && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Location</span>
              <span className="font-mono text-electric">
                Rack {device.rack_id} • U{device.start_unit}
              </span>
            </div>
          )}

          {/* Specifications */}
          <div className="grid grid-cols-3 gap-2 pt-2 border-t border-border">
            <div className="text-center">
              <p className="text-xs text-muted-foreground">Height</p>
              <p className="font-mono text-foreground font-semibold mt-1">
                {device.height_units}U
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground">Power</p>
              <p className="font-mono text-amber font-semibold mt-1">
                {formatPower(device.power_consumption_watts)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground">Temp</p>
              <p className={`font-mono font-semibold mt-1 ${thermalStatus.color}`}>
                {formatTemperature(device.temperature_celsius)}
              </p>
            </div>
          </div>

          {/* Network Info */}
          {device.ip_address && (
            <div className="flex items-center gap-2 text-xs pt-2 border-t border-border">
              <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
              </svg>
              <span className="text-muted-foreground font-mono">{device.ip_address}</span>
            </div>
          )}
        </div>
      </CardContent>

      <CardFooter>
        <div className="flex gap-2 w-full">
          {onEdit && (
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={(e) => {
                e.stopPropagation();
                onEdit(device);
              }}
            >
              Edit
            </Button>
          )}
          {onDelete && (
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(device);
              }}
              className="text-red-500 hover:text-red-400"
            >
              Delete
            </Button>
          )}
        </div>
      </CardFooter>
    </Card>
  );
};
