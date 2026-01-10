# HomeRack Frontend - Component Guide

## Complete File Structure

### Core Files (4)
- `src/main.tsx` - Application entry point
- `src/App.tsx` - Main app with routing and layout
- `src/index.css` - Global styles with Precision Engineering theme
- `src/types/index.ts` - TypeScript type definitions (200+ lines)

### Utilities & State (3)
- `src/lib/utils.ts` - Utility functions (cn, formatting, validation)
- `src/lib/api.ts` - Axios API client with full backend integration
- `src/store/useStore.ts` - Zustand state management (400+ lines)

### UI Components (6)
All located in `src/components/ui/`

1. **button.tsx** - Multi-variant button component
   - Variants: primary, secondary, outline, ghost, danger
   - Sizes: sm, md, lg
   - Loading state with spinner
   - Icon support (left/right)
   - Framer Motion animations

2. **card.tsx** - Modular card system
   - Card (base container)
   - CardHeader, CardTitle, CardDescription
   - CardContent, CardFooter
   - Glass and interactive variants

3. **badge.tsx** - Status indicators
   - Variants: success, warning, error, info
   - Optional glow effects
   - Pulse animation
   - Status dot indicator

4. **input.tsx** - Form controls
   - Input - Standard text input with icons
   - TextArea - Multi-line input
   - Select - Dropdown selector
   - Label and error state support

5. **dialog.tsx** - Modal dialogs
   - Backdrop with blur
   - Escape key handling
   - Size variants (sm, md, lg, xl)
   - Animated entrance/exit
   - DialogFooter helper

6. **toast.tsx** - Notifications
   - ToastContainer (global)
   - ToastItem (individual)
   - 4 types: success, error, warning, info
   - Auto-dismiss with configurable duration
   - Stacking support

### Layout Components (2)
Located in `src/components/layout/`

1. **Sidebar.tsx**
   - Navigation menu with icons
   - Active route highlighting
   - Logo/branding section
   - System status indicator
   - Smooth hover animations

2. **Header.tsx**
   - Page title with breadcrumbs
   - Search bar
   - Refresh button
   - Notification bell
   - User menu

### Rack Components (3)
Located in `src/components/rack/`

1. **RackVisualizer.tsx**
   - Full 42U rack display
   - Unit numbering (bottom-up)
   - Device placement visualization
   - Click handlers for units
   - Rack statistics footer
   - Power/utilization metrics

2. **DeviceSlot.tsx**
   - Individual device in rack
   - Height-based scaling (1U-4U+)
   - Status indicators with LED
   - Device info display
   - Color-coded by type
   - Thermal indicators
   - Hover effects

3. **ThermalOverlay.tsx**
   - Heat map visualization
   - Temperature gradient overlay
   - Real-time data fetching
   - Thermal legend
   - Airflow direction indicator
   - Auto-refresh (10s interval)

### Device Components (2)
Located in `src/components/devices/`

1. **DeviceCard.tsx**
   - Grid/list view card
   - Device specifications
   - Status badge
   - Power/temp metrics
   - Edit/delete actions
   - Click to view details

2. **SpecFetcher.tsx**
   - Auto-fetch device specs
   - URL input form
   - Loading states
   - Integration with API

### Connection Components (1)
Located in `src/components/connections/`

1. **CableValidator.tsx**
   - Connection validation display
   - Port compatibility check
   - Cable length validation
   - Speed matching warnings

### Dashboard Components (2)
Located in `src/components/dashboard/`

1. **StatsCard.tsx**
   - Metric display card
   - Icon + value layout
   - Color-coded by type
   - Hover animations

2. **SystemHealth.tsx**
   - System status indicators
   - API/DB connection status
   - Service health badges

### Page Components (6)
Located in `src/pages/`

1. **Dashboard.tsx**
   - System overview
   - Stats grid (4 cards)
   - Power/thermal widgets
   - Recent devices list
   - Quick links

2. **Racks.tsx**
   - Rack list sidebar
   - Selected rack visualizer
   - Add rack button
   - Device interaction

3. **Devices.tsx**
   - Device grid view
   - Search/filter bar
   - Add device button
   - Device cards

4. **Connections.tsx**
   - Connection table
   - Cable type indicators
   - Status badges
   - Add connection form

5. **ThermalAnalysis.tsx**
   - Temperature monitoring
   - Heat maps (placeholder)
   - Future: Charts & analytics

6. **Settings.tsx**
   - App configuration
   - User preferences
   - Theme settings (future)

## Component Usage Examples

### Using the Button
```tsx
<Button variant="primary" size="md" loading={isLoading}>
  Save Changes
</Button>
```

### Using Cards
```tsx
<Card interactive>
  <CardHeader>
    <CardTitle>Device Info</CardTitle>
  </CardHeader>
  <CardContent>
    <p>Content here...</p>
  </CardContent>
</Card>
```

### Adding Toasts
```tsx
const { addToast } = useStore();

addToast({
  title: 'Success!',
  description: 'Operation completed',
  type: 'success'
});
```

### Using the Store
```tsx
const { devices, fetchDevices, loading } = useStore();

useEffect(() => {
  fetchDevices();
}, []);
```

## Styling Approach

All components use:
- TailwindCSS for utility classes
- Custom CSS in index.css for theme
- Framer Motion for animations
- cn() utility for class merging

## Key Features

### Animations
- Framer Motion for smooth transitions
- Stagger animations on lists
- Hover/tap interactions
- Page transitions
- Loading states

### Accessibility
- ARIA labels on interactive elements
- Keyboard navigation
- Focus indicators
- Semantic HTML
- Screen reader support

### Responsive Design
- Mobile-first approach
- Breakpoint system (sm, md, lg, xl)
- Flexible grid layouts
- Adaptive typography

### Type Safety
- Full TypeScript coverage
- Strict type checking
- Interface definitions
- Type inference

## API Integration

All components integrate with backend via:
- `useStore` hooks for data
- Automatic error handling
- Toast notifications
- Loading states
- Optimistic updates

## Next Steps for Development

1. Implement drag-and-drop for device placement
2. Add real-time WebSocket updates
3. Enhance thermal analytics with charts
4. Build connection path visualization
5. Add user authentication
6. Implement export/import features
