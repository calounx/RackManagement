import React from 'react';
import { motion } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../ui/card';
import { IconButton } from '../ui/icon-button';
import { Badge } from '../ui/badge';
import type { ModelResponse } from '../../types/catalog';
import { Pencil, Trash2, ExternalLink, Ruler, Zap, Package, Thermometer } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ModelCardProps {
  model: ModelResponse;
  onEdit?: (model: ModelResponse) => void;
  onDelete?: (model: ModelResponse) => void;
}

// Device type color mapping (matches existing style)
const DEVICE_TYPE_COLORS: Record<string, string> = {
  server: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  switch: 'bg-green-500/10 text-green-400 border-green-500/30',
  router: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
  firewall: 'bg-red-500/10 text-red-400 border-red-500/30',
  storage: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
  pdu: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
  ups: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
  patch_panel: 'bg-pink-500/10 text-pink-400 border-pink-500/30',
  other: 'bg-gray-500/10 text-gray-400 border-gray-500/30',
};

// Device type icons
const DEVICE_TYPE_ICONS: Record<string, string> = {
  server: '🖥️',
  switch: '🔀',
  router: '📡',
  firewall: '🛡️',
  storage: '💾',
  pdu: '⚡',
  ups: '🔋',
  patch_panel: '🔌',
  other: '📦',
};

export const ModelCard: React.FC<ModelCardProps> = ({ model, onEdit, onDelete }) => {
  const deviceTypeColor = DEVICE_TYPE_COLORS[model.device_type.slug] || DEVICE_TYPE_COLORS.other;
  const deviceTypeIcon = DEVICE_TYPE_ICONS[model.device_type.slug] || DEVICE_TYPE_ICONS.other;

  const handleDatasheetClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (model.datasheet_url) {
      window.open(model.datasheet_url, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card
        interactive
        className="group hover:border-electric/30 transition-all duration-200 hover:shadow-xl"
      >
        <CardHeader className="pb-3">
          <div className="flex items-start gap-4">
            {/* Product Image or Icon */}
            <div className="w-16 h-16 rounded-lg glass border border-electric/20 flex items-center justify-center overflow-hidden group-hover:scale-105 transition-transform duration-200">
              {model.image_url ? (
                <img
                  src={model.image_url}
                  alt={model.name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                    e.currentTarget.parentElement!.innerHTML = `<span class="text-3xl">${deviceTypeIcon}</span>`;
                  }}
                />
              ) : (
                <span className="text-3xl">{deviceTypeIcon}</span>
              )}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <CardTitle className="text-base truncate">{model.name}</CardTitle>
                  {model.brand.logo_url ? (
                    <div className="flex items-center gap-2 mt-1">
                      <img
                        src={model.brand.logo_url}
                        alt={model.brand.name}
                        className="h-4 object-contain"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                          e.currentTarget.nextElementSibling!.classList.remove('hidden');
                        }}
                      />
                      <p className="hidden text-sm text-muted-foreground font-medium">
                        {model.brand.name}
                      </p>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground font-medium mt-1">
                      {model.brand.name}
                    </p>
                  )}
                </div>

                {/* Confidence Badge */}
                {model.confidence && (
                  <Badge
                    variant="default"
                    className={cn(
                      'text-xs',
                      model.confidence === 'high' && 'bg-green-500/10 text-green-400 border-green-500/30',
                      model.confidence === 'medium' && 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
                      model.confidence === 'low' && 'bg-red-500/10 text-red-400 border-red-500/30'
                    )}
                  >
                    {model.confidence} confidence
                  </Badge>
                )}
              </div>

              {/* Device Type Badge */}
              <div className="flex items-center gap-2 mt-2">
                <div className={cn('px-2 py-0.5 rounded-full border text-xs font-medium', deviceTypeColor)}>
                  <span className="mr-1">{deviceTypeIcon}</span>
                  {model.device_type.name}
                </div>
                {model.variant && (
                  <span className="text-xs text-muted-foreground">({model.variant})</span>
                )}
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-3">
          {/* Key Specifications Grid */}
          <div className="grid grid-cols-3 gap-2">
            <div className="glass rounded-lg p-2.5 border border-border hover:border-electric/30 transition-colors">
              <div className="flex items-center justify-center gap-1.5 mb-1">
                <Ruler className="h-3.5 w-3.5 text-muted-foreground" />
                <p className="text-xs text-muted-foreground font-medium">Height</p>
              </div>
              <p className="font-mono text-foreground font-bold text-center text-lg">
                {model.height_u}U
              </p>
            </div>

            {model.power_watts && (
              <div className="glass rounded-lg p-2.5 border border-border hover:border-amber/30 transition-colors">
                <div className="flex items-center justify-center gap-1.5 mb-1">
                  <Zap className="h-3.5 w-3.5 text-amber" />
                  <p className="text-xs text-muted-foreground font-medium">Power</p>
                </div>
                <p className="font-mono text-amber font-bold text-center text-sm">
                  {model.power_watts}W
                </p>
              </div>
            )}

            {model.depth_mm && (
              <div className="glass rounded-lg p-2.5 border border-border hover:border-electric/30 transition-colors">
                <div className="flex items-center justify-center gap-1.5 mb-1">
                  <Package className="h-3.5 w-3.5 text-muted-foreground" />
                  <p className="text-xs text-muted-foreground font-medium">Depth</p>
                </div>
                <p className="font-mono text-foreground font-bold text-center text-sm">
                  {model.depth_mm}mm
                </p>
              </div>
            )}
          </div>

          {/* Additional specs row */}
          {(model.heat_output_btu || model.max_operating_temp_c) && (
            <div className="flex gap-2">
              {model.heat_output_btu && (
                <div className="flex-1 glass rounded-lg p-2 border border-border">
                  <div className="flex items-center gap-1.5">
                    <Thermometer className="h-3 w-3 text-red-400" />
                    <p className="text-xs text-muted-foreground">Heat Output</p>
                  </div>
                  <p className="font-mono text-xs font-semibold text-red-400 mt-0.5">
                    {model.heat_output_btu} BTU
                  </p>
                </div>
              )}
              {model.max_operating_temp_c && (
                <div className="flex-1 glass rounded-lg p-2 border border-border">
                  <div className="flex items-center gap-1.5">
                    <Thermometer className="h-3 w-3 text-muted-foreground" />
                    <p className="text-xs text-muted-foreground">Max Temp</p>
                  </div>
                  <p className="font-mono text-xs font-semibold text-foreground mt-0.5">
                    {model.max_operating_temp_c}°C
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Description */}
          {model.description && (
            <p className="text-xs text-muted-foreground line-clamp-2 px-2">
              {model.description}
            </p>
          )}

          {/* Source info if fetched */}
          {model.source && (
            <div className="text-xs text-muted-foreground/70 italic px-2">
              Source: {model.source}
            </div>
          )}
        </CardContent>

        <CardFooter className="pt-3">
          <div className="flex gap-2 w-full">
            {model.datasheet_url && (
              <IconButton
                icon={ExternalLink}
                variant="outline"
                size="md"
                tooltip="View Datasheet"
                onClick={handleDatasheetClick}
                className="flex-1"
              />
            )}
            {onEdit && (
              <IconButton
                icon={Pencil}
                variant="outline"
                size="md"
                tooltip="Edit Model"
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(model);
                }}
                className={model.datasheet_url ? '' : 'flex-1'}
              />
            )}
            {onDelete && (
              <IconButton
                icon={Trash2}
                variant="danger"
                size="md"
                tooltip="Delete Model"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(model);
                }}
              />
            )}
          </div>
        </CardFooter>
      </Card>
    </motion.div>
  );
};
