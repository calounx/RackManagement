import React, { useState, useEffect, useMemo } from 'react';
import { Dialog, DialogFooter } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input, TextArea, Select } from '../ui/input';
import { Combobox } from '../ui/combobox';
import { Collapsible } from '../ui/collapsible';
import { useStore } from '../../store/useStore';
import type { Device, DeviceType, DeviceSpec } from '../../types';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  CheckCircle2,
  Loader2,
  ExternalLink,
  Database,
  Info,
} from 'lucide-react';

interface DeviceDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: any) => void;
  device?: Device | null;
  mode: 'create' | 'edit';
}

const DEVICE_TYPES: Array<{ value: DeviceType; label: string }> = [
  { value: 'server', label: 'Server' },
  { value: 'switch', label: 'Switch' },
  { value: 'router', label: 'Router' },
  { value: 'firewall', label: 'Firewall' },
  { value: 'storage', label: 'Storage' },
  { value: 'pdu', label: 'PDU (Power Distribution Unit)' },
  { value: 'ups', label: 'UPS (Uninterruptible Power Supply)' },
  { value: 'patch_panel', label: 'Patch Panel' },
  { value: 'other', label: 'Other' },
];

export const DeviceDialog: React.FC<DeviceDialogProps> = ({
  isOpen,
  onClose,
  onSave,
  device,
  mode,
}) => {
  const { deviceSpecs, fetchDeviceSpecs, fetchSpecsFromUrl } = useStore();

  // Form state
  const [formData, setFormData] = useState({
    device_type: 'server' as DeviceType,
    manufacturer: '',
    model: '',
    custom_name: '',
    height_units: 1,
    power_consumption_watts: 0,
    weight_kg: 0,
    depth_mm: null as number | null,
    max_temperature_celsius: null as number | null,
    notes: '',
    datasheet_url: null as string | null,
  });

  const [isSearching, setIsSearching] = useState(false);
  const [searchResult, setSearchResult] = useState<'found' | 'not-found' | null>(null);
  const [existingSpec, setExistingSpec] = useState<DeviceSpec | null>(null);
  const [autoPopulatedFields, setAutoPopulatedFields] = useState<Set<string>>(new Set());
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Fetch device specs on mount
  useEffect(() => {
    if (isOpen) {
      fetchDeviceSpecs();
    }
  }, [isOpen, fetchDeviceSpecs]);

  // Populate form in edit mode
  useEffect(() => {
    if (device && mode === 'edit') {
      setFormData({
        device_type: (device.device_type as DeviceType) || 'server',
        manufacturer: device.manufacturer || '',
        model: device.model || '',
        custom_name: device.name || '',
        height_units: device.height_units || 1,
        power_consumption_watts: device.power_consumption_watts || 0,
        weight_kg: device.weight_kg || 0,
        depth_mm: null,
        max_temperature_celsius: device.temperature_celsius || null,
        notes: device.notes || '',
        datasheet_url: null,
      });
    } else {
      resetForm();
    }
  }, [device, mode, isOpen]);

  const resetForm = () => {
    setFormData({
      device_type: 'server',
      manufacturer: '',
      model: '',
      custom_name: '',
      height_units: 1,
      power_consumption_watts: 0,
      weight_kg: 0,
      depth_mm: null,
      max_temperature_celsius: null,
      notes: '',
      datasheet_url: null,
    });
    setErrors({});
    setSearchResult(null);
    setExistingSpec(null);
    setAutoPopulatedFields(new Set());
  };

  // Get unique brands from existing specs
  const availableBrands = useMemo(() => {
    const brands = Array.from(new Set(deviceSpecs.map((s) => s.manufacturer))).sort();
    return brands.map((brand) => ({ value: brand, label: brand }));
  }, [deviceSpecs]);

  // Get models for selected brand
  const availableModels = useMemo(() => {
    if (!formData.manufacturer) return [];
    const models = deviceSpecs
      .filter((s) => s.manufacturer.toLowerCase() === formData.manufacturer.toLowerCase())
      .map((s) => s.model)
      .sort();
    return Array.from(new Set(models)).map((model) => ({ value: model, label: model }));
  }, [deviceSpecs, formData.manufacturer]);

  // Check if brand+model matches existing spec
  const matchingSpec = useMemo(() => {
    if (!formData.manufacturer || !formData.model) return null;
    return deviceSpecs.find(
      (s) =>
        s.manufacturer.toLowerCase() === formData.manufacturer.toLowerCase() &&
        s.model.toLowerCase() === formData.model.toLowerCase()
    );
  }, [deviceSpecs, formData.manufacturer, formData.model]);

  // Auto-populate from matching spec
  useEffect(() => {
    if (matchingSpec && mode === 'create') {
      setExistingSpec(matchingSpec);
      const newAutoPopulated = new Set<string>();

      setFormData((prev) => {
        const updated = { ...prev };

        // Only auto-populate if fields haven't been manually changed
        if (prev.height_units === 1) {
          updated.height_units = matchingSpec.height_units;
          newAutoPopulated.add('height_units');
        }
        if (prev.power_consumption_watts === 0) {
          updated.power_consumption_watts = matchingSpec.power_consumption_watts;
          newAutoPopulated.add('power_consumption_watts');
        }
        if (prev.weight_kg === 0) {
          updated.weight_kg = matchingSpec.weight_kg;
          newAutoPopulated.add('weight_kg');
        }
        if (matchingSpec.max_temperature_celsius && !prev.max_temperature_celsius) {
          updated.max_temperature_celsius = matchingSpec.max_temperature_celsius;
          newAutoPopulated.add('max_temperature_celsius');
        }
        if (matchingSpec.dimensions_mm && !prev.depth_mm) {
          const depthMatch = matchingSpec.dimensions_mm.match(/(\d+\.?\d*)/);
          if (depthMatch) {
            updated.depth_mm = parseFloat(depthMatch[1]);
            newAutoPopulated.add('depth_mm');
          }
        }
        if (matchingSpec.datasheet_url && !prev.datasheet_url) {
          updated.datasheet_url = matchingSpec.datasheet_url;
          newAutoPopulated.add('datasheet_url');
        }

        return updated;
      });

      setAutoPopulatedFields(newAutoPopulated);
      setSearchResult('found');
    } else if (!matchingSpec && existingSpec) {
      setExistingSpec(null);
      setSearchResult(null);
      setAutoPopulatedFields(new Set());
    }
  }, [matchingSpec, mode, existingSpec]);

  // Search manufacturer database
  const handleSearchManufacturer = async () => {
    if (!formData.manufacturer || !formData.model) {
      setErrors({ ...errors, search: 'Please enter both manufacturer and model' });
      return;
    }

    setIsSearching(true);
    setSearchResult(null);
    setErrors({});

    try {
      const spec = await fetchSpecsFromUrl(formData.manufacturer, formData.model);
      if (spec) {
        setSearchResult('found');
        setExistingSpec(spec);
        const newAutoPopulated = new Set<string>([
          'height_units',
          'power_consumption_watts',
          'weight_kg',
        ]);

        // Auto-populate all fields from spec
        setFormData((prev) => ({
          ...prev,
          height_units: spec.height_units,
          power_consumption_watts: spec.power_consumption_watts,
          weight_kg: spec.weight_kg,
          max_temperature_celsius: spec.max_temperature_celsius || prev.max_temperature_celsius,
          datasheet_url: spec.datasheet_url || prev.datasheet_url,
          depth_mm: spec.dimensions_mm
            ? parseFloat(spec.dimensions_mm.match(/(\d+\.?\d*)/)![1])
            : prev.depth_mm,
        }));

        if (spec.max_temperature_celsius) newAutoPopulated.add('max_temperature_celsius');
        if (spec.datasheet_url) newAutoPopulated.add('datasheet_url');
        if (spec.dimensions_mm) newAutoPopulated.add('depth_mm');

        setAutoPopulatedFields(newAutoPopulated);
      } else {
        setSearchResult('not-found');
      }
    } catch (error) {
      setSearchResult('not-found');
    } finally {
      setIsSearching(false);
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.manufacturer.trim()) {
      newErrors.manufacturer = 'Manufacturer is required';
    }
    if (!formData.model.trim()) {
      newErrors.model = 'Model is required';
    }
    if (formData.height_units < 1 || formData.height_units > 48) {
      newErrors.height_units = 'Height must be between 1 and 48 units';
    }
    if (formData.power_consumption_watts < 0) {
      newErrors.power_consumption_watts = 'Power cannot be negative';
    }
    if (formData.weight_kg < 0) {
      newErrors.weight_kg = 'Weight cannot be negative';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    // If matching existing spec, use specification_id
    if (matchingSpec && mode === 'create') {
      onSave({
        specification_id: matchingSpec.id,
        custom_name: formData.custom_name || undefined,
        access_frequency: 'medium',
        notes: formData.notes || undefined,
      });
    } else {
      // Create new device with manual specs
      onSave({
        name: formData.custom_name || `${formData.manufacturer} ${formData.model}`,
        manufacturer: formData.manufacturer,
        model: formData.model,
        device_type: formData.device_type,
        height_units: formData.height_units,
        power_consumption_watts: formData.power_consumption_watts,
        weight_kg: formData.weight_kg,
        temperature_celsius: formData.max_temperature_celsius || undefined,
        notes: formData.notes || undefined,
      });
    }

    onClose();
    resetForm();
  };

  const canSearch =
    formData.manufacturer &&
    formData.model &&
    !isSearching &&
    !matchingSpec &&
    mode === 'create';

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={mode === 'create' ? 'Add New Device' : 'Edit Device'}
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Section 1: Device Identity */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground pb-2 border-b border-border">
            <Database className="w-4 h-4 text-electric" />
            Device Identity
          </div>

          {/* Device Type */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Device Type <span className="text-red-500">*</span>
            </label>
            <Select
              value={formData.device_type}
              onChange={(e) =>
                setFormData({ ...formData, device_type: e.target.value as DeviceType })
              }
              options={DEVICE_TYPES}
              disabled={mode === 'edit'}
            />
          </div>

          {/* Manufacturer */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Manufacturer/Brand <span className="text-red-500">*</span>
            </label>
            <Combobox
              value={formData.manufacturer}
              onChange={(value) => {
                setFormData({ ...formData, manufacturer: value });
                setErrors({ ...errors, manufacturer: '' });
              }}
              options={availableBrands}
              placeholder="e.g., Cisco, Dell, HPE, Ubiquiti"
              error={errors.manufacturer}
              allowCustom={true}
              disabled={mode === 'edit'}
            />
          </div>

          {/* Model */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Model <span className="text-red-500">*</span>
            </label>
            <Combobox
              value={formData.model}
              onChange={(value) => {
                setFormData({ ...formData, model: value });
                setErrors({ ...errors, model: '' });
              }}
              options={availableModels}
              placeholder="e.g., Catalyst 2960, PowerEdge R740"
              error={errors.model}
              allowCustom={true}
              disabled={mode === 'edit'}
            />
          </div>

          {/* Auto-Search Integration */}
          {mode === 'create' && (
            <AnimatePresence mode="wait">
              {matchingSpec ? (
                <motion.div
                  key="found-existing"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="p-4 bg-electric/10 border border-electric/30 rounded-lg"
                >
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-electric flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-electric mb-1">
                        Specifications Found in Database
                      </p>
                      <p className="text-xs text-muted-foreground mb-3">
                        Using existing specifications for {matchingSpec.manufacturer}{' '}
                        {matchingSpec.model}
                      </p>
                      <div className="grid grid-cols-3 gap-2">
                        <div className="p-2 bg-background/50 rounded">
                          <span className="text-xs text-muted-foreground block">Height</span>
                          <span className="text-sm text-electric font-mono font-bold">
                            {matchingSpec.height_units}U
                          </span>
                        </div>
                        <div className="p-2 bg-background/50 rounded">
                          <span className="text-xs text-muted-foreground block">Power</span>
                          <span className="text-sm text-electric font-mono font-bold">
                            {matchingSpec.power_consumption_watts}W
                          </span>
                        </div>
                        <div className="p-2 bg-background/50 rounded">
                          <span className="text-xs text-muted-foreground block">Weight</span>
                          <span className="text-sm text-electric font-mono font-bold">
                            {matchingSpec.weight_kg}kg
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              ) : canSearch ? (
                <motion.div
                  key="search-button"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                >
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleSearchManufacturer}
                    disabled={isSearching}
                    className="w-full border-electric/30 hover:bg-electric/5 hover:border-electric"
                  >
                    {isSearching ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                        Searching Manufacturer Database...
                      </>
                    ) : (
                      <>
                        <Search className="w-4 h-4 mr-2" />
                        Search Manufacturer Database for Specs
                      </>
                    )}
                  </Button>

                  {searchResult === 'not-found' && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="mt-3 p-3 bg-muted/30 border border-border rounded-lg flex items-start gap-2"
                    >
                      <Info className="w-4 h-4 text-muted-foreground flex-shrink-0 mt-0.5" />
                      <p className="text-xs text-muted-foreground">
                        No specifications found in manufacturer database. Please enter
                        specifications manually below.
                      </p>
                    </motion.div>
                  )}
                </motion.div>
              ) : null}
            </AnimatePresence>
          )}
        </div>

        {/* Section 2: Specifications */}
        <Collapsible title="Physical Specifications" defaultOpen={true}>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Height (U) <span className="text-red-500">*</span>
                </label>
                <Input
                  type="number"
                  min="1"
                  max="48"
                  value={formData.height_units}
                  onChange={(e) => {
                    setFormData({ ...formData, height_units: parseInt(e.target.value) || 1 });
                    setErrors({ ...errors, height_units: '' });
                    setAutoPopulatedFields((prev) => {
                      const next = new Set(prev);
                      next.delete('height_units');
                      return next;
                    });
                  }}
                  error={errors.height_units}
                />
              </div>
              {autoPopulatedFields.has('height_units') && (
                <p className="text-xs text-electric mt-1 flex items-center gap-1">
                  <Database className="w-3 h-3" />
                  from database
                </p>
              )}
            </div>

            <div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Power (W) <span className="text-red-500">*</span>
                </label>
                <Input
                  type="number"
                  min="0"
                  value={formData.power_consumption_watts}
                  onChange={(e) => {
                    setFormData({
                      ...formData,
                      power_consumption_watts: parseInt(e.target.value) || 0,
                    });
                    setErrors({ ...errors, power_consumption_watts: '' });
                    setAutoPopulatedFields((prev) => {
                      const next = new Set(prev);
                      next.delete('power_consumption_watts');
                      return next;
                    });
                  }}
                  error={errors.power_consumption_watts}
                />
              </div>
              {autoPopulatedFields.has('power_consumption_watts') && (
                <p className="text-xs text-electric mt-1 flex items-center gap-1">
                  <Database className="w-3 h-3" />
                  from database
                </p>
              )}
            </div>

            <div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Weight (kg) <span className="text-red-500">*</span>
                </label>
                <Input
                  type="number"
                  min="0"
                  step="0.1"
                  value={formData.weight_kg}
                  onChange={(e) => {
                    setFormData({ ...formData, weight_kg: parseFloat(e.target.value) || 0 });
                    setErrors({ ...errors, weight_kg: '' });
                    setAutoPopulatedFields((prev) => {
                      const next = new Set(prev);
                      next.delete('weight_kg');
                      return next;
                    });
                  }}
                  error={errors.weight_kg}
                />
              </div>
              {autoPopulatedFields.has('weight_kg') && (
                <p className="text-xs text-electric mt-1 flex items-center gap-1">
                  <Database className="w-3 h-3" />
                  from database
                </p>
              )}
            </div>
          </div>

          <Input
            label="Depth (mm)"
            type="number"
            min="0"
            value={formData.depth_mm || ''}
            onChange={(e) => {
              setFormData({
                ...formData,
                depth_mm: e.target.value ? parseFloat(e.target.value) : null,
              });
              setAutoPopulatedFields((prev) => {
                const next = new Set(prev);
                next.delete('depth_mm');
                return next;
              });
            }}
            placeholder="Optional"
          />
          {autoPopulatedFields.has('depth_mm') && (
            <p className="text-xs text-electric -mt-2 flex items-center gap-1">
              <Database className="w-3 h-3" />
              from database
            </p>
          )}
        </Collapsible>

        {/* Operating Specs (Optional) */}
        <Collapsible title="Operating Specifications (Optional)">
          <Input
            label="Max Temperature (°C)"
            type="number"
            value={formData.max_temperature_celsius || ''}
            onChange={(e) => {
              setFormData({
                ...formData,
                max_temperature_celsius: e.target.value ? parseFloat(e.target.value) : null,
              });
              setAutoPopulatedFields((prev) => {
                const next = new Set(prev);
                next.delete('max_temperature_celsius');
                return next;
              });
            }}
            placeholder="e.g., 35"
          />
          {autoPopulatedFields.has('max_temperature_celsius') && (
            <p className="text-xs text-electric -mt-2 flex items-center gap-1">
              <Database className="w-3 h-3" />
              from database
            </p>
          )}

          <div className="p-3 bg-muted/30 rounded-lg border border-border">
            <p className="text-xs text-muted-foreground">
              Additional port configurations can be added after device creation.
            </p>
          </div>
        </Collapsible>

        {/* Additional Information */}
        <Collapsible title="Additional Information (Optional)">
          <Input
            label="Custom Name"
            value={formData.custom_name}
            onChange={(e) => setFormData({ ...formData, custom_name: e.target.value })}
            placeholder={`e.g., Core Switch 1 (defaults to "${formData.manufacturer} ${formData.model}")`}
          />

          <TextArea
            label="Notes"
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            placeholder="Additional notes about this device..."
            rows={3}
          />
        </Collapsible>

        {/* Documentation (Optional) */}
        {formData.datasheet_url && (
          <Collapsible title="Documentation">
            <div className="p-4 bg-secondary/30 rounded-lg border border-border">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-foreground mb-1">Datasheet</p>
                  {autoPopulatedFields.has('datasheet_url') && (
                    <p className="text-xs text-electric flex items-center gap-1 mb-2">
                      <Database className="w-3 h-3" />
                      from database
                    </p>
                  )}
                </div>
                <a
                  href={formData.datasheet_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm text-electric hover:text-electric/80 transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                  View Datasheet
                </a>
              </div>
            </div>
          </Collapsible>
        )}

        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary">
            {mode === 'create' ? 'Add Device' : 'Save Changes'}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
};
