# Catalog Shared Components - Architecture

## Component Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                      Catalog Management Page                 │
│                   (DeviceTypes/Brands/Models)                │
└─────────────────────────────────────────────────────────────┘
                              │
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│ StatsDashboard│    │ SearchFilterBar  │    │ ConfirmDialog│
│ (Top Stats)  │    │ (Search+Filters) │    │ (Modals)     │
└──────────────┘    └──────────────────┘    └──────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│  EmptyState  │    │   Content Grid   │    │ Form Dialogs │
│ (No Results) │    │   (Item Cards)   │    │ (Create/Edit)│
└──────────────┘    └──────────────────┘    └──────────────┘
                              │                     │
                              ▼                     ▼
                    ┌──────────────────┐    ┌──────────────┐
                    │PaginationControls│    │ FormSection  │
                    │  (Navigation)    │    │ (Sections)   │
                    └──────────────────┘    └──────────────┘
```

## Component Relationships

### 1. Page-Level Components
Components that structure the entire page:

```
Page Layout
├── Header Section
│   ├── Title & Description
│   └── Action Button (Create/Add)
├── StatsDashboard (Summary metrics)
├── SearchFilterBar (Search + Filters)
├── Content Section
│   ├── EmptyState (if no items)
│   └── OR
│   ├── Grid/List of Items
│   └── PaginationControls
└── Dialogs (rendered at root level)
    ├── Form Dialog (Create/Edit)
    │   └── FormSection(s)
    └── ConfirmDialog (Delete/Actions)
```

### 2. Dialog Components
Components for modal interactions:

```
Dialog (from ui/dialog)
├── Dialog Header
├── Dialog Content
│   └── FormSection(s)
│       ├── FormSection title="Basic Info"
│       │   └── FormGrid columns={2}
│       │       ├── Input
│       │       └── Input
│       └── FormSection title="Details"
│           └── TextArea
└── DialogFooter
    ├── Cancel Button
    └── Submit Button
```

### 3. Data Flow

```
┌──────────────┐
│  User Action │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  Event Handler   │
│  (Page Level)    │
└──────┬───────────┘
       │
       ├──────────────────┐
       │                  │
       ▼                  ▼
┌─────────────┐    ┌──────────────┐
│ Update State│    │  API Call    │
└──────┬──────┘    └──────┬───────┘
       │                  │
       ▼                  ▼
┌─────────────┐    ┌──────────────┐
│ Re-render   │    │ Update Store │
│ Components  │    │ (Zustand)    │
└─────────────┘    └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │  Notify User │
                   │   (Toast)    │
                   └──────────────┘
```

## Usage Patterns

### Pattern 1: List Page with Stats
```typescript
<Page>
  <Header />
  <StatsDashboard stats={...} />        // Shows aggregate data
  <SearchFilterBar {...} />             // User input
  {items.length > 0 ? (
    <>
      <ItemGrid items={...} />          // Display items
      <PaginationControls {...} />      // Navigate pages
    </>
  ) : (
    <EmptyState {...} />                // No results
  )}
  <ConfirmDialog {...} />               // Delete confirmation
</Page>
```

### Pattern 2: Form Dialog
```typescript
<Dialog isOpen={...} onClose={...}>
  <form onSubmit={...}>
    <FormSection title="Basic Information">
      <FormGrid columns={2}>
        <Input label="Name" {...} />
        <Input label="Slug" {...} />
      </FormGrid>
    </FormSection>

    <FormSection title="Details">
      <TextArea label="Description" {...} />
    </FormSection>

    <DialogFooter>
      <Button>Cancel</Button>
      <Button>Save</Button>
    </DialogFooter>
  </form>
</Dialog>
```

### Pattern 3: Delete Confirmation
```typescript
// 1. User clicks delete
<Button onClick={() => setShowConfirm(true)}>
  Delete
</Button>

// 2. Show confirmation
<ConfirmDialog
  isOpen={showConfirm}
  onClose={() => setShowConfirm(false)}
  onConfirm={handleDelete}
  variant="danger"
  {...}
/>

// 3. Handle deletion
const handleDelete = async () => {
  setLoading(true);
  await api.delete(id);
  toast.success('Deleted');
  setShowConfirm(false);
};
```

## State Management

### Component State
Each component manages its own UI state:
- **FormSection**: Animation state
- **ConfirmDialog**: Keyboard event listeners, body scroll lock
- **SearchFilterBar**: Clear button visibility
- **PaginationControls**: Page number calculations
- **EmptyState**: Animation state
- **StatsDashboard**: Hover effects, stagger delays

### Page State
Parent pages manage:
- Data fetching and caching
- User inputs (search, filters, page)
- Dialog visibility
- Loading/error states

### Global State (Zustand)
Catalog store manages:
- API data (device types, brands, models)
- CRUD operations
- Loading/error states
- Cache invalidation

```typescript
useCatalogStore:
  - deviceTypes[]
  - brands[]
  - models[]
  - loading states
  - error states
  - CRUD operations
```

## Component Communication

### Props Down
Parent → Child data flow:
```typescript
<SearchFilterBar
  searchValue={search}              // State
  onSearchChange={setSearch}        // Updater
  filters={filterConfig}            // Config
  onFilterChange={handleFilter}     // Handler
/>
```

### Events Up
Child → Parent communication via callbacks:
```typescript
const handleFilterChange = (id: string, value: string) => {
  // Update parent state
  setFilters({ ...filters, [id]: value });

  // Trigger side effects
  fetchData({ ...filters, [id]: value });
};
```

### Context (Limited Use)
- Theme context (dark/light mode)
- Toast notifications (useStore)
- No component-specific contexts

## Styling Architecture

### CSS Layers
```
Base Styles (Tailwind)
└── Component Classes
    └── Variant Classes
        └── State Classes (hover, focus, disabled)
            └── Custom Classes (className prop)
```

### Responsive Strategy
Mobile-first with breakpoints:
```scss
// Base (Mobile)
.grid { grid-cols: 1 }

// Tablet (md: 768px)
@media (min-width: 768px) {
  .grid { grid-cols: 2 }
}

// Desktop (lg: 1024px)
@media (min-width: 1024px) {
  .grid { grid-cols: 3 }
}
```

### Color System
```typescript
// Semantic colors from design system
--electric: #00eaff      // Primary actions
--lime: #beff00          // Success
--amber: #fbbf24         // Warning
--red: #ef4444           // Danger/Error

// Theme colors (auto-switching)
--foreground             // Main text
--background             // Page background
--border                 // Borders
--muted-foreground       // Secondary text
```

## Performance Optimization

### Component Level
- React.memo for expensive renders
- useMemo for computed values
- useCallback for stable references
- Lazy loading for dialogs

### Animation Level
- GPU-accelerated transforms
- RequestAnimationFrame for smooth animations
- Reduced motion support
- Stagger delays < 50ms

### Bundle Level
- Tree-shakeable exports
- Code splitting at route level
- Dynamic imports for heavy components
- Optimized icon imports

## Accessibility Tree

```
Page [role="main"]
├── Header [role="banner"]
│   ├── Heading [level=1]
│   └── Button [aria-label="Add item"]
├── Stats [role="region" aria-label="Statistics"]
│   └── Multiple stats [aria-live="polite"]
├── Search [role="search"]
│   ├── Input [aria-label="Search"]
│   └── Filters [role="group"]
├── Content [role="region" aria-label="Items"]
│   ├── EmptyState [role="status"]
│   └── OR
│   ├── Grid [role="list"]
│   │   └── Items [role="listitem"]
│   └── Pagination [role="navigation" aria-label="Pagination"]
└── Dialogs [role="dialog" aria-modal="true"]
    ├── Form Dialog
    └── Confirm Dialog [role="alertdialog"]
```

## Error Boundaries

```
App
└── ErrorBoundary (Page Level)
    └── CatalogPage
        ├── StatsDashboard (isolated)
        ├── SearchFilterBar (isolated)
        └── ContentSection
            └── ErrorBoundary (Component Level)
                └── Items
```

Each major section should handle its own errors:
- API failures show inline errors
- Component crashes show error boundary
- Network errors show retry options

## Testing Strategy

### Unit Tests
```
Component Tests
├── Props rendering
├── Event handlers
├── Conditional logic
├── Accessibility attributes
└── Error states
```

### Integration Tests
```
Feature Tests
├── Search flow
├── Filter interactions
├── Pagination navigation
├── Form submission
└── Delete confirmation
```

### E2E Tests
```
User Flows
├── Create item flow
├── Edit item flow
├── Delete item flow
├── Search and filter flow
└── Pagination flow
```

## Migration Guide

### From Inline Components
```typescript
// Before
<div className="p-4 border-l-2 border-electric">
  <h3>Basic Information</h3>
  <div className="grid grid-cols-2 gap-4">
    <Input />
    <Input />
  </div>
</div>

// After
<FormSection title="Basic Information">
  <FormGrid columns={2}>
    <Input />
    <Input />
  </FormGrid>
</FormSection>
```

### From Custom Implementations
1. Identify similar patterns in existing code
2. Replace with shared component
3. Move custom logic to page level
4. Test thoroughly
5. Remove duplicate code

## Future Enhancements

### Potential Additions
- [ ] BulkActionBar (select multiple items)
- [ ] AdvancedFilters (date ranges, multi-select)
- [ ] ExportButton (CSV, JSON export)
- [ ] ImportDialog (bulk import)
- [ ] SortControls (column sorting)
- [ ] ViewToggle (grid vs list view)
- [ ] QuickActions (inline actions menu)

### API Improvements
- [ ] Infinite scroll option for pagination
- [ ] Virtual scrolling for large lists
- [ ] Optimistic updates
- [ ] Real-time updates (WebSocket)
- [ ] Offline support

---

**Last Updated**: 2026-01-11
**Version**: 1.0.0
