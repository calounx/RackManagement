import React, { useState } from 'react';
import { Dialog, DialogFooter } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { AlertCircle, Globe, Info, CheckCircle } from 'lucide-react';
import type { BrandInfoResponse } from '../../types/catalog';
import { useCatalogStore } from '../../store/useCatalogStore';
import { getCatalogErrorMessage } from '../../lib/api-catalog';
// import { cn } from '../../lib/utils'; // Removed unused import

interface BrandFetchDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

type FetchState = 'idle' | 'fetching' | 'preview' | 'saving';

export const BrandFetchDialog: React.FC<BrandFetchDialogProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { fetchBrandInfo, createBrand } = useCatalogStore();

  const [brandName, setBrandName] = useState('');
  const [fetchState, setFetchState] = useState<FetchState>('idle');
  const [fetchedData, setFetchedData] = useState<BrandInfoResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Editable fields in preview mode
  const [editedData, setEditedData] = useState<Partial<BrandInfoResponse>>({});

  const handleFetch = async () => {
    if (!brandName.trim()) {
      setError('Please enter a brand name');
      return;
    }

    setFetchState('fetching');
    setError(null);

    try {
      const data = await fetchBrandInfo(brandName.trim());

      // Data fetched successfully, show preview
      setFetchedData(data);
      setEditedData(data);
      setFetchState('preview');
    } catch (err: any) {
      const errorMessage = getCatalogErrorMessage(err);
      setError(errorMessage);
      setFetchState('idle');
    }
  };

  const handleSave = async () => {
    if (!editedData) return;

    setFetchState('saving');
    setError(null);

    try {
      // Create the brand with the edited data
      await createBrand({
        name: editedData.name!,
        slug: editedData.slug!,
        website: editedData.website || undefined,
        logo_url: editedData.logo_url || undefined,
        description: editedData.description || undefined,
        founded_year: editedData.founded_year || undefined,
        headquarters: editedData.headquarters || undefined,
      });

      onSuccess?.();
      handleClose();
    } catch (err) {
      setError(getCatalogErrorMessage(err));
      setFetchState('preview');
    }
  };

  const handleClose = () => {
    setBrandName('');
    setFetchState('idle');
    setFetchedData(null);
    setEditedData({});
    setError(null);
    onClose();
  };

  const handleEditChange = (field: keyof BrandInfoResponse, value: any) => {
    setEditedData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={handleClose}
      title="Fetch Brand from Web"
      description="Automatically fetch brand information from Wikipedia and other sources"
      size="lg"
    >
      <div className="space-y-5">
        {/* Info Banner */}
        <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg flex items-start gap-3">
          <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-medium text-blue-400 mb-1">Auto-fetch Brand Data</h4>
            <p className="text-sm text-blue-300">
              Enter a brand name to automatically fetch information from Wikipedia and other sources.
              You can preview and edit the data before saving.
            </p>
          </div>
        </div>

        {/* Input Section */}
        {fetchState !== 'preview' && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Brand Name
              </label>
              <Input
                type="text"
                value={brandName}
                onChange={(e) => {
                  setBrandName(e.target.value);
                  setError(null);
                }}
                placeholder="e.g., Dell, Cisco, HPE"
                disabled={fetchState === 'fetching'}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleFetch();
                  }
                }}
              />
            </div>

            <Button
              variant="primary"
              onClick={handleFetch}
              loading={fetchState === 'fetching'}
              leftIcon={<Globe className="w-4 h-4" />}
              className="w-full"
            >
              Fetch from Wikipedia
            </Button>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="p-4 border rounded-lg flex items-start gap-3 bg-red-500/10 border-red-500/30">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-red-400" />
            <div>
              <h4 className="text-sm font-medium mb-1 text-red-400">
                Error
              </h4>
              <p className="text-sm text-red-300">
                {error}
              </p>
            </div>
          </div>
        )}

        {/* Preview Section */}
        {fetchState === 'preview' && fetchedData && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-foreground">Preview Fetched Data</h3>
              {fetchedData.fetch_confidence && (
                <Badge
                  variant={
                    fetchedData.fetch_confidence === 'high'
                      ? 'success'
                      : fetchedData.fetch_confidence === 'medium'
                      ? 'warning'
                      : 'info'
                  }
                  glow
                >
                  {fetchedData.fetch_confidence} confidence
                </Badge>
              )}
            </div>

            {fetchedData.fetch_source && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Globe className="w-3.5 h-3.5" />
                <span>Source: {fetchedData.fetch_source}</span>
              </div>
            )}

            {/* Editable Fields */}
            <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
              {/* Name */}
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Brand Name
                </label>
                <Input
                  value={editedData.name || ''}
                  onChange={(e) => handleEditChange('name', e.target.value)}
                  className="text-sm"
                />
              </div>

              {/* Slug */}
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Slug
                </label>
                <Input
                  value={editedData.slug || ''}
                  onChange={(e) => handleEditChange('slug', e.target.value)}
                  className="text-sm font-mono"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Description
                </label>
                <textarea
                  value={editedData.description || ''}
                  onChange={(e) => handleEditChange('description', e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 bg-card border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-electric transition-all resize-none"
                />
              </div>

              {/* Website */}
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Website
                </label>
                <Input
                  type="url"
                  value={editedData.website || ''}
                  onChange={(e) => handleEditChange('website', e.target.value)}
                  className="text-sm"
                />
              </div>

              {/* Logo URL */}
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Logo URL
                </label>
                <Input
                  type="url"
                  value={editedData.logo_url || ''}
                  onChange={(e) => handleEditChange('logo_url', e.target.value)}
                  className="text-sm"
                />
                {editedData.logo_url && (
                  <div className="mt-2 p-2 bg-secondary/30 border border-border rounded-lg">
                    <img
                      src={editedData.logo_url}
                      alt="Logo preview"
                      className="h-12 object-contain"
                    />
                  </div>
                )}
              </div>

              {/* Headquarters */}
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Headquarters
                </label>
                <Input
                  value={editedData.headquarters || ''}
                  onChange={(e) => handleEditChange('headquarters', e.target.value)}
                  className="text-sm"
                />
              </div>

              {/* Founded Year */}
              <div>
                <label className="block text-xs font-medium text-muted-foreground mb-1">
                  Founded Year
                </label>
                <Input
                  type="number"
                  value={editedData.founded_year || ''}
                  onChange={(e) => handleEditChange('founded_year', parseInt(e.target.value) || null)}
                  className="text-sm"
                />
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <DialogFooter>
          {fetchState === 'preview' || fetchState === 'saving' ? (
            <>
              <Button
                variant="ghost"
                onClick={() => {
                  setFetchState('idle');
                  setFetchedData(null);
                  setEditedData({});
                }}
                disabled={fetchState === 'saving'}
              >
                Back
              </Button>
              <Button
                variant="primary"
                onClick={handleSave}
                loading={fetchState === 'saving'}
                leftIcon={<CheckCircle className="w-4 h-4" />}
              >
                Save Brand
              </Button>
            </>
          ) : (
            <Button variant="ghost" onClick={handleClose}>
              Close
            </Button>
          )}
        </DialogFooter>
      </div>
    </Dialog>
  );
};
