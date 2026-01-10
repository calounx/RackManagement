# HomeRack Frontend - Precision Engineering UI

A beautiful, production-ready frontend application for the HomeRack data center management system, featuring a distinctive "Precision Engineering" aesthetic with electric blue accents, smooth animations, and comprehensive rack visualization.

## Features

### Design System
- **Deep Slate Dark Theme** (#0a0e1a background)
- **Electric Blue Accents** (#00d4ff) for primary actions
- **Amber** (#ffb020) for warnings
- **Lime** (#a3ff12) for success states
- **IBM Plex Mono** for technical content
- **DM Sans** for UI elements
- Subtle dot grid background pattern
- Glowing indicators and smooth Framer Motion animations

### Core Features
- **Dashboard**: System overview with real-time metrics
- **Rack Management**: Visual 42U rack representation with drag-and-drop
- **Device Library**: Complete hardware inventory management
- **Cable Management**: Network and power connection tracking
- **Thermal Analysis**: Real-time temperature monitoring with heat maps
- **Settings**: Application configuration

### Components

#### UI Components
- `Button` - Styled buttons with variants (primary, secondary, outline, ghost, danger)
- `Card` - Container component with header, content, and footer
- `Badge` - Status indicators with glow effects
- `Input` - Form inputs with labels and error states
- `Dialog` - Modal dialogs with animations
- `Toast` - Non-intrusive notifications

#### Layout Components
- `Sidebar` - Main navigation with active state indicators
- `Header` - Top bar with search and user menu

#### Rack Components
- `RackVisualizer` - Complete 42U rack visualization
- `DeviceSlot` - Individual device representation in rack
- `ThermalOverlay` - Heat map overlay for temperature analysis

#### Feature Components
- `DeviceCard` - Device library card display
- `SpecFetcher` - Auto-fetch device specifications
- `CableValidator` - Connection validation UI
- `StatsCard` - Dashboard metric cards
- `SystemHealth` - Health monitoring widget

## Technology Stack

- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS 4** - Styling
- **Framer Motion** - Animations
- **Zustand** - State management
- **React Router** - Routing
- **Axios** - API client

## Project Structure

```
src/
├── components/
│   ├── ui/              # Base UI components
│   ├── layout/          # Layout components
│   ├── rack/            # Rack visualization
│   ├── devices/         # Device management
│   ├── connections/     # Cable management
│   └── dashboard/       # Dashboard widgets
├── pages/               # Route pages
├── lib/                 # Utilities and API client
├── store/               # Zustand state management
├── types/               # TypeScript definitions
├── App.tsx              # Main app component
├── main.tsx             # Entry point
└── index.css            # Global styles
```

## Getting Started

### Prerequisites
- Node.js 18+
- Backend API running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
```

## Key Features Walkthrough

### Rack Visualization
The `RackVisualizer` component provides:
- Visual representation of 42U rack units
- Drag-and-drop device placement
- Real-time power and thermal monitoring
- Device status indicators with glow effects
- Thermal overlay toggle

### State Management
Using Zustand for global state:
- Racks, devices, device specs, connections
- UI state (selected items, filters, view options)
- Async actions with error handling
- Toast notifications
- Persisted user preferences

### API Integration
All backend endpoints integrated via `lib/api.ts`:
- RESTful CRUD operations
- Thermal data fetching
- Connection validation
- Device spec auto-fetching
- Error handling with user-friendly messages

## Styling Guidelines

### Color Usage
- Primary actions: Electric blue (`text-electric`, `bg-electric`)
- Success states: Lime green (`text-lime`, `bg-lime`)
- Warnings: Amber (`text-amber`, `bg-amber`)
- Errors: Red (`text-red-500`)
- Muted content: Slate (`text-muted-foreground`)

### Custom CSS Classes
- `.dot-grid` - Background grid pattern
- `.glass` - Glassmorphism effect
- `.glow-electric` - Electric blue glow
- `.neon-text` - Neon text effect
- `.animate-pulse-glow` - Pulsing glow animation
- `.thermal-{status}` - Thermal color gradients

## Responsive Design

All components are fully responsive:
- Mobile: Single column layouts
- Tablet: 2-column grids
- Desktop: Full multi-column layouts
- Rack visualizer scales appropriately

## Accessibility

- Proper ARIA labels
- Keyboard navigation support
- Focus states with visible rings
- Semantic HTML structure
- Screen reader friendly

## Performance

- Code splitting by route
- Lazy loading of components
- Optimized animations with Framer Motion
- Efficient re-renders with Zustand
- Image optimization
- CSS purging in production

## Future Enhancements

- [ ] Advanced thermal analytics with charts
- [ ] Real-time WebSocket updates
- [ ] Drag-and-drop device placement
- [ ] Export/import configurations
- [ ] Advanced cable path visualization
- [ ] Multi-rack views
- [ ] User authentication
- [ ] Role-based access control
- [ ] Audit logging
- [ ] Dark/light theme toggle

## License

Part of the HomeRack project.
