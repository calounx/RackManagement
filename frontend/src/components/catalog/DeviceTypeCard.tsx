import React from 'react';
import { motion } from 'framer-motion';
import { Pencil, Trash2, Package } from 'lucide-react';
import { Card } from '../ui/card';
import { IconButton } from '../ui/icon-button';
import { cn } from '../../lib/utils';
import type { DeviceTypeResponse } from '../../types/catalog';

interface DeviceTypeCardProps {
  deviceType: DeviceTypeResponse;
  onEdit?: (deviceType: DeviceTypeResponse) => void;
  onDelete?: (deviceType: DeviceTypeResponse) => void;
}

export const DeviceTypeCard: React.FC<DeviceTypeCardProps> = ({
  deviceType,
  onEdit,
  onDelete,
}) => {
  const icon = deviceType.icon || '📦';
  const color = deviceType.color || '#6b7280';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.2 }}
    >
      <Card
        className={cn(
          'p-5 transition-all duration-200 group',
          'hover:shadow-xl hover:scale-[1.02]',
          'border-l-4'
        )}
        style={{ borderLeftColor: color }}
      >
        <div className="flex items-start gap-4">
          {/* Icon Section */}
          <div
            className="p-3 rounded-xl glass border-2 group-hover:scale-110 transition-transform duration-200"
            style={{ borderColor: color + '40', backgroundColor: color + '10' }}
          >
            <span className="text-3xl" role="img" aria-label={deviceType.name}>
              {icon}
            </span>
          </div>

          {/* Content Section */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-semibold text-foreground truncate">
                  {deviceType.name}
                </h3>
                {deviceType.description && (
                  <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                    {deviceType.description}
                  </p>
                )}
              </div>
            </div>

            {/* Color Badge */}
            <div className="flex items-center gap-2 mb-3">
              <div
                className="px-2.5 py-1 rounded-full text-xs font-medium border-2 flex items-center gap-1.5"
                style={{
                  color: color,
                  borderColor: color + '40',
                  backgroundColor: color + '10',
                }}
              >
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: color }}
                />
                <span className="font-mono">{deviceType.slug}</span>
              </div>
            </div>

            {/* Stats Section */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 px-3 py-2 glass rounded-lg border border-border">
                <Package className="w-4 h-4 text-electric" />
                <span className="text-sm text-muted-foreground">Models:</span>
                <span className="text-sm font-mono font-bold text-electric">
                  {deviceType.model_count}
                </span>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2">
                {onEdit && (
                  <IconButton
                    icon={Pencil}
                    variant="outline"
                    size="sm"
                    tooltip="Edit Device Type"
                    onClick={(e) => {
                      e.stopPropagation();
                      onEdit(deviceType);
                    }}
                  />
                )}
                {onDelete && (
                  <IconButton
                    icon={Trash2}
                    variant="danger"
                    size="sm"
                    tooltip="Delete Device Type"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(deviceType);
                    }}
                  />
                )}
              </div>
            </div>
          </div>
        </div>
      </Card>
    </motion.div>
  );
};
