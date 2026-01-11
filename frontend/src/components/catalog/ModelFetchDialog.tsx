import React, { useState, useEffect } from 'react';
import { Dialog, DialogFooter } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { useCatalogStore } from '../../store/useCatalogStore';
import type { ModelResponse } from '../../types/catalog';
import { AlertCircle, CheckCircle, Globe, Search } from 'lucide-react';
import { cn } from '../../lib/utils';
import axios from 'axios';

interface ModelFetchDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const ModelFetchDialog: React.FC<ModelFetchDialogProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { brands, fetchBrands, fetchModelSpecs, createModel, modelsLoading } = useCatalogStore();

  const [selectedBrandId, setSelectedBrandId] = useState<number>(0);
  const [modelName, setModelName] = useState('');
  const [fetchedData, setFetchedData] = useState<ModelResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isFetching, setIsFetching] = useState(false);
  const [isNotImplemented, setIsNotImplemented] = useState(false);

  // Load brands on mount
  useEffect(() => {
    if (isOpen) {
      fetchBrands({ page_size: 1000 });
    }
  }, [isOpen, fetchBrands]);

  // Reset on open/close
  useEffect(() => {
    if (isOpen) {
      setSelectedBrandId(0);
      setModelName('');
      setFetchedData(null);
      setError(null);
      setIsNotImplemented(false);
    }
  }, [isOpen]);

  const handleFetch = async () => {
    if (!selectedBrandId || !modelName.trim()) {
      setError('Please select a brand and enter a model name');
      return;
    }

    const selectedBrand = brands.find((b) => b.id === selectedBrandId);
    if (!selectedBrand) {
      setError('Invalid brand selected');
      return;
    }

    setIsFetching(true);
    setError(null);
    setFetchedData(null);
    setIsNotImplemented(false);

    try {
      const data = await fetchModelSpecs(selectedBrand.name, modelName);
      setFetchedData(data);
    } catch (err) {
      // Check if it's a 501 Not Implemented error
      if (axios.isAxiosError(err) && err.response?.status === 501) {
        setIsNotImplemented(true);
        setError(
          'Model specification fetching is not yet implemented. This feature will be available in Phase 5 of the project.'
        );
      } else {
        setError(
          axios.isAxiosError(err)
            ? err.response?.data?.detail || err.message
            : 'Failed to fetch model specifications'
        );
      }
    } finally {
      setIsFetching(false);
    }
  };

  const handleSave = async () => {
    if (!fetchedData) return;

    try {
      await createModel({
        brand_id: fetchedData.brand_id,
        device_type_id: fetchedData.device_type_id,
        name: fetchedData.name,
        variant: fetchedData.variant,
        description: fetchedData.description,
        height_u: fetchedData.height_u,
        width_type: fetchedData.width_type,
        depth_mm: fetchedData.depth_mm,
        weight_kg: fetchedData.weight_kg,
        power_watts: fetchedData.power_watts,
        heat_output_btu: fetchedData.heat_output_btu,
        airflow_pattern: fetchedData.airflow_pattern,
        max_operating_temp_c: fetchedData.max_operating_temp_c,
        typical_ports: fetchedData.typical_ports,
        mounting_type: fetchedData.mounting_type,
        datasheet_url: fetchedData.datasheet_url,
        image_url: fetchedData.image_url,
        release_date: fetchedData.release_date,
        end_of_life: fetchedData.end_of_life,
        source: fetchedData.source,
        confidence: fetchedData.confidence,
      });

      onSuccess?.();
      onClose();
    } catch (err) {
      setError(
        axios.isAxiosError(err)
          ? err.response?.data?.detail || err.message
          : 'Failed to save model'
      );
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title="Fetch Model Specifications"
      description="Automatically fetch device specifications from manufacturer websites and databases"
      size="lg"
    >
      <div className="space-y-6">
        {/* Input Section */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">
              Brand <span className="text-red-500">*</span>
            </label>
            <select
              value={selectedBrandId}
              onChange={(e) => setSelectedBrandId(parseInt(e.target.value, 10))}
              disabled={isFetching}
              className="w-full px-3 py-2 bg-card border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-electric disabled:opacity-50"
            >
              <option value={0}>Select a brand...</option>
              {brands.map((brand) => (
                <option key={brand.id} value={brand.id}>
                  {brand.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">
              Model Name <span className="text-red-500">*</span>
            </label>
            <Input
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              placeholder="e.g., PowerEdge R740, Catalyst 2960"
              disabled={isFetching}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleFetch();
                }
              }}
            />
          </div>

          <Button
            type="button"
            variant="primary"
            onClick={handleFetch}
            loading={isFetching}
            disabled={!selectedBrandId || !modelName.trim()}
            leftIcon={<Search className="w-4 h-4" />}
            className="w-full"
          >
            Fetch Specifications
          </Button>
        </div>

        {/* Error Message */}
        {error && (
          <div
            className={cn(
              'p-4 rounded-lg border flex items-start gap-3',
              isNotImplemented
                ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
                : 'bg-red-500/10 border-red-500/30 text-red-400'
            )}
          >
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div className="flex-1 text-sm">
              <p className="font-medium mb-1">
                {isNotImplemented ? 'Feature Not Yet Available' : 'Error'}
              </p>
              <p className="text-xs opacity-90">{error}</p>
              {isNotImplemented && (
                <p className="text-xs opacity-75 mt-2">
                  In the meantime, you can manually add models using the "Add Model" button.
                </p>
              )}
            </div>
          </div>
        )}

        {/* Fetched Data Preview */}
        {fetchedData && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-400" />
              <div className="flex-1">
                <p className="text-sm font-medium text-green-400">
                  Specifications fetched successfully
                </p>
                <p className="text-xs text-green-400/70 mt-0.5">
                  Review the data below and click "Save Model" to add it to your catalog
                </p>
              </div>
            </div>

            {/* Preview Card */}
            <div className="glass rounded-lg p-4 border border-electric/20 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-foreground text-lg">
                    {fetchedData.name}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {fetchedData.brand.name}
                  </p>
                </div>
                {fetchedData.confidence && (
                  <Badge
                    variant="default"
                    className={cn(
                      'text-xs',
                      fetchedData.confidence === 'high' &&
                        'bg-green-500/10 text-green-400 border-green-500/30',
                      fetchedData.confidence === 'medium' &&
                        'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
                      fetchedData.confidence === 'low' &&
                        'bg-red-500/10 text-red-400 border-red-500/30'
                    )}
                  >
                    {fetchedData.confidence} confidence
                  </Badge>
                )}
              </div>

              {/* Device Type */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Device Type:</span>
                <Badge variant="default" className="text-xs">
                  {fetchedData.device_type.icon} {fetchedData.device_type.name}
                </Badge>
              </div>

              {/* Key Specs */}
              <div className="grid grid-cols-3 gap-2 pt-2">
                <div className="p-2 bg-secondary/30 rounded text-center">
                  <p className="text-xs text-muted-foreground">Height</p>
                  <p className="text-sm font-mono font-bold text-electric">
                    {fetchedData.height_u}U
                  </p>
                </div>
                {fetchedData.power_watts && (
                  <div className="p-2 bg-secondary/30 rounded text-center">
                    <p className="text-xs text-muted-foreground">Power</p>
                    <p className="text-sm font-mono font-bold text-amber">
                      {fetchedData.power_watts}W
                    </p>
                  </div>
                )}
                {fetchedData.depth_mm && (
                  <div className="p-2 bg-secondary/30 rounded text-center">
                    <p className="text-xs text-muted-foreground">Depth</p>
                    <p className="text-sm font-mono font-bold text-foreground">
                      {fetchedData.depth_mm}mm
                    </p>
                  </div>
                )}
              </div>

              {/* Description */}
              {fetchedData.description && (
                <p className="text-xs text-muted-foreground pt-2 border-t border-border">
                  {fetchedData.description}
                </p>
              )}

              {/* Source */}
              {fetchedData.source && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground pt-2 border-t border-border">
                  <Globe className="w-3.5 h-3.5" />
                  <span>Source: {fetchedData.source}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Footer */}
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose} disabled={modelsLoading}>
            {fetchedData ? 'Cancel' : 'Close'}
          </Button>
          {fetchedData && (
            <Button
              type="button"
              variant="primary"
              onClick={handleSave}
              loading={modelsLoading}
            >
              Save Model
            </Button>
          )}
        </DialogFooter>
      </div>
    </Dialog>
  );
};
