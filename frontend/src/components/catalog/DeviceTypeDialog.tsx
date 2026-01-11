import React, { useState, useEffect } from 'react';
import { Dialog, DialogFooter } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import type { DeviceTypeResponse, DeviceTypeCreate, DeviceTypeUpdate } from '../../types/catalog';

interface DeviceTypeDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: DeviceTypeCreate | DeviceTypeUpdate) => Promise<void>;
  deviceType?: DeviceTypeResponse | null;
  mode: 'create' | 'edit';
}

interface FormErrors {
  name?: string;
  slug?: string;
  icon?: string;
  description?: string;
  color?: string;
}

// Common device type emojis
const EMOJI_SUGGESTIONS = [
  '🖥️', '🔀', '📡', '🛡️', '💾', '⚡', '🔋', '🔌', '📦',
  '🌐', '💻', '🖨️', '📱', '⌨️', '🖱️', '📸', '🎥', '🔊',
  '🎛️', '🔧', '⚙️', '🔩', '📊', '📈', '💡', '🚀', '🔬'
];

// Common color presets
const COLOR_PRESETS = [
  { name: 'Blue', value: '#3b82f6' },
  { name: 'Green', value: '#10b981' },
  { name: 'Purple', value: '#8b5cf6' },
  { name: 'Red', value: '#ef4444' },
  { name: 'Orange', value: '#f97316' },
  { name: 'Yellow', value: '#eab308' },
  { name: 'Cyan', value: '#06b6d4' },
  { name: 'Pink', value: '#ec4899' },
  { name: 'Gray', value: '#6b7280' },
];

export const DeviceTypeDialog: React.FC<DeviceTypeDialogProps> = ({
  isOpen,
  onClose,
  onSave,
  deviceType,
  mode,
}) => {
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    icon: '📦',
    description: '',
    color: '#6b7280',
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (deviceType && mode === 'edit') {
      setFormData({
        name: deviceType.name,
        slug: deviceType.slug,
        icon: deviceType.icon || '📦',
        description: deviceType.description || '',
        color: deviceType.color || '#6b7280',
      });
    } else {
      setFormData({
        name: '',
        slug: '',
        icon: '📦',
        description: '',
        color: '#6b7280',
      });
    }
    setErrors({});
  }, [deviceType, mode, isOpen]);

  const generateSlug = (name: string): string => {
    return name
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
  };

  const handleNameChange = (name: string) => {
    setFormData((prev) => ({
      ...prev,
      name,
      // Auto-generate slug only in create mode and if slug hasn't been manually edited
      slug: mode === 'create' && !prev.slug ? generateSlug(name) : prev.slug,
    }));
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Required fields
    if (!formData.name.trim()) {
      newErrors.name = 'Device type name is required';
    }

    if (!formData.slug.trim()) {
      newErrors.slug = 'Slug is required';
    } else if (!/^[a-z0-9-]+$/.test(formData.slug)) {
      newErrors.slug = 'Slug must contain only lowercase letters, numbers, and hyphens';
    }

    // Optional validations
    if (formData.icon && formData.icon.length > 10) {
      newErrors.icon = 'Icon must be 10 characters or less (typically 1-2 emoji characters)';
    }

    if (formData.description && formData.description.length > 500) {
      newErrors.description = 'Description must be 500 characters or less';
    }

    if (formData.color && !/^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/.test(formData.color)) {
      newErrors.color = 'Color must be a valid hex color (e.g., #3b82f6)';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    try {
      await onSave({
        name: formData.name,
        slug: formData.slug,
        icon: formData.icon || null,
        description: formData.description || null,
        color: formData.color || null,
      });
      onClose();
    } catch (error) {
      console.error('Error saving device type:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={mode === 'create' ? 'Add New Device Type' : 'Edit Device Type'}
      description={
        mode === 'create'
          ? 'Create a new device type category for organizing your equipment models'
          : 'Update the device type information'
      }
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-border/50">
            <div className="w-1 h-5 bg-electric rounded-full" />
            <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">
              Basic Information
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Device Type Name"
              id="name"
              value={formData.name}
              onChange={(e) => handleNameChange(e.target.value)}
              placeholder="e.g., Server, Switch, Router"
              error={errors.name}
              required
            />
            <div>
              <Input
                label="Slug"
                id="slug"
                value={formData.slug}
                onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                placeholder="e.g., server, network-switch"
                error={errors.slug}
                required
              />
              {!errors.slug && (
                <p className="mt-1 text-xs text-muted-foreground">
                  Unique identifier (lowercase, hyphens allowed)
                </p>
              )}
            </div>
          </div>

          <Input
            label="Description (Optional)"
            id="description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Brief description of this device type"
            error={errors.description}
          />
        </div>

        {/* Appearance */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-border/50">
            <div className="w-1 h-5 bg-electric rounded-full" />
            <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">
              Visual Appearance
            </h3>
          </div>

          {/* Icon Selection */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-foreground">
              Icon (Emoji)
            </label>
            <div className="flex gap-2">
              <Input
                id="icon"
                value={formData.icon}
                onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
                placeholder="📦"
                error={errors.icon}
                className="flex-1"
              />
              <div
                className="flex items-center justify-center w-12 h-12 rounded-lg border-2 glass"
                style={{
                  borderColor: formData.color + '40',
                  backgroundColor: formData.color + '10',
                }}
              >
                <span className="text-2xl">{formData.icon}</span>
              </div>
            </div>

            {/* Emoji Suggestions */}
            <div className="flex flex-wrap gap-2 p-3 bg-secondary/30 rounded-lg">
              {EMOJI_SUGGESTIONS.map((emoji) => (
                <button
                  key={emoji}
                  type="button"
                  onClick={() => setFormData({ ...formData, icon: emoji })}
                  className={`w-10 h-10 rounded-lg flex items-center justify-center text-xl transition-all
                    ${formData.icon === emoji
                      ? 'bg-electric/20 border-2 border-electric scale-110'
                      : 'bg-secondary hover:bg-secondary/80 border border-border hover:scale-105'
                    }`}
                >
                  {emoji}
                </button>
              ))}
            </div>
          </div>

          {/* Color Selection */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-foreground">
              Color
            </label>
            <div className="flex gap-2">
              <Input
                id="color"
                value={formData.color}
                onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                placeholder="#6b7280"
                error={errors.color}
                className="flex-1 font-mono"
              />
              <input
                type="color"
                value={formData.color}
                onChange={(e) => setFormData({ ...formData, color: e.target.value })}
                className="w-12 h-12 rounded-lg border border-border cursor-pointer"
              />
            </div>

            {/* Color Presets */}
            <div className="flex flex-wrap gap-2 p-3 bg-secondary/30 rounded-lg">
              {COLOR_PRESETS.map((preset) => (
                <button
                  key={preset.value}
                  type="button"
                  onClick={() => setFormData({ ...formData, color: preset.value })}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg border-2 transition-all
                    ${formData.color === preset.value
                      ? 'border-electric scale-105'
                      : 'border-transparent hover:border-border hover:scale-105'
                    }`}
                  style={{ backgroundColor: preset.value + '20' }}
                >
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: preset.value }}
                  />
                  <span className="text-xs font-medium" style={{ color: preset.value }}>
                    {preset.name}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Preview */}
          <div className="p-4 bg-secondary/30 rounded-lg border border-border">
            <p className="text-xs text-muted-foreground mb-2 uppercase tracking-wide">Preview</p>
            <div className="flex items-center gap-3">
              <div
                className="p-3 rounded-xl glass border-2"
                style={{
                  borderColor: formData.color + '40',
                  backgroundColor: formData.color + '10',
                }}
              >
                <span className="text-3xl">{formData.icon}</span>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-foreground">
                  {formData.name || 'Device Type Name'}
                </h3>
                <div
                  className="px-2.5 py-1 rounded-full text-xs font-medium border-2 inline-flex items-center gap-1.5 mt-1"
                  style={{
                    color: formData.color,
                    borderColor: formData.color + '40',
                    backgroundColor: formData.color + '10',
                  }}
                >
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: formData.color }}
                  />
                  <span className="font-mono">{formData.slug || 'slug'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="ghost" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" loading={loading}>
            {mode === 'create' ? 'Create Device Type' : 'Save Changes'}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
};
