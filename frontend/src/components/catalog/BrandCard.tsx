import React from 'react';
import { ExternalLink, Building2, MapPin, Calendar, Pencil, Trash2, Package } from 'lucide-react';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import type { BrandResponse } from '../../types/catalog';

interface BrandCardProps {
  brand: BrandResponse;
  onEdit: (brand: BrandResponse) => void;
  onDelete: (brand: BrandResponse) => void;
  onViewModels: (brand: BrandResponse) => void;
}

export const BrandCard: React.FC<BrandCardProps> = ({
  brand,
  onEdit,
  onDelete,
  onViewModels,
}) => {
  return (
    <Card className="p-5 hover:border-electric/40 transition-all duration-300 group">
      <div className="flex items-start gap-4">
        {/* Logo Section */}
        <div className="flex-shrink-0">
          {brand.logo_url ? (
            <div className="w-16 h-16 rounded-lg bg-secondary/30 border border-border overflow-hidden flex items-center justify-center">
              <img
                src={brand.logo_url}
                alt={`${brand.name} logo`}
                className="w-full h-full object-contain p-2"
                onError={(e) => {
                  // Fallback to icon if image fails to load
                  const target = e.target as HTMLImageElement;
                  target.style.display = 'none';
                  const parent = target.parentElement;
                  if (parent) {
                    const icon = document.createElement('div');
                    icon.className = 'w-full h-full flex items-center justify-center text-muted-foreground';
                    icon.innerHTML = '<svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path></svg>';
                    parent.appendChild(icon);
                  }
                }}
              />
            </div>
          ) : (
            <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-electric/20 to-electric-blue/20 border border-electric/30 flex items-center justify-center">
              <Building2 className="w-8 h-8 text-electric" />
            </div>
          )}
        </div>

        {/* Content Section */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-start justify-between gap-3 mb-3">
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold text-foreground mb-1 truncate">
                {brand.name}
              </h3>
              <p className="text-xs text-muted-foreground font-mono">
                {brand.slug}
              </p>
            </div>

            {/* Fetch Confidence Badge */}
            {brand.fetch_confidence && (
              <Badge
                variant={
                  brand.fetch_confidence === 'high'
                    ? 'success'
                    : brand.fetch_confidence === 'medium'
                    ? 'warning'
                    : 'info'
                }
                glow
                className="flex-shrink-0"
              >
                {brand.fetch_confidence} confidence
              </Badge>
            )}
          </div>

          {/* Description */}
          {brand.description && (
            <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
              {brand.description}
            </p>
          )}

          {/* Metadata Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-3">
            {/* Website */}
            {brand.website && (
              <a
                href={brand.website}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-xs text-electric hover:text-electric-blue transition-colors group/link"
              >
                <ExternalLink className="w-3.5 h-3.5 flex-shrink-0" />
                <span className="truncate group-hover/link:underline">
                  {brand.website.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                </span>
              </a>
            )}

            {/* Headquarters */}
            {brand.headquarters && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <MapPin className="w-3.5 h-3.5 flex-shrink-0" />
                <span className="truncate">{brand.headquarters}</span>
              </div>
            )}

            {/* Founded Year */}
            {brand.founded_year && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Calendar className="w-3.5 h-3.5 flex-shrink-0" />
                <span>Founded {brand.founded_year}</span>
              </div>
            )}

            {/* Fetch Source */}
            {brand.fetch_source && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Building2 className="w-3.5 h-3.5 flex-shrink-0" />
                <span className="truncate">Source: {brand.fetch_source}</span>
              </div>
            )}
          </div>

          {/* Stats and Actions */}
          <div className="flex items-center justify-between pt-3 border-t border-border">
            {/* Model Count */}
            <button
              onClick={() => onViewModels(brand)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors"
            >
              <Package className="w-4 h-4 text-electric" />
              <span className="text-sm font-medium text-foreground">
                {brand.model_count}
              </span>
              <span className="text-xs text-muted-foreground">
                {brand.model_count === 1 ? 'model' : 'models'}
              </span>
            </button>

            {/* Action Buttons */}
            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onEdit(brand)}
                leftIcon={<Pencil className="w-3.5 h-3.5" />}
              >
                Edit
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onDelete(brand)}
                className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                leftIcon={<Trash2 className="w-3.5 h-3.5" />}
              >
                Delete
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};
