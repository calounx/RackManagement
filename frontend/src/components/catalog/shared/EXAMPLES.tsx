/**
 * Usage Examples for Catalog Shared Components
 *
 * This file contains practical examples of how to use the shared components
 * in your catalog management pages.
 */

import React, { useState } from 'react';
import {
  FormSection,
  FormGrid,
  ConfirmDialog,
  SearchFilterBar,
  PaginationControls,
  EmptyState,
  StatsDashboard,
  MiniStat,
} from './index';
import { Input, TextArea } from '../../ui/input';
import { Button } from '../../ui/button';
import { Dialog, DialogFooter } from '../../ui/dialog';
import {
  Database,
  Search,
  Plus,
  TrendingUp,
  Package,
  Server,
} from 'lucide-react';

// ============================================================================
// Example 1: Form Dialog with FormSection and FormGrid
// ============================================================================

export const ExampleFormDialog: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    website: '',
    description: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Form submitted:', formData);
    setIsOpen(false);
  };

  return (
    <>
      <Button onClick={() => setIsOpen(true)}>Open Form</Button>

      <Dialog
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Add New Brand"
        description="Create a new device manufacturer"
        size="lg"
      >
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information Section */}
          <FormSection
            title="Basic Information"
            description="Enter the core details"
          >
            <FormGrid columns={2}>
              <Input
                label="Brand Name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="e.g., Dell, Cisco, HPE"
                required
              />
              <Input
                label="Slug"
                value={formData.slug}
                onChange={(e) =>
                  setFormData({ ...formData, slug: e.target.value })
                }
                placeholder="e.g., dell, cisco"
                required
              />
            </FormGrid>
          </FormSection>

          {/* URLs Section */}
          <FormSection
            title="URLs & Resources"
            accentColor="rgb(190, 255, 0)"
          >
            <Input
              label="Website"
              type="url"
              value={formData.website}
              onChange={(e) =>
                setFormData({ ...formData, website: e.target.value })
              }
              placeholder="https://example.com"
            />
            <TextArea
              label="Description"
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              placeholder="Brief description of the brand..."
            />
          </FormSection>

          <DialogFooter>
            <Button variant="ghost" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Create Brand
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </>
  );
};

// ============================================================================
// Example 2: ConfirmDialog for Delete Actions
// ============================================================================

export const ExampleConfirmDialog: React.FC = () => {
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleDelete = async () => {
    setLoading(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setLoading(false);
    setShowConfirm(false);
    console.log('Item deleted');
  };

  return (
    <>
      <Button variant="danger" onClick={() => setShowConfirm(true)}>
        Delete Item
      </Button>

      <ConfirmDialog
        isOpen={showConfirm}
        onClose={() => setShowConfirm(false)}
        onConfirm={handleDelete}
        title="Delete Device Type?"
        message="This action cannot be undone. All associated models will be removed from the catalog."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        isLoading={loading}
      />
    </>
  );
};

// ============================================================================
// Example 3: SearchFilterBar with Multiple Filters
// ============================================================================

export const ExampleSearchFilterBar: React.FC = () => {
  const [search, setSearch] = useState('');
  const [brandFilter, setBrandFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  const filters = [
    {
      id: 'brand',
      label: 'Brand',
      value: brandFilter,
      options: [
        { value: 'dell', label: 'Dell' },
        { value: 'cisco', label: 'Cisco' },
        { value: 'hpe', label: 'HPE' },
      ],
    },
    {
      id: 'type',
      label: 'Device Type',
      value: typeFilter,
      options: [
        { value: 'server', label: 'Server' },
        { value: 'switch', label: 'Switch' },
        { value: 'router', label: 'Router' },
      ],
    },
  ];

  const handleFilterChange = (filterId: string, value: string) => {
    if (filterId === 'brand') setBrandFilter(value);
    if (filterId === 'type') setTypeFilter(value);
  };

  const handleClearFilters = () => {
    setBrandFilter('all');
    setTypeFilter('all');
  };

  return (
    <div className="space-y-4">
      <SearchFilterBar
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search models by name or SKU..."
        filters={filters}
        onFilterChange={handleFilterChange}
        onClearFilters={handleClearFilters}
      />

      <div className="text-sm text-muted-foreground">
        Search: "{search}" | Brand: {brandFilter} | Type: {typeFilter}
      </div>
    </div>
  );
};

// ============================================================================
// Example 4: PaginationControls
// ============================================================================

export const ExamplePaginationControls: React.FC = () => {
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 25;
  const totalItems = 237;
  const totalPages = Math.ceil(totalItems / pageSize);

  return (
    <div className="space-y-6">
      <div className="p-4 bg-secondary/30 rounded-lg">
        <p className="text-sm text-muted-foreground">
          Current page: {currentPage} of {totalPages}
        </p>
      </div>

      <PaginationControls
        currentPage={currentPage}
        totalPages={totalPages}
        totalItems={totalItems}
        pageSize={pageSize}
        onPageChange={setCurrentPage}
      />
    </div>
  );
};

// ============================================================================
// Example 5: EmptyState Variations
// ============================================================================

export const ExampleEmptyStates: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* No Data Yet */}
      <div className="border border-border rounded-lg p-8">
        <EmptyState
          icon={Database}
          title="No device types yet"
          description="Get started by creating your first device type category to organize your equipment"
          variant="no-data"
          actionButton={{
            label: 'Add Device Type',
            onClick: () => console.log('Create clicked'),
            icon: Plus,
          }}
        />
      </div>

      {/* No Search Results */}
      <div className="border border-border rounded-lg p-8">
        <EmptyState
          icon={Search}
          title="No results found"
          description="Try adjusting your search criteria or filters to find what you're looking for"
          variant="no-results"
        />
      </div>

      {/* Error State */}
      <div className="border border-border rounded-lg p-8">
        <EmptyState
          icon={Database}
          title="Failed to load data"
          description="An error occurred while fetching the data. Please try again later."
          variant="error"
          actionButton={{
            label: 'Retry',
            onClick: () => console.log('Retry clicked'),
          }}
        />
      </div>
    </div>
  );
};

// ============================================================================
// Example 6: StatsDashboard
// ============================================================================

export const ExampleStatsDashboard: React.FC = () => {
  const stats = [
    {
      icon: Database,
      label: 'Total Types',
      value: 12,
      color: '#00eaff',
      description: 'Device type categories',
    },
    {
      icon: Package,
      label: 'Total Brands',
      value: 45,
      color: '#f97316',
      trend: { value: 8, isPositive: true },
      description: '8% increase this month',
    },
    {
      icon: Server,
      label: 'Active Models',
      value: 237,
      color: '#10b981',
      trend: { value: 12, isPositive: true },
      description: '12% growth',
    },
    {
      icon: TrendingUp,
      label: 'Monthly Growth',
      value: '+15%',
      color: '#8b5cf6',
      description: 'Compared to last month',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Full Dashboard */}
      <StatsDashboard stats={stats} columns={4} />

      {/* 3 Column Layout */}
      <StatsDashboard stats={stats.slice(0, 3)} columns={3} />

      {/* Mini Stats */}
      <div className="flex flex-wrap gap-4 p-4 bg-secondary/30 rounded-lg">
        <MiniStat icon={Database} label="Types" value={12} color="#00eaff" />
        <MiniStat icon={Package} label="Brands" value={45} color="#f97316" />
        <MiniStat icon={Server} label="Models" value={237} color="#10b981" />
      </div>
    </div>
  );
};

// ============================================================================
// Example 7: Complete List Page Pattern
// ============================================================================

interface Item {
  id: number;
  name: string;
  description: string;
}

export const ExampleCompleteListPage: React.FC = () => {
  const [items] = useState<Item[]>([]);
  const [search, setSearch] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const stats = [
    { icon: Database, label: 'Total Items', value: 50, color: '#00eaff' },
    { icon: TrendingUp, label: 'Active', value: 45, color: '#10b981' },
    { icon: Package, label: 'Categories', value: 8, color: '#f97316' },
  ];

  const handleCreate = () => {
    console.log('Create item');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-foreground">
            Device Types
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Manage device categories and their visual appearance
          </p>
        </div>
        <Button variant="primary" leftIcon={<Plus className="w-4 h-4" />} onClick={handleCreate}>
          Add Device Type
        </Button>
      </div>

      {/* Stats Dashboard */}
      <StatsDashboard stats={stats} columns={3} />

      {/* Search Bar */}
      <SearchFilterBar
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search device types..."
      />

      {/* Content or Empty State */}
      {items.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {items.map((item) => (
              <div
                key={item.id}
                className="p-4 glass rounded-lg border border-border"
              >
                <h3 className="font-semibold text-foreground">{item.name}</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
          <PaginationControls
            currentPage={currentPage}
            totalPages={5}
            totalItems={50}
            pageSize={10}
            onPageChange={setCurrentPage}
          />
        </>
      ) : (
        <EmptyState
          icon={Database}
          title={search ? 'No results found' : 'No device types yet'}
          description={
            search
              ? 'Try adjusting your search criteria'
              : 'Get started by creating your first device type category'
          }
          variant={search ? 'no-results' : 'no-data'}
          actionButton={
            !search
              ? {
                  label: 'Add Your First Device Type',
                  onClick: handleCreate,
                  icon: Plus,
                }
              : undefined
          }
        />
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => setShowDeleteConfirm(false)}
        onConfirm={() => {
          console.log('Delete confirmed');
          setShowDeleteConfirm(false);
        }}
        title="Delete Device Type?"
        message="This action cannot be undone. All associated models will be removed."
        confirmText="Delete"
        variant="danger"
      />
    </div>
  );
};
