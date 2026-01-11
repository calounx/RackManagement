# Catalog Shared Components

A collection of reusable UI components for the catalog management system (Device Types, Brands, and Models). These components provide consistent styling, behavior, and user experience across all catalog pages.

## Design Philosophy

These components follow the HomeRack design system:
- **Electric Blue Accents** (`#00eaff`) - Primary interactive elements
- **Glass Morphism** - Translucent cards with backdrop blur
- **Framer Motion Animations** - Smooth, purposeful transitions
- **Accessibility First** - ARIA labels, keyboard navigation, focus management
- **Responsive Design** - Mobile-first with adaptive layouts

## Components

### 1. FormSection

A wrapper for form sections with consistent styling and visual hierarchy.

#### Features
- Electric blue indicator bar
- Optional description text
- Consistent padding and spacing
- Animated entrance

#### Usage

```tsx
import { FormSection, FormGrid } from '@/components/catalog/shared';

<FormSection
  title="Basic Information"
  description="Enter the core details"
>
  <FormGrid columns={2}>
    <Input label="Name" />
    <Input label="Slug" />
  </FormGrid>
</FormSection>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| title | string | required | Section heading |
| description | string | undefined | Optional description text |
| children | ReactNode | required | Form content |
| accentColor | string | `rgb(0, 234, 255)` | Left border color |
| className | string | undefined | Additional CSS classes |

---

### 2. ConfirmDialog

A reusable confirmation dialog for destructive actions and important decisions.

#### Features
- Modal overlay with backdrop blur
- Variant styling (danger/warning/info)
- Loading states
- Keyboard shortcuts (Enter = confirm, Esc = cancel)
- Accessible focus trap

#### Usage

```tsx
import { ConfirmDialog } from '@/components/catalog/shared';

const [isOpen, setIsOpen] = useState(false);
const [loading, setLoading] = useState(false);

const handleDelete = async () => {
  setLoading(true);
  try {
    await deleteItem(id);
    setIsOpen(false);
  } catch (error) {
    // Handle error
  } finally {
    setLoading(false);
  }
};

<ConfirmDialog
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  onConfirm={handleDelete}
  title="Delete Device Type?"
  message="This action cannot be undone. All associated models will also be removed."
  confirmText="Delete"
  variant="danger"
  isLoading={loading}
/>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| isOpen | boolean | required | Dialog visibility |
| onClose | () => void | required | Close handler |
| onConfirm | () => void \| Promise<void> | required | Confirm handler |
| title | string | required | Dialog title |
| message | string | required | Confirmation message |
| confirmText | string | `"Confirm"` | Confirm button text |
| cancelText | string | `"Cancel"` | Cancel button text |
| isLoading | boolean | `false` | Loading state |
| variant | `'danger'` \| `'warning'` \| `'info'` | `'danger'` | Visual variant |

---

### 3. SearchFilterBar

A comprehensive search and filter bar with multiple filter support.

#### Features
- Search input with clear button
- Multiple filter dropdowns
- Active filter count badge
- Clear all filters button
- Responsive layout

#### Usage

```tsx
import { SearchFilterBar } from '@/components/catalog/shared';

const [search, setSearch] = useState('');
const [brandFilter, setBrandFilter] = useState('all');
const [typeFilter, setTypeFilter] = useState('all');

const filters = [
  {
    id: 'brand',
    label: 'Brand',
    value: brandFilter,
    options: brands.map(b => ({ value: b.id, label: b.name }))
  },
  {
    id: 'type',
    label: 'Type',
    value: typeFilter,
    options: types.map(t => ({ value: t.id, label: t.name }))
  }
];

const handleFilterChange = (filterId: string, value: string) => {
  if (filterId === 'brand') setBrandFilter(value);
  if (filterId === 'type') setTypeFilter(value);
};

const handleClearFilters = () => {
  setBrandFilter('all');
  setTypeFilter('all');
};

<SearchFilterBar
  searchValue={search}
  onSearchChange={setSearch}
  searchPlaceholder="Search models..."
  filters={filters}
  onFilterChange={handleFilterChange}
  onClearFilters={handleClearFilters}
/>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| searchValue | string | required | Search input value |
| onSearchChange | (value: string) => void | required | Search change handler |
| searchPlaceholder | string | `"Search..."` | Search placeholder |
| filters | FilterConfig[] | `[]` | Filter configurations |
| onFilterChange | (filterId: string, value: string) => void | undefined | Filter change handler |
| onClearFilters | () => void | undefined | Clear all handler |
| className | string | undefined | Additional CSS classes |

---

### 4. PaginationControls

Standardized pagination with page numbers and navigation.

#### Features
- Previous/Next navigation
- First/Last page buttons
- Page number buttons with ellipsis
- Result counter
- Responsive layout
- Boundary detection

#### Usage

```tsx
import { PaginationControls } from '@/components/catalog/shared';

const [currentPage, setCurrentPage] = useState(1);
const pageSize = 25;
const totalItems = 500;
const totalPages = Math.ceil(totalItems / pageSize);

<PaginationControls
  currentPage={currentPage}
  totalPages={totalPages}
  totalItems={totalItems}
  pageSize={pageSize}
  onPageChange={setCurrentPage}
/>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| currentPage | number | required | Current page number (1-indexed) |
| totalPages | number | required | Total number of pages |
| totalItems | number | required | Total number of items |
| pageSize | number | required | Items per page |
| onPageChange | (page: number) => void | required | Page change handler |
| showPageNumbers | boolean | `true` | Show page number buttons |
| maxPageButtons | number | `7` | Max page buttons to show |
| className | string | undefined | Additional CSS classes |

---

### 5. EmptyState

A friendly empty state component for no data or no results scenarios.

#### Features
- Icon display with color theming
- Title and description
- Optional CTA button
- Multiple variants
- Decorative background elements

#### Usage

```tsx
import { EmptyState } from '@/components/catalog/shared';
import { Database, Plus } from 'lucide-react';

// No data yet
<EmptyState
  icon={Database}
  title="No device types yet"
  description="Get started by creating your first device type category"
  variant="no-data"
  actionButton={{
    label: "Add Device Type",
    onClick: handleCreate,
    icon: Plus
  }}
/>

// No search results
<EmptyState
  icon={Search}
  title="No results found"
  description="Try adjusting your search criteria or filters"
  variant="no-results"
/>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| icon | LucideIcon | required | Icon component |
| title | string | required | Empty state title |
| description | string | required | Description text |
| actionButton | { label, onClick, icon? } | undefined | Optional action button |
| variant | `'no-data'` \| `'no-results'` \| `'error'` | `'no-data'` | Visual variant |
| className | string | undefined | Additional CSS classes |

---

### 6. StatsDashboard

A responsive dashboard for displaying statistics with icons and trends.

#### Features
- Responsive grid (1-4 columns)
- Icon + label + value pattern
- Color-coded icons
- Optional trend indicators
- Hover animations
- Staggered entrance animations

#### Usage

```tsx
import { StatsDashboard } from '@/components/catalog/shared';
import { Database, TrendingUp, Package } from 'lucide-react';

const stats = [
  {
    icon: Database,
    label: "Total Types",
    value: deviceTypes.length,
    color: "#00eaff"
  },
  {
    icon: TrendingUp,
    label: "Active Models",
    value: 150,
    color: "#10b981",
    trend: { value: 12, isPositive: true },
    description: "12% increase this month"
  },
  {
    icon: Package,
    label: "Brands",
    value: 25,
    color: "#f97316"
  }
];

<StatsDashboard stats={stats} columns={3} />
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| stats | StatItem[] | required | Array of stat items |
| columns | 1 \| 2 \| 3 \| 4 | `3` | Number of columns |
| className | string | undefined | Additional CSS classes |
| animated | boolean | `true` | Enable entrance animations |

**StatItem Interface:**

```typescript
interface StatItem {
  icon: LucideIcon;
  label: string;
  value: string | number;
  color?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  description?: string;
}
```

---

## Common Patterns

### Form Dialog Pattern

```tsx
import { Dialog } from '@/components/ui/dialog';
import { FormSection, FormGrid } from '@/components/catalog/shared';

<Dialog isOpen={isOpen} onClose={onClose} title="Add Item">
  <form onSubmit={handleSubmit}>
    <FormSection title="Basic Information">
      <FormGrid columns={2}>
        <Input label="Name" />
        <Input label="Slug" />
      </FormGrid>
    </FormSection>

    <FormSection title="Details" description="Additional information">
      <TextArea label="Description" />
    </FormSection>

    <DialogFooter>
      <Button variant="ghost" onClick={onClose}>Cancel</Button>
      <Button variant="primary" type="submit">Save</Button>
    </DialogFooter>
  </form>
</Dialog>
```

### List Page Pattern

```tsx
import {
  SearchFilterBar,
  StatsDashboard,
  EmptyState,
  PaginationControls
} from '@/components/catalog/shared';

const ListPage = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2>Device Types</h2>
          <p>Manage device categories</p>
        </div>
        <Button onClick={handleCreate}>Add Device Type</Button>
      </div>

      {/* Stats Dashboard */}
      <StatsDashboard stats={stats} columns={3} />

      {/* Search & Filters */}
      <SearchFilterBar
        searchValue={search}
        onSearchChange={setSearch}
        filters={filters}
        onFilterChange={handleFilterChange}
      />

      {/* Content */}
      {items.length > 0 ? (
        <>
          <div className="grid grid-cols-3 gap-4">
            {items.map(item => <ItemCard key={item.id} item={item} />)}
          </div>
          <PaginationControls {...paginationProps} />
        </>
      ) : (
        <EmptyState
          icon={Database}
          title="No items found"
          description="Get started by adding your first item"
          actionButton={{ label: "Add Item", onClick: handleCreate }}
        />
      )}
    </div>
  );
};
```

## Accessibility

All components follow WCAG 2.1 Level AA guidelines:

- **Keyboard Navigation**: All interactive elements are keyboard accessible
- **Focus Management**: Visible focus indicators and proper focus trap in dialogs
- **ARIA Labels**: Proper labeling for screen readers
- **Color Contrast**: Minimum 4.5:1 contrast ratio for text
- **Semantic HTML**: Proper use of headings, buttons, and landmarks

## Styling

Components use Tailwind CSS with the HomeRack design tokens:

```css
--electric-blue: 0 234 255
--lime: 190 255 0
--amber: 251 191 36
--border: [theme border color]
--foreground: [theme text color]
--muted-foreground: [theme muted text]
```

## Best Practices

1. **Consistent Imports**: Use barrel exports
   ```tsx
   import { FormSection, ConfirmDialog } from '@/components/catalog/shared';
   ```

2. **Type Safety**: All components are fully typed with TypeScript

3. **Responsive Design**: Test on mobile, tablet, and desktop viewports

4. **Animation Performance**: Components use GPU-accelerated transforms

5. **Error Handling**: Always handle loading and error states

6. **Accessibility**: Test with keyboard navigation and screen readers

## Examples

See the existing catalog pages for complete implementation examples:
- `/components/catalog/DeviceTypesManagement.tsx`
- `/components/catalog/BrandsManagement.tsx`
- `/components/catalog/ModelsManagement.tsx`
