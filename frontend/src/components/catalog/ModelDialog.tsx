import React, { useState, useEffect } from 'react';
import { Dialog, DialogFooter } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { useCatalogStore } from '../../store/useCatalogStore';
import type { ModelCreate, ModelUpdate, ModelResponse } from '../../types/catalog';
import { Plus, Trash2 } from 'lucide-react';

interface ModelDialogProps {
  isOpen: boolean;
  onClose: () => void;
  model?: ModelResponse | null;
  onSuccess?: () => void;
}

export const ModelDialog: React.FC<ModelDialogProps> = ({
  isOpen,
  onClose,
  model,
  onSuccess,
}) => {
  const {
    brands,
    deviceTypes,
    fetchBrands,
    fetchDeviceTypes,
    createModel,
    updateModel,
    modelsLoading,
    brandsLoading,
    deviceTypesLoading,
  } = useCatalogStore();

  // Form state
  const [formData, setFormData] = useState<Partial<ModelCreate>>({
    brand_id: 0,
    device_type_id: 0,
    name: '',
    variant: '',
    description: '',
    height_u: 1,
    width_type: 'standard',
    depth_mm: null,
    weight_kg: null,
    power_watts: null,
    heat_output_btu: null,
    airflow_pattern: '',
    max_operating_temp_c: null,
    mounting_type: '',
    datasheet_url: '',
    image_url: '',
    release_date: '',
    end_of_life: '',
    typical_ports: {},
  });

  const [portEntries, setPortEntries] = useState<Array<{ key: string; value: string }>>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Load brands and device types on mount
  useEffect(() => {
    if (isOpen) {
      fetchBrands({ page_size: 1000 });
      fetchDeviceTypes({ page_size: 1000 });
    }
  }, [isOpen, fetchBrands, fetchDeviceTypes]);

  // Populate form when editing
  useEffect(() => {
    if (model) {
      setFormData({
        brand_id: model.brand_id,
        device_type_id: model.device_type_id,
        name: model.name,
        variant: model.variant || '',
        description: model.description || '',
        height_u: model.height_u,
        width_type: model.width_type || 'standard',
        depth_mm: model.depth_mm,
        weight_kg: model.weight_kg,
        power_watts: model.power_watts,
        heat_output_btu: model.heat_output_btu,
        airflow_pattern: model.airflow_pattern || '',
        max_operating_temp_c: model.max_operating_temp_c,
        mounting_type: model.mounting_type || '',
        datasheet_url: model.datasheet_url || '',
        image_url: model.image_url || '',
        release_date: model.release_date || '',
        end_of_life: model.end_of_life || '',
        typical_ports: model.typical_ports || {},
      });

      // Convert typical_ports to array for editing
      if (model.typical_ports) {
        setPortEntries(
          Object.entries(model.typical_ports).map(([key, value]) => ({
            key,
            value: String(value),
          }))
        );
      }
    } else {
      // Reset form for new model
      setFormData({
        brand_id: 0,
        device_type_id: 0,
        name: '',
        variant: '',
        description: '',
        height_u: 1,
        width_type: 'standard',
        depth_mm: null,
        weight_kg: null,
        power_watts: null,
        heat_output_btu: null,
        airflow_pattern: '',
        max_operating_temp_c: null,
        mounting_type: '',
        datasheet_url: '',
        image_url: '',
        release_date: '',
        end_of_life: '',
        typical_ports: {},
      });
      setPortEntries([]);
    }
    setErrors({});
  }, [model, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    const newErrors: Record<string, string> = {};
    if (!formData.brand_id || formData.brand_id <= 0) {
      newErrors.brand_id = 'Please select a brand';
    }
    if (!formData.device_type_id || formData.device_type_id <= 0) {
      newErrors.device_type_id = 'Please select a device type';
    }
    if (!formData.name?.trim()) {
      newErrors.name = 'Model name is required';
    }
    if (!formData.height_u || formData.height_u <= 0) {
      newErrors.height_u = 'Height must be greater than 0';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      // Convert port entries to object
      const typical_ports: Record<string, number> = {};
      portEntries.forEach(({ key, value }) => {
        if (key.trim() && value.trim()) {
          typical_ports[key.trim()] = parseInt(value, 10) || 0;
        }
      });

      const submitData: ModelCreate | ModelUpdate = {
        ...formData,
        brand_id: formData.brand_id!,
        device_type_id: formData.device_type_id!,
        name: formData.name!,
        height_u: formData.height_u!,
        typical_ports: Object.keys(typical_ports).length > 0 ? typical_ports : null,
        // Convert empty strings to null
        variant: formData.variant || null,
        description: formData.description || null,
        width_type: formData.width_type || null,
        airflow_pattern: formData.airflow_pattern || null,
        mounting_type: formData.mounting_type || null,
        datasheet_url: formData.datasheet_url || null,
        image_url: formData.image_url || null,
        release_date: formData.release_date || null,
        end_of_life: formData.end_of_life || null,
      };

      if (model) {
        await updateModel(model.id, submitData as ModelUpdate);
      } else {
        await createModel(submitData as ModelCreate);
      }

      onSuccess?.();
      onClose();
    } catch (error) {
      console.error('Error saving model:', error);
    }
  };

  const addPortEntry = () => {
    setPortEntries([...portEntries, { key: '', value: '' }]);
  };

  const removePortEntry = (index: number) => {
    setPortEntries(portEntries.filter((_, i) => i !== index));
  };

  const updatePortEntry = (index: number, field: 'key' | 'value', value: string) => {
    const newEntries = [...portEntries];
    newEntries[index][field] = value;
    setPortEntries(newEntries);
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={model ? 'Edit Model' : 'Add New Model'}
      description={model ? 'Update model specifications' : 'Add a new device model to the catalog'}
      size="xl"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2">
            Basic Information
          </h3>

          <div className="grid grid-cols-2 gap-4">
            {/* Brand Selector */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Brand <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.brand_id || 0}
                onChange={(e) =>
                  setFormData({ ...formData, brand_id: parseInt(e.target.value, 10) })
                }
                disabled={brandsLoading}
                className="w-full px-3 py-2 bg-card border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-electric disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {brandsLoading && brands.length === 0 ? (
                  <option value={0}>Loading brands...</option>
                ) : (
                  <>
                    <option value={0}>Select a brand...</option>
                    {brands.map((brand) => (
                      <option key={brand.id} value={brand.id}>
                        {brand.name}
                      </option>
                    ))}
                  </>
                )}
              </select>
              {errors.brand_id && (
                <p className="text-xs text-red-500 mt-1">{errors.brand_id}</p>
              )}
            </div>

            {/* Device Type Selector */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Device Type <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.device_type_id || 0}
                onChange={(e) =>
                  setFormData({ ...formData, device_type_id: parseInt(e.target.value, 10) })
                }
                disabled={deviceTypesLoading}
                className="w-full px-3 py-2 bg-card border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-electric disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {deviceTypesLoading && deviceTypes.length === 0 ? (
                  <option value={0}>Loading device types...</option>
                ) : (
                  <>
                    <option value={0}>Select a device type...</option>
                    {deviceTypes.map((type) => (
                      <option key={type.id} value={type.id}>
                        {type.icon} {type.name}
                      </option>
                    ))}
                  </>
                )}
              </select>
              {errors.device_type_id && (
                <p className="text-xs text-red-500 mt-1">{errors.device_type_id}</p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Model Name <span className="text-red-500">*</span>
              </label>
              <Input
                value={formData.name || ''}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., PowerEdge R740"
              />
              {errors.name && <p className="text-xs text-red-500 mt-1">{errors.name}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Variant
              </label>
              <Input
                value={formData.variant || ''}
                onChange={(e) => setFormData({ ...formData, variant: e.target.value })}
                placeholder="e.g., xd, LFF"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">
              Description
            </label>
            <textarea
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Brief description of the model..."
              rows={3}
              className="w-full px-3 py-2 bg-card border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-electric resize-none"
            />
          </div>
        </div>

        {/* Physical Specifications */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2">
            Physical Specifications
          </h3>

          <div className="grid grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Height (U) <span className="text-red-500">*</span>
              </label>
              <Input
                type="number"
                min="1"
                step="1"
                value={formData.height_u || ''}
                onChange={(e) =>
                  setFormData({ ...formData, height_u: parseInt(e.target.value, 10) || 1 })
                }
              />
              {errors.height_u && <p className="text-xs text-red-500 mt-1">{errors.height_u}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Width Type
              </label>
              <select
                value={formData.width_type || 'standard'}
                onChange={(e) => setFormData({ ...formData, width_type: e.target.value })}
                className="w-full px-3 py-2 bg-card border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-electric"
              >
                <option value="standard">Standard (19")</option>
                <option value="half">Half Width</option>
                <option value="full">Full Width</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Depth (mm)
              </label>
              <Input
                type="number"
                min="0"
                step="1"
                value={formData.depth_mm || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    depth_mm: e.target.value ? parseFloat(e.target.value) : null,
                  })
                }
                placeholder="e.g., 730"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Weight (kg)
              </label>
              <Input
                type="number"
                min="0"
                step="0.1"
                value={formData.weight_kg || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    weight_kg: e.target.value ? parseFloat(e.target.value) : null,
                  })
                }
                placeholder="e.g., 15.5"
              />
            </div>
          </div>
        </div>

        {/* Power & Thermal */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2">
            Power & Thermal
          </h3>

          <div className="grid grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Power (W)
              </label>
              <Input
                type="number"
                min="0"
                step="1"
                value={formData.power_watts || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    power_watts: e.target.value ? parseInt(e.target.value, 10) : null,
                  })
                }
                placeholder="e.g., 750"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Heat Output (BTU)
              </label>
              <Input
                type="number"
                min="0"
                step="1"
                value={formData.heat_output_btu || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    heat_output_btu: e.target.value ? parseInt(e.target.value, 10) : null,
                  })
                }
                placeholder="e.g., 2560"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Airflow Pattern
              </label>
              <select
                value={formData.airflow_pattern || ''}
                onChange={(e) => setFormData({ ...formData, airflow_pattern: e.target.value })}
                className="w-full px-3 py-2 bg-card border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-electric"
              >
                <option value="">Select...</option>
                <option value="front-to-back">Front to Back</option>
                <option value="back-to-front">Back to Front</option>
                <option value="side-to-side">Side to Side</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Max Temp (°C)
              </label>
              <Input
                type="number"
                min="0"
                step="1"
                value={formData.max_operating_temp_c || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    max_operating_temp_c: e.target.value ? parseInt(e.target.value, 10) : null,
                  })
                }
                placeholder="e.g., 35"
              />
            </div>
          </div>
        </div>

        {/* Connectivity */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2">
            Connectivity
          </h3>

          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-foreground">
                Typical Ports
              </label>
              <Button type="button" variant="outline" size="sm" onClick={addPortEntry} leftIcon={<Plus className="w-4 h-4" />}>
                Add Port
              </Button>
            </div>

            {portEntries.length > 0 ? (
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {portEntries.map((entry, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <Input
                      placeholder="Port type (e.g., RJ45)"
                      value={entry.key}
                      onChange={(e) => updatePortEntry(index, 'key', e.target.value)}
                      className="flex-1"
                    />
                    <Input
                      type="number"
                      min="0"
                      placeholder="Count"
                      value={entry.value}
                      onChange={(e) => updatePortEntry(index, 'value', e.target.value)}
                      className="w-24"
                    />
                    <Button
                      type="button"
                      variant="danger"
                      size="sm"
                      onClick={() => removePortEntry(index)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground italic">No ports defined</p>
            )}
          </div>
        </div>

        {/* Mounting & Documentation */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2">
            Mounting & Documentation
          </h3>

          <div>
            <label className="block text-sm font-medium text-foreground mb-1.5">
              Mounting Type
            </label>
            <select
              value={formData.mounting_type || ''}
              onChange={(e) => setFormData({ ...formData, mounting_type: e.target.value })}
              className="w-full px-3 py-2 bg-card border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-electric"
            >
              <option value="">Select...</option>
              <option value="rack-mount">Rack Mount</option>
              <option value="blade">Blade</option>
              <option value="wall-mount">Wall Mount</option>
              <option value="floor-standing">Floor Standing</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Datasheet URL
              </label>
              <Input
                type="url"
                value={formData.datasheet_url || ''}
                onChange={(e) => setFormData({ ...formData, datasheet_url: e.target.value })}
                placeholder="https://..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Image URL
              </label>
              <Input
                type="url"
                value={formData.image_url || ''}
                onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                placeholder="https://..."
              />
            </div>
          </div>
        </div>

        {/* Lifecycle */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2">
            Lifecycle
          </h3>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                Release Date
              </label>
              <Input
                type="date"
                value={formData.release_date || ''}
                onChange={(e) => setFormData({ ...formData, release_date: e.target.value })}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-1.5">
                End of Life
              </label>
              <Input
                type="date"
                value={formData.end_of_life || ''}
                onChange={(e) => setFormData({ ...formData, end_of_life: e.target.value })}
              />
            </div>
          </div>
        </div>

        {/* Footer Buttons */}
        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose} disabled={modelsLoading}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" loading={modelsLoading}>
            {model ? 'Update Model' : 'Create Model'}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
};
