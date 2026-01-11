import React, { useState, useEffect, useRef } from 'react';
import { Dialog, DialogFooter } from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { AlertCircle, Upload, X, Image as ImageIcon } from 'lucide-react';
import type { BrandResponse, BrandCreate, BrandUpdate } from '../../types/catalog';
import { useCatalogStore } from '../../store/useCatalogStore';
import { getCatalogErrorMessage } from '../../lib/api-catalog';

interface BrandDialogProps {
  isOpen: boolean;
  onClose: () => void;
  brand?: BrandResponse | null;
  onSuccess?: () => void;
}

interface FormData {
  name: string;
  slug: string;
  website: string;
  support_url: string;
  logo_url: string;
  description: string;
  founded_year: string;
  headquarters: string;
}

interface FormErrors {
  name?: string;
  slug?: string;
  website?: string;
  support_url?: string;
  logo_url?: string;
  founded_year?: string;
  general?: string;
}

export const BrandDialog: React.FC<BrandDialogProps> = ({
  isOpen,
  onClose,
  brand,
  onSuccess,
}) => {
  const { createBrand, updateBrand, uploadBrandLogo, deleteBrandLogo, brandsLoading } = useCatalogStore();
  const isEditMode = !!brand;
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [formData, setFormData] = useState<FormData>({
    name: '',
    slug: '',
    website: '',
    support_url: '',
    logo_url: '',
    description: '',
    founded_year: '',
    headquarters: '',
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filePreview, setFilePreview] = useState<string | null>(null);
  const [uploadingLogo, setUploadingLogo] = useState(false);

  // Initialize form data when brand changes
  useEffect(() => {
    if (brand) {
      setFormData({
        name: brand.name,
        slug: brand.slug,
        website: brand.website || '',
        support_url: brand.support_url || '',
        logo_url: brand.logo_url || '',
        description: brand.description || '',
        founded_year: brand.founded_year?.toString() || '',
        headquarters: brand.headquarters || '',
      });
    } else {
      setFormData({
        name: '',
        slug: '',
        website: '',
        support_url: '',
        logo_url: '',
        description: '',
        founded_year: '',
        headquarters: '',
      });
    }
    setErrors({});
    setSelectedFile(null);
    setFilePreview(null);
  }, [brand, isOpen]);

  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setErrors({ ...errors, logo_url: 'Invalid file type. Allowed: PNG, JPG, SVG, WebP' });
      return;
    }

    // Validate file size (5MB max)
    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
      setErrors({ ...errors, logo_url: 'File size must be less than 5MB' });
      return;
    }

    setSelectedFile(file);
    setErrors({ ...errors, logo_url: undefined });

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setFilePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  // Handle file upload
  const handleUploadLogo = async () => {
    if (!selectedFile || !brand?.id) return;

    setUploadingLogo(true);
    try {
      const updatedBrand = await uploadBrandLogo(brand.id, selectedFile);
      setFormData((prev) => ({ ...prev, logo_url: updatedBrand.logo_url || '' }));
      setSelectedFile(null);
      setFilePreview(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      setErrors({ ...errors, logo_url: getCatalogErrorMessage(error) });
    } finally {
      setUploadingLogo(false);
    }
  };

  // Handle remove logo
  const handleRemoveLogo = async () => {
    if (!brand?.id) return;

    setUploadingLogo(true);
    try {
      await deleteBrandLogo(brand.id);
      setFormData((prev) => ({ ...prev, logo_url: '' }));
    } catch (error) {
      setErrors({ ...errors, logo_url: getCatalogErrorMessage(error) });
    } finally {
      setUploadingLogo(false);
    }
  };

  // Clear file selection
  const handleClearFile = () => {
    setSelectedFile(null);
    setFilePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Auto-generate slug from name
  const handleNameChange = (value: string) => {
    setFormData((prev) => ({
      ...prev,
      name: value,
      slug: isEditMode ? prev.slug : value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''),
    }));
    if (errors.name) {
      setErrors((prev) => ({ ...prev, name: undefined }));
    }
  };

  const handleChange = (field: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Required fields
    if (!formData.name.trim()) {
      newErrors.name = 'Brand name is required';
    }
    if (!formData.slug.trim()) {
      newErrors.slug = 'Slug is required';
    }

    // Slug format validation
    if (formData.slug && !/^[a-z0-9-]+$/.test(formData.slug)) {
      newErrors.slug = 'Slug must contain only lowercase letters, numbers, and hyphens';
    }

    // URL validations
    const urlFields: Array<keyof FormData> = ['website', 'support_url', 'logo_url'];
    urlFields.forEach((field) => {
      const value = formData[field];
      if (value && value.trim()) {
        try {
          new URL(value);
        } catch {
          newErrors[field as keyof FormErrors] = 'Must be a valid URL';
        }
      }
    });

    // Founded year validation
    if (formData.founded_year) {
      const year = parseInt(formData.founded_year);
      const currentYear = new Date().getFullYear();
      if (isNaN(year) || year < 1800 || year > currentYear) {
        newErrors.founded_year = `Must be between 1800 and ${currentYear}`;
      }
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
      const brandData = {
        name: formData.name.trim(),
        slug: formData.slug.trim(),
        website: formData.website.trim() || null,
        support_url: formData.support_url.trim() || null,
        logo_url: formData.logo_url.trim() || null,
        description: formData.description.trim() || null,
        founded_year: formData.founded_year ? parseInt(formData.founded_year) : null,
        headquarters: formData.headquarters.trim() || null,
      };

      if (isEditMode) {
        await updateBrand(brand.id, brandData as BrandUpdate);
      } else {
        await createBrand(brandData as BrandCreate);
      }

      onSuccess?.();
      onClose();
    } catch (error) {
      setErrors({
        general: getCatalogErrorMessage(error),
      });
    }
  };

  return (
    <Dialog
      isOpen={isOpen}
      onClose={onClose}
      title={isEditMode ? 'Edit Brand' : 'Add New Brand'}
      description={isEditMode ? 'Update brand information' : 'Add a new device manufacturer to the catalog'}
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* General Error */}
        {errors.general && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-red-400 mb-1">Error</h4>
              <p className="text-sm text-red-300">{errors.general}</p>
            </div>
          </div>
        )}

        {/* Basic Information */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2">
            Basic Information
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Brand Name */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Brand Name <span className="text-red-400">*</span>
              </label>
              <Input
                type="text"
                value={formData.name}
                onChange={(e) => handleNameChange(e.target.value)}
                placeholder="e.g., Dell, Cisco, HPE"
                className={errors.name ? 'border-red-500' : ''}
              />
              {errors.name && (
                <p className="text-xs text-red-400 mt-1">{errors.name}</p>
              )}
            </div>

            {/* Slug */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Slug <span className="text-red-400">*</span>
              </label>
              <Input
                type="text"
                value={formData.slug}
                onChange={(e) => handleChange('slug', e.target.value)}
                placeholder="e.g., dell, cisco, hpe"
                className={errors.slug ? 'border-red-500' : ''}
              />
              {errors.slug && (
                <p className="text-xs text-red-400 mt-1">{errors.slug}</p>
              )}
              <p className="text-xs text-muted-foreground mt-1">
                Lowercase letters, numbers, and hyphens only
              </p>
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              placeholder="Brief description of the brand..."
              rows={3}
              className="w-full px-3 py-2 bg-card border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-electric transition-all resize-none"
            />
          </div>
        </div>

        {/* Company Details */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2">
            Company Details
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Headquarters */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Headquarters
              </label>
              <Input
                type="text"
                value={formData.headquarters}
                onChange={(e) => handleChange('headquarters', e.target.value)}
                placeholder="e.g., Round Rock, TX, USA"
              />
            </div>

            {/* Founded Year */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Founded Year
              </label>
              <Input
                type="number"
                value={formData.founded_year}
                onChange={(e) => handleChange('founded_year', e.target.value)}
                placeholder="e.g., 1984"
                min="1800"
                max={new Date().getFullYear()}
                className={errors.founded_year ? 'border-red-500' : ''}
              />
              {errors.founded_year && (
                <p className="text-xs text-red-400 mt-1">{errors.founded_year}</p>
              )}
            </div>
          </div>
        </div>

        {/* URLs */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-foreground border-b border-border pb-2">
            URLs & Resources
          </h3>

          <div className="space-y-4">
            {/* Website */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Website
              </label>
              <Input
                type="url"
                value={formData.website}
                onChange={(e) => handleChange('website', e.target.value)}
                placeholder="https://example.com"
                className={errors.website ? 'border-red-500' : ''}
              />
              {errors.website && (
                <p className="text-xs text-red-400 mt-1">{errors.website}</p>
              )}
            </div>

            {/* Support URL */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Support URL
              </label>
              <Input
                type="url"
                value={formData.support_url}
                onChange={(e) => handleChange('support_url', e.target.value)}
                placeholder="https://support.example.com"
                className={errors.support_url ? 'border-red-500' : ''}
              />
              {errors.support_url && (
                <p className="text-xs text-red-400 mt-1">{errors.support_url}</p>
              )}
            </div>

            {/* Logo Upload/URL */}
            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Brand Logo
              </label>

              {/* Current Logo Preview */}
              {formData.logo_url && !selectedFile && (
                <div className="mb-3 p-3 bg-secondary/30 border border-border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs text-muted-foreground">Current Logo:</p>
                    {isEditMode && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={handleRemoveLogo}
                        disabled={uploadingLogo}
                        loading={uploadingLogo}
                      >
                        <X className="w-4 h-4" />
                        Remove
                      </Button>
                    )}
                  </div>
                  <img
                    src={formData.logo_url}
                    alt="Current logo"
                    className="h-16 object-contain"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                    }}
                  />
                </div>
              )}

              {/* File Upload Section (Edit mode only) */}
              {isEditMode && (
                <div className="mb-3">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".png,.jpg,.jpeg,.svg,.webp"
                    onChange={handleFileSelect}
                    className="hidden"
                  />

                  {/* Selected File Preview */}
                  {selectedFile && filePreview && (
                    <div className="mb-3 p-3 bg-secondary/30 border border-border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-xs text-muted-foreground">New Logo:</p>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={handleClearFile}
                        >
                          <X className="w-4 h-4" />
                          Clear
                        </Button>
                      </div>
                      <img
                        src={filePreview}
                        alt="Logo preview"
                        className="h-16 object-contain mb-2"
                      />
                      <p className="text-xs text-muted-foreground">
                        {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                      </p>
                    </div>
                  )}

                  {/* Upload Buttons */}
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploadingLogo}
                      leftIcon={<ImageIcon className="w-4 h-4" />}
                    >
                      Choose File
                    </Button>
                    {selectedFile && (
                      <Button
                        type="button"
                        variant="primary"
                        size="sm"
                        onClick={handleUploadLogo}
                        disabled={uploadingLogo}
                        loading={uploadingLogo}
                        leftIcon={<Upload className="w-4 h-4" />}
                      >
                        Upload Logo
                      </Button>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    PNG, JPG, SVG, or WebP (max 5MB)
                  </p>
                </div>
              )}

              {/* Manual URL Input */}
              <div>
                <label className="block text-xs text-muted-foreground mb-1">
                  Or enter URL manually:
                </label>
                <Input
                  type="url"
                  value={formData.logo_url}
                  onChange={(e) => handleChange('logo_url', e.target.value)}
                  placeholder="https://example.com/logo.png"
                  className={errors.logo_url ? 'border-red-500' : ''}
                />
              </div>

              {errors.logo_url && (
                <p className="text-xs text-red-400 mt-1">{errors.logo_url}</p>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <DialogFooter>
          <Button
            type="button"
            variant="ghost"
            onClick={onClose}
            disabled={brandsLoading}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            loading={brandsLoading}
          >
            {isEditMode ? 'Update Brand' : 'Create Brand'}
          </Button>
        </DialogFooter>
      </form>
    </Dialog>
  );
};
