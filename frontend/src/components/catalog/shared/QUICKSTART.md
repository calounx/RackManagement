# Quick Start Guide - Catalog Shared Components

Get up and running with the shared components in 5 minutes.

## Installation

Components are already available in your project:
```typescript
import { ComponentName } from '@/components/catalog/shared';
```

## Common Use Cases

### 1. Add Stats to Your Page (30 seconds)

```typescript
import { StatsDashboard } from '@/components/catalog/shared';
import { Database, Package, TrendingUp } from 'lucide-react';

const stats = [
  { icon: Database, label: 'Total Items', value: 50, color: '#00eaff' },
  { icon: Package, label: 'Categories', value: 8, color: '#f97316' },
  { icon: TrendingUp, label: 'Active', value: 45, color: '#10b981' },
];

<StatsDashboard stats={stats} columns={3} />
```

### 2. Add Search and Filters (1 minute)

```typescript
import { SearchFilterBar } from '@/components/catalog/shared';

const [search, setSearch] = useState('');

<SearchFilterBar
  searchValue={search}
  onSearchChange={setSearch}
  searchPlaceholder="Search items..."
/>
```

### 3. Add Empty State (30 seconds)

```typescript
import { EmptyState } from '@/components/catalog/shared';
import { Database, Plus } from 'lucide-react';

<EmptyState
  icon={Database}
  title="No items yet"
  description="Get started by creating your first item"
  variant="no-data"
  actionButton={{
    label: "Add Item",
    onClick: handleCreate,
    icon: Plus
  }}
/>
```

### 4. Add Pagination (30 seconds)

```typescript
import { PaginationControls } from '@/components/catalog/shared';

const [page, setPage] = useState(1);

<PaginationControls
  currentPage={page}
  totalPages={10}
  totalItems={250}
  pageSize={25}
  onPageChange={setPage}
/>
```

### 5. Add Delete Confirmation (1 minute)

```typescript
import { ConfirmDialog } from '@/components/catalog/shared';

const [showConfirm, setShowConfirm] = useState(false);

// Delete button
<Button variant="danger" onClick={() => setShowConfirm(true)}>
  Delete
</Button>

// Confirmation dialog
<ConfirmDialog
  isOpen={showConfirm}
  onClose={() => setShowConfirm(false)}
  onConfirm={async () => {
    await deleteItem();
    setShowConfirm(false);
  }}
  title="Delete Item?"
  message="This action cannot be undone."
  variant="danger"
/>
```

### 6. Add Form Sections (2 minutes)

```typescript
import { Dialog } from '@/components/ui/dialog';
import { FormSection, FormGrid } from '@/components/catalog/shared';

<Dialog isOpen={isOpen} onClose={onClose} title="Add Item">
  <form onSubmit={handleSubmit}>
    <FormSection title="Basic Information">
      <FormGrid columns={2}>
        <Input label="Name" value={name} onChange={e => setName(e.target.value)} />
        <Input label="Slug" value={slug} onChange={e => setSlug(e.target.value)} />
      </FormGrid>
    </FormSection>

    <FormSection title="Details">
      <TextArea label="Description" value={desc} onChange={e => setDesc(e.target.value)} />
    </FormSection>

    <DialogFooter>
      <Button variant="ghost" onClick={onClose}>Cancel</Button>
      <Button variant="primary" type="submit">Save</Button>
    </DialogFooter>
  </form>
</Dialog>
```

## Complete Example: List Page

Copy-paste template for a complete list page:

```typescript
import React, { useState, useEffect } from 'react';
import { Plus, Database } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  StatsDashboard,
  SearchFilterBar,
  EmptyState,
  PaginationControls,
  ConfirmDialog
} from '@/components/catalog/shared';

export const MyListPage: React.FC = () => {
  // State
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [deleteId, setDeleteId] = useState<number | null>(null);

  // Stats
  const stats = [
    { icon: Database, label: 'Total Items', value: items.length, color: '#00eaff' },
  ];

  // Handlers
  const handleCreate = () => {
    // Open create dialog
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    await api.delete(deleteId);
    setDeleteId(null);
    // Refresh data
  };

  // Fetch data
  useEffect(() => {
    fetchData();
  }, [search, page]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-foreground">My Items</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Manage your items
          </p>
        </div>
        <Button variant="primary" leftIcon={<Plus className="w-4 h-4" />} onClick={handleCreate}>
          Add Item
        </Button>
      </div>

      {/* Stats */}
      <StatsDashboard stats={stats} columns={3} />

      {/* Search */}
      <SearchFilterBar
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="Search items..."
      />

      {/* Content */}
      {loading ? (
        <div>Loading...</div>
      ) : items.length > 0 ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {items.map(item => (
              <div key={item.id} className="p-4 glass rounded-lg border border-border">
                {/* Item content */}
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => setDeleteId(item.id)}
                >
                  Delete
                </Button>
              </div>
            ))}
          </div>
          <PaginationControls
            currentPage={page}
            totalPages={Math.ceil(items.length / 25)}
            totalItems={items.length}
            pageSize={25}
            onPageChange={setPage}
          />
        </>
      ) : (
        <EmptyState
          icon={Database}
          title={search ? "No results found" : "No items yet"}
          description={search ? "Try adjusting your search" : "Get started by adding your first item"}
          variant={search ? "no-results" : "no-data"}
          actionButton={!search ? {
            label: "Add Your First Item",
            onClick: handleCreate,
            icon: Plus
          } : undefined}
        />
      )}

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={deleteId !== null}
        onClose={() => setDeleteId(null)}
        onConfirm={handleDelete}
        title="Delete Item?"
        message="This action cannot be undone."
        variant="danger"
      />
    </div>
  );
};
```

## Tips & Tricks

### 1. Customizing Colors
```typescript
// Use custom accent colors
<FormSection title="Basic Info" accentColor="rgb(190, 255, 0)" />
```

### 2. Conditional Rendering
```typescript
// Show different empty states
{items.length === 0 && !loading && (
  search ? (
    <EmptyState variant="no-results" {...} />
  ) : (
    <EmptyState variant="no-data" {...} />
  )
)}
```

### 3. Multiple Filters
```typescript
const filters = [
  {
    id: 'category',
    label: 'Category',
    value: category,
    options: categories.map(c => ({ value: c.id, label: c.name }))
  },
  {
    id: 'status',
    label: 'Status',
    value: status,
    options: [
      { value: 'active', label: 'Active' },
      { value: 'inactive', label: 'Inactive' }
    ]
  }
];

<SearchFilterBar
  searchValue={search}
  onSearchChange={setSearch}
  filters={filters}
  onFilterChange={(id, value) => {
    if (id === 'category') setCategory(value);
    if (id === 'status') setStatus(value);
  }}
  onClearFilters={() => {
    setCategory('all');
    setStatus('all');
  }}
/>
```

### 4. Async Delete Confirmation
```typescript
const [deleteLoading, setDeleteLoading] = useState(false);

const handleDelete = async () => {
  setDeleteLoading(true);
  try {
    await api.delete(id);
    toast.success('Deleted successfully');
    setShowConfirm(false);
  } catch (error) {
    toast.error('Failed to delete');
  } finally {
    setDeleteLoading(false);
  }
};

<ConfirmDialog
  isOpen={showConfirm}
  onConfirm={handleDelete}
  isLoading={deleteLoading}
  {...}
/>
```

### 5. Stats with Trends
```typescript
const stats = [
  {
    icon: TrendingUp,
    label: 'Active Users',
    value: 1234,
    color: '#10b981',
    trend: { value: 12, isPositive: true },
    description: '12% increase this month'
  },
  {
    icon: TrendingDown,
    label: 'Response Time',
    value: '150ms',
    color: '#ef4444',
    trend: { value: -5, isPositive: false },
    description: '5% slower than last week'
  }
];
```

## Common Patterns

### Loading State
```typescript
{loading && (
  <div className="flex items-center justify-center py-12">
    <Loader2 className="w-8 h-8 text-electric animate-spin" />
  </div>
)}
```

### Error State
```typescript
{error && (
  <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
    <p className="text-red-400">{error}</p>
  </div>
)}
```

### Filtered Results Count
```typescript
const filteredItems = items.filter(item =>
  item.name.toLowerCase().includes(search.toLowerCase())
);

<p className="text-sm text-muted-foreground">
  Showing {filteredItems.length} of {items.length} items
</p>
```

## Troubleshooting

### Component Not Found
```typescript
// Make sure you're importing from the correct path
import { ComponentName } from '@/components/catalog/shared';

// If '@/' alias doesn't work, use relative path
import { ComponentName } from '../catalog/shared';
```

### Type Errors
```typescript
// Import types explicitly
import type { StatItem, FilterConfig } from '@/components/catalog/shared';

// Or get types from the component
import { StatsDashboard } from '@/components/catalog/shared';
type StatItem = React.ComponentProps<typeof StatsDashboard>['stats'][0];
```

### Styling Issues
```typescript
// Add custom classes with className prop
<FormSection title="..." className="mb-8" />

// Override Tailwind classes
<StatsDashboard stats={stats} className="grid-cols-4" />
```

## Next Steps

1. Check out [README.md](./README.md) for detailed documentation
2. See [EXAMPLES.tsx](./EXAMPLES.tsx) for more usage examples
3. Review [ARCHITECTURE.md](./ARCHITECTURE.md) for design patterns
4. Look at existing catalog pages for real-world usage

## Support

Need help? Check these resources:
- Component props: TypeScript IntelliSense
- Usage examples: EXAMPLES.tsx
- Design patterns: ARCHITECTURE.md
- Full docs: README.md

---

**Pro Tip**: Start with the "Complete Example" above and customize it for your needs. Most catalog pages follow this exact pattern!
