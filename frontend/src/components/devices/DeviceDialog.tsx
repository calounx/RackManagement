import React, { useState, useEffect, useMemo } from 'react';
import { Dialog, DialogFooter } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input, TextArea } from '../ui/input';
import { Combobox } from '../ui/combobox';
import { Collapsible } from '../ui/collapsible';
import { useStore } from '../../store/useStore';
import type { Device, DeviceType } from '../../types';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircle2,
  
  Database,
  Info,
  AlertCircle,
  Sparkles,
} from 'lucide-react';

interface DeviceDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: any) => void;
  device?: Device | null;
  mode: 'create' | 'edit';
}

const DEVICE_TYPES: Array<{ value: DeviceType; label: string; icon: string }> = [
  { value: 'server', label: 'Server', icon: '🖥️' },
  { value: 'switch', label: 'Switch', icon: '🔀' },
  { value: 'router', label: 'Router', icon: '📡' },
  { value: 'firewall', label: 'Firewall', icon: '🛡️' },
  { value: 'storage', label: 'Storage', icon: '💾' },
  { value: 'pdu', label: 'PDU (Power Distribution Unit)', icon: '⚡' },
  { value: 'ups', label: 'UPS (Uninterruptible Power Supply)', icon: '🔋' },
  { value: 'patch_panel', label: 'Patch Panel', icon: '🔌' },
  { value: 'other', label: 'Other', icon: '📦' },
];

export const DeviceDialog: React.FC<DeviceDialogProps> = ({
  isOpen,
  onClose,
  onSave,
  device,
  mode,
}) => {
  const { deviceSpecs, fetchDeviceSpecs, createDeviceSpec, fetchSpecsFromUrl } = useStore();

  // Form state
  const [formData, setFormData] = useState({
    device_type: 'server' as DeviceType,
    manufacturer: '',
    model: '',
    custom_name: '',
    height_units: 1,
    power_consumption_watts: 0,
    weight_kg: 0,
    notes: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [willCreateNewSpec, setWillCreateNewSpec] = useState(false);
  const [isFetchingFromWeb, setIsFetchingFromWeb] = useState(false);

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
        notes: device.notes || '',
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
      notes: '',
    });
    setErrors({});
    // setExistingSpec(null);
    setWillCreateNewSpec(false);
    setIsFetchingFromWeb(false);
  };

  const handleFetchFromWeb = async () => {
    if (!formData.manufacturer || !formData.model) {
      setErrors({
        manufacturer: !formData.manufacturer ? 'Brand is required' : '',
        model: !formData.model ? 'Model is required' : '',
      });
      return;
    }

    setIsFetchingFromWeb(true);
    setErrors({});

    try {
      const fetchedSpec = await fetchSpecsFromUrl(formData.manufacturer, formData.model);

      if (fetchedSpec) {
        // Auto-populate form with fetched data
        setFormData(prev => ({
          ...prev,
          height_units: fetchedSpec.height_u,
          power_consumption_watts: fetchedSpec.power_watts,
          weight_kg: fetchedSpec.weight_kg,
        }));

        // Refresh device specs list
        await fetchDeviceSpecs();

        setErrors({ manufacturer: '' });
      } else {
        setErrors({ manufacturer: 'Could not fetch specifications from web. Please enter manually.' });
      }
    } catch (error) {
      console.error('Failed to fetch from web:', error);
      setErrors({ manufacturer: 'Failed to fetch from web. Please enter specifications manually.' });
    } finally {
      setIsFetchingFromWeb(false);
    }
  };

  // Get unique brands filtered by device type
  const availableBrands = useMemo(() => {
    if (!formData.device_type) return [];
    const brands = deviceSpecs
      .filter(s => s.device_type === formData.device_type)
      .map(s => s.brand);
    return Array.from(new Set(brands)).sort().map(brand => ({ value: brand, label: brand }));
  }, [deviceSpecs, formData.device_type]);

  // Get models for selected brand and device type
  const availableModels = useMemo(() => {
    if (!formData.manufacturer || !formData.device_type) return [];
    const models = deviceSpecs
      .filter(
        s =>
          s.brand.toLowerCase() === formData.manufacturer.toLowerCase() &&
          s.device_type === formData.device_type
      )
      .map(s => s.model)
      .sort();
    return Array.from(new Set(models)).map(model => ({ value: model, label: model }));
  }, [deviceSpecs, formData.manufacturer, formData.device_type]);

  // Check if brand+model+type matches existing spec
  const matchingSpec = useMemo(() => {
    if (!formData.manufacturer || !formData.model || !formData.device_type) return null;
    return deviceSpecs.find(
      s =>
        s.brand.toLowerCase() === formData.manufacturer.toLowerCase() &&
        s.model.toLowerCase() === formData.model.toLowerCase() &&
        s.device_type === formData.device_type
    );
  }, [deviceSpecs, formData.manufacturer, formData.model, formData.device_type]);

  // Auto-populate from matching spec
  useEffect(() => {
    if (matchingSpec && mode === 'create') {
      // setExistingSpec(matchingSpec);
      setWillCreateNewSpec(false);
      setFormData(prev => ({
        ...prev,
        height_units: matchingSpec.height_u,
        power_consumption_watts: matchingSpec.power_watts,
        weight_kg: matchingSpec.weight_kg,
      }));
    } else if (!matchingSpec && formData.manufacturer && formData.model) {
      // setExistingSpec(null);
      setWillCreateNewSpec(true);
    } else {
      // setExistingSpec(null);
      setWillCreateNewSpec(false);
    }
  }, [matchingSpec, mode, formData.manufacturer, formData.model]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.device_type) {
      newErrors.device_type = 'Device type is required';
    }
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      let specId = matchingSpec?.id;

      // If no matching spec exists, create a new one
      if (!matchingSpec) {
        const newSpec = await createDeviceSpec({
          brand: formData.manufacturer,
          model: formData.model,
          variant: null,
          height_u: formData.height_units,
          width_type: '19"',
          depth_mm: 450,
          weight_kg: formData.weight_kg,
          power_watts: formData.power_consumption_watts,
          heat_output_btu: Math.round(formData.power_consumption_watts * 3.41),
          airflow_pattern: 'front_to_back',
          max_operating_temp_c: 45,
          typical_ports: null,
          mounting_type: '4-post',
          source: 'user_custom',
          source_url: null,
          confidence: 'medium',
          fetched_at: null,
          last_updated: new Date().toISOString(),
          device_type: formData.device_type,
        });

        if (!newSpec) {
          throw new Error('Failed to create device specification');
        }

        specId = newSpec.id;

        // Refresh device specs list
        await fetchDeviceSpecs();
      }

      const submitData: any = {
        specification_id: specId,
        custom_name: formData.custom_name || undefined,
        notes: formData.notes || undefined,
      };

      await onSave(submitData);
      onClose();
      resetForm();
    } catch (error) {
      console.error('Failed to create device:', error);
      setErrors({ manufacturer: 'Failed to create device. Please try again.' });
    }
  };

  const selectedDeviceTypeInfo = DEVICE_TYPES.find(dt => dt.value === formData.device_type);

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={mode === 'create' ? 'Add New Device' : 'Edit Device'}
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Step 1: Device Type */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground pb-2 border-b border-border">
            <div className="text-lg">{selectedDeviceTypeInfo?.icon || '📦'}</div>
            <span>Step 1: Select Device Type</span>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Device Type <span className="text-red-500">*</span>
            </label>
            <div className="grid grid-cols-3 gap-2">
              {DEVICE_TYPES.map(type => (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => {
                    setFormData({
                      ...formData,
                      device_type: type.value,
                      manufacturer: '',
                      model: '',
                    });
                    setErrors({ ...errors, device_type: '' });
                  }}
                  disabled={mode === 'edit'}
                  className={`p-3 rounded-lg border-2 transition-all text-left ${
                    formData.device_type === type.value
                      ? 'border-electric bg-electric/10 text-electric'
                      : 'border-border hover:border-electric/50 text-muted-foreground hover:text-foreground'
                  } ${mode === 'edit' ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <div className="text-xl mb-1">{type.icon}</div>
                  <div className="text-xs font-medium">{type.label.split('(')[0].trim()}</div>
                </button>
              ))}
            </div>
            {errors.device_type && (
              <p className="text-xs text-red-500 mt-1">{errors.device_type}</p>
            )}
          </div>
        </div>

        {/* Step 2 & 3: Brand and Model */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-foreground pb-2 border-b border-border">
            <Database className="w-4 h-4 text-electric" />
            <span>Step 2: Identify Device</span>
          </div>

          {/* Manufacturer */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Manufacturer/Brand <span className="text-red-500">*</span>
            </label>
            <Combobox
              value={formData.manufacturer}
              onChange={value => {
                setFormData({ ...formData, manufacturer: value, model: '' });
                setErrors({ ...errors, manufacturer: '' });
              }}
              options={availableBrands}
              placeholder="Type to search or enter new brand (e.g., Cisco, Dell, HPE)"
              error={errors.manufacturer}
              allowCustom={true}
              disabled={mode === 'edit'}
            />
            {availableBrands.length > 0 && (
              <p className="text-xs text-muted-foreground mt-1">
                {availableBrands.length} {formData.device_type} brand(s) in database
              </p>
            )}
          </div>

          {/* Model */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Model <span className="text-red-500">*</span>
            </label>
            <Combobox
              value={formData.model}
              onChange={value => {
                setFormData({ ...formData, model: value });
                setErrors({ ...errors, model: '' });
              }}
              options={availableModels}
              placeholder="Type model name (e.g., Catalyst 2960, PowerEdge R740)"
              error={errors.model}
              allowCustom={true}
              disabled={mode === 'edit' || !formData.manufacturer}
            />
            {availableModels.length > 0 && (
              <p className="text-xs text-muted-foreground mt-1">
                {availableModels.length} {formData.manufacturer} model(s) available
              </p>
            )}

            {/* Fetch from Web Button */}
            {formData.manufacturer && formData.model && !matchingSpec && (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleFetchFromWeb}
                disabled={isFetchingFromWeb}
                className="mt-2 w-full gap-2"
              >
                {isFetchingFromWeb ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-electric" />
                    Fetching specifications...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Fetch Specs from Web
                  </>
                )}
              </Button>
            )}
          </div>

          {/* Spec Detection Status */}
          {mode === 'create' && formData.manufacturer && formData.model && (
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
                        Using existing specifications for {matchingSpec.brand}{' '}
                        {matchingSpec.model}
                      </p>
                      <div className="grid grid-cols-3 gap-2">
                        <div className="p-2 bg-background/50 rounded">
                          <span className="text-xs text-muted-foreground block">Height</span>
                          <span className="text-sm text-electric font-mono font-bold">
                            {matchingSpec.height_u}U
                          </span>
                        </div>
                        <div className="p-2 bg-background/50 rounded">
                          <span className="text-xs text-muted-foreground block">Power</span>
                          <span className="text-sm text-electric font-mono font-bold">
                            {matchingSpec.power_watts}W
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
              ) : willCreateNewSpec ? (
                <motion.div
                  key="will-create-new"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg"
                >
                  <div className="flex items-start gap-3">
                    <Sparkles className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-yellow-500 mb-1">
                        New Device Specification
                      </p>
                      <p className="text-xs text-muted-foreground">
                        This brand/model combination is not in the database. Please enter the
                        specifications below and we'll save them for future use.
                      </p>
                    </div>
                  </div>
                </motion.div>
              ) : null}
            </AnimatePresence>
          )}
        </div>

        {/* Step 4: Physical Specifications */}
        {formData.manufacturer && formData.model && (
          <Collapsible
            title="Step 3: Physical Specifications"
            defaultOpen={true}
          >
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Height (U) <span className="text-red-500">*</span>
                </label>
                <Input
                  type="number"
                  min="1"
                  max="48"
                  value={formData.height_units}
                  onChange={e => {
                    setFormData({ ...formData, height_units: parseInt(e.target.value) || 1 });
                    setErrors({ ...errors, height_units: '' });
                  }}
                  error={errors.height_units}
                  disabled={!!matchingSpec}
                />
                {matchingSpec && (
                  <p className="text-xs text-electric mt-1 flex items-center gap-1">
                    <Database className="w-3 h-3" />
                    from database
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Power (W) <span className="text-red-500">*</span>
                </label>
                <Input
                  type="number"
                  min="0"
                  value={formData.power_consumption_watts}
                  onChange={e => {
                    setFormData({
                      ...formData,
                      power_consumption_watts: parseInt(e.target.value) || 0,
                    });
                    setErrors({ ...errors, power_consumption_watts: '' });
                  }}
                  error={errors.power_consumption_watts}
                  disabled={!!matchingSpec}
                />
                {matchingSpec && (
                  <p className="text-xs text-electric mt-1 flex items-center gap-1">
                    <Database className="w-3 h-3" />
                    from database
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Weight (kg) <span className="text-red-500">*</span>
                </label>
                <Input
                  type="number"
                  min="0"
                  step="0.1"
                  value={formData.weight_kg}
                  onChange={e => {
                    setFormData({ ...formData, weight_kg: parseFloat(e.target.value) || 0 });
                    setErrors({ ...errors, weight_kg: '' });
                  }}
                  error={errors.weight_kg}
                  disabled={!!matchingSpec}
                />
                {matchingSpec && (
                  <p className="text-xs text-electric mt-1 flex items-center gap-1">
                    <Database className="w-3 h-3" />
                    from database
                  </p>
                )}
              </div>
            </div>

            {willCreateNewSpec && (
              <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg flex items-start gap-2">
                <Info className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-muted-foreground">
                  These specifications will be saved to the database and can be reused when adding
                  more devices of the same model.
                </p>
              </div>
            )}
          </Collapsible>
        )}

        {/* Step 5: Additional Information */}
        {formData.manufacturer && formData.model && (
          <Collapsible title="Step 4: Additional Information (Optional)">
            <Input
              label="Custom Name"
              value={formData.custom_name}
              onChange={e => setFormData({ ...formData, custom_name: e.target.value })}
              placeholder={`Defaults to "${formData.manufacturer} ${formData.model}"`}
            />

            <TextArea
              label="Notes"
              value={formData.notes}
              onChange={e => setFormData({ ...formData, notes: e.target.value })}
              placeholder="Additional notes about this device..."
              rows={3}
            />
          </Collapsible>
        )}

        {/* Validation Summary */}
        {Object.keys(errors).length > 0 && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-red-500 mb-1">Please fix the following errors:</p>
                <ul className="text-xs text-muted-foreground list-disc list-inside">
                  {Object.values(errors).map((error, idx) => (
                    <li key={idx}>{error}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
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
