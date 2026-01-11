import React, { useState, useEffect } from 'react';
import { Dialog, DialogFooter } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input, Select } from '../ui/input';
import { Collapsible } from '../ui/collapsible';
import type { Rack } from '../../types';

interface RackDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: any) => void;
  rack?: Rack | null;
  mode: 'create' | 'edit';
}

interface FormErrors {
  name?: string;
  location?: string;
  units?: string;
  depth_mm?: string;
  max_power_watts?: string;
  max_weight_kg?: string;
  cooling_capacity_btu?: string;
  ambient_temp_c?: string;
  max_inlet_temp_c?: string;
  airflow_cfm?: string;
}

export const RackDialog: React.FC<RackDialogProps> = ({
  isOpen,
  onClose,
  onSave,
  rack,
  mode,
}) => {
  const [formData, setFormData] = useState({
    // Basic Information
    name: '',
    location: '',
    // Physical Dimensions
    units: 42,
    width_inches: 19,
    depth_mm: 700,
    // Capacity Limits
    max_power_watts: 5000,
    max_weight_kg: 500,
    // Cooling & Thermal (optional)
    cooling_type: '',
    cooling_capacity_btu: undefined as number | undefined,
    ambient_temp_c: 22,
    max_inlet_temp_c: 27,
    airflow_cfm: undefined as number | undefined,
  });

  const [errors, setErrors] = useState<FormErrors>({});

  useEffect(() => {
    if (rack && mode === 'edit') {
      setFormData({
        name: rack.name,
        location: rack.location,
        units: rack.units,
        width_inches: rack.width_inches || 19,
        depth_mm: rack.depth_mm || 700,
        max_power_watts: rack.max_power_watts,
        max_weight_kg: rack.max_weight_kg,
        cooling_type: rack.cooling_type || '',
        cooling_capacity_btu: rack.cooling_capacity_btu,
        ambient_temp_c: rack.ambient_temp_c || 22,
        max_inlet_temp_c: rack.max_inlet_temp_c || 27,
        airflow_cfm: rack.airflow_cfm,
      });
    } else {
      setFormData({
        name: '',
        location: '',
        units: 42,
        width_inches: 19,
        depth_mm: 700,
        max_power_watts: 5000,
        max_weight_kg: 500,
        cooling_type: '',
        cooling_capacity_btu: undefined,
        ambient_temp_c: 22,
        max_inlet_temp_c: 27,
        airflow_cfm: undefined,
      });
    }
    setErrors({});
  }, [rack, mode, isOpen]);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Required fields
    if (!formData.name.trim()) {
      newErrors.name = 'Rack name is required';
    }
    if (!formData.location.trim()) {
      newErrors.location = 'Location is required';
    }

    // Numeric validations
    if (formData.units < 1 || formData.units > 100) {
      newErrors.units = 'Height must be between 1 and 100 U';
    }
    if (formData.depth_mm < 200 || formData.depth_mm > 1500) {
      newErrors.depth_mm = 'Depth must be between 200 and 1500 mm';
    }
    if (formData.max_power_watts < 0 || formData.max_power_watts > 50000) {
      newErrors.max_power_watts = 'Power must be between 0 and 50000 W';
    }
    if (formData.max_weight_kg < 0 || formData.max_weight_kg > 2000) {
      newErrors.max_weight_kg = 'Weight must be between 0 and 2000 kg';
    }

    // Optional cooling validations
    if (formData.cooling_capacity_btu !== undefined && (formData.cooling_capacity_btu < 0 || formData.cooling_capacity_btu > 100000)) {
      newErrors.cooling_capacity_btu = 'Cooling capacity must be between 0 and 100000 BTU';
    }
    if (formData.ambient_temp_c < 10 || formData.ambient_temp_c > 35) {
      newErrors.ambient_temp_c = 'Ambient temp must be between 10 and 35°C';
    }
    if (formData.max_inlet_temp_c < 15 || formData.max_inlet_temp_c > 40) {
      newErrors.max_inlet_temp_c = 'Max inlet temp must be between 15 and 40°C';
    }
    if (formData.airflow_cfm !== undefined && formData.airflow_cfm < 0) {
      newErrors.airflow_cfm = 'Airflow must be 0 or greater';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    // Clean up undefined values before submitting
    const cleanedData = Object.entries(formData).reduce((acc, [key, value]) => {
      if (value !== undefined && value !== '') {
        acc[key] = value;
      }
      return acc;
    }, {} as any);

    onSave(cleanedData);
    onClose();
  };

  const widthOptions = [
    { value: 11, label: '11"' },
    { value: 18, label: '18"' },
    { value: 19, label: '19"' },
    { value: 23, label: '23"' },
  ];

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={mode === 'create' ? 'Add New Rack' : 'Edit Rack'}
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Section 1: Basic Information */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-border/50">
            <div className="w-1 h-5 bg-electric rounded-full" />
            <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">
              Basic Information
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Rack Name"
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Main Server Rack"
              error={errors.name}
              required
            />
            <Input
              label="Location"
              id="location"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              placeholder="e.g., Datacenter Room A1"
              error={errors.location}
              required
            />
          </div>
        </div>

        {/* Section 2: Physical Dimensions */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-border/50">
            <div className="w-1 h-5 bg-electric rounded-full" />
            <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">
              Physical Dimensions
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              label="Height (U)"
              id="units"
              type="number"
              min="1"
              max="100"
              value={formData.units}
              onChange={(e) => setFormData({ ...formData, units: parseInt(e.target.value) || 1 })}
              placeholder="42"
              error={errors.units}
            />
            <Select
              label="Width"
              id="width_inches"
              value={formData.width_inches}
              onChange={(e) => setFormData({ ...formData, width_inches: parseInt(e.target.value) })}
              options={widthOptions}
            />
            <Input
              label="Depth (mm)"
              id="depth_mm"
              type="number"
              min="200"
              max="1500"
              step="10"
              value={formData.depth_mm}
              onChange={(e) => setFormData({ ...formData, depth_mm: parseFloat(e.target.value) || 700 })}
              placeholder="700"
              error={errors.depth_mm}
            />
          </div>
        </div>

        {/* Section 3: Capacity Limits */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-border/50">
            <div className="w-1 h-5 bg-electric rounded-full" />
            <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">
              Capacity Limits
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Max Weight (kg)"
              id="max_weight_kg"
              type="number"
              min="0"
              max="2000"
              step="10"
              value={formData.max_weight_kg}
              onChange={(e) => setFormData({ ...formData, max_weight_kg: parseFloat(e.target.value) || 0 })}
              placeholder="500"
              error={errors.max_weight_kg}
            />
            <Input
              label="Max Power (W)"
              id="max_power_watts"
              type="number"
              min="0"
              max="50000"
              step="100"
              value={formData.max_power_watts}
              onChange={(e) => setFormData({ ...formData, max_power_watts: parseFloat(e.target.value) || 0 })}
              placeholder="5000"
              error={errors.max_power_watts}
            />
          </div>
        </div>

        {/* Section 4: Cooling & Thermal (Collapsible) */}
        <Collapsible
          title="Cooling & Thermal (Optional)"
          defaultOpen={false}
          className="border-border/50"
        >
          <div className="space-y-4">
            <Input
              label="Cooling Type"
              id="cooling_type"
              value={formData.cooling_type}
              onChange={(e) => setFormData({ ...formData, cooling_type: e.target.value })}
              placeholder="e.g., In-row cooling, CRAC"
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Cooling Capacity (BTU)"
                id="cooling_capacity_btu"
                type="number"
                min="0"
                max="100000"
                step="100"
                value={formData.cooling_capacity_btu || ''}
                onChange={(e) => setFormData({
                  ...formData,
                  cooling_capacity_btu: e.target.value ? parseFloat(e.target.value) : undefined
                })}
                placeholder="12000"
                error={errors.cooling_capacity_btu}
              />
              <Input
                label="Airflow (CFM)"
                id="airflow_cfm"
                type="number"
                min="0"
                step="10"
                value={formData.airflow_cfm || ''}
                onChange={(e) => setFormData({
                  ...formData,
                  airflow_cfm: e.target.value ? parseFloat(e.target.value) : undefined
                })}
                placeholder="200"
                error={errors.airflow_cfm}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Ambient Temp (°C)"
                id="ambient_temp_c"
                type="number"
                min="10"
                max="35"
                step="0.5"
                value={formData.ambient_temp_c}
                onChange={(e) => setFormData({ ...formData, ambient_temp_c: parseFloat(e.target.value) || 22 })}
                placeholder="22"
                error={errors.ambient_temp_c}
              />
              <Input
                label="Max Inlet Temp (°C)"
                id="max_inlet_temp_c"
                type="number"
                min="15"
                max="40"
                step="0.5"
                value={formData.max_inlet_temp_c}
                onChange={(e) => setFormData({ ...formData, max_inlet_temp_c: parseFloat(e.target.value) || 27 })}
                placeholder="27"
                error={errors.max_inlet_temp_c}
              />
            </div>
          </div>
        </Collapsible>

        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" variant="primary">
            {mode === 'create' ? 'Create Rack' : 'Save Changes'}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
};
