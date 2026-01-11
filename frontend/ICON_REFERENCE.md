# HomeRack Icon Reference Guide

## Device Type Icons

This guide shows all device type icons and their associated colors used throughout the HomeRack UI.

### Computing Devices

| Device Type | Icon | Color | Description |
|-------------|------|-------|-------------|
| `server` | Server | Blue (#3B82F6) | Standard rack-mounted server |
| `console_server` | Cpu | Violet (#8B5CF6) | Console/terminal server |
| `kvm_switch` | MonitorDot | Indigo (#6366F1) | KVM switch for remote access |

### Network Equipment

| Device Type | Icon | Color | Description |
|-------------|------|-------|-------------|
| `switch` | Network | Purple (#A855F7) | Network switch |
| `router` | Router | Cyan (#06B6D4) | Network router |
| `patch_panel` | Cable | Slate (#64748B) | Cable patch panel |
| `wifi` | Wifi | Cyan (#22D3EE) | Wireless access point |

### Security

| Device Type | Icon | Color | Description |
|-------------|------|-------|-------------|
| `firewall` | Shield | Red (#EF4444) | Security firewall |

### Storage

| Device Type | Icon | Color | Description |
|-------------|------|-------|-------------|
| `storage` | Database | Green (#22C55E) | General storage device |
| `nas` | HardDrive | Emerald (#10B981) | Network Attached Storage |
| `san` | Archive | Teal (#14B8A6) | Storage Area Network |
| `backup_device` | Archive | Orange (#F97316) | Backup/archive device |

### Power & Environment

| Device Type | Icon | Color | Description |
|-------------|------|-------|-------------|
| `pdu` | Plug | Amber (#F59E0B) | Power Distribution Unit |
| `ups` | Zap | Yellow (#EAB308) | Uninterruptible Power Supply |
| `fan` | Fan | Sky (#0EA5E9) | Cooling fan unit |
| `sensor` | Activity | Pink (#EC4899) | Environmental sensor |

### Infrastructure

| Device Type | Icon | Color | Description |
|-------------|------|-------|-------------|
| `cable_management` | Cable | Gray (#6B7280) | Cable management system |
| `rack_drawer` | Boxes | Zinc (#71717A) | Rack drawer/shelf |
| `rail_kit` | Wrench | Stone (#78716C) | Rail mounting kit |
| `other` | Boxes | Muted | Miscellaneous equipment |

## Status Icons

| Status | Icon | Color | Usage |
|--------|------|-------|-------|
| `active` | Activity / CheckCircle | Lime (#84CC16) | Device operational |
| `inactive` | Circle | Gray | Device offline |
| `maintenance` | AlertTriangle | Amber (#F59E0B) | Under maintenance |
| `error` | AlertCircle | Red (#EF4444) | Error state |
| `success` | CheckCircle | Lime (#84CC16) | Operation successful |
| `warning` | AlertTriangle | Amber | Warning state |
| `info` | Info | Blue (#3B82F6) | Informational |

## Action Icons

| Action | Icon | Usage |
|--------|------|-------|
| Add/Create | Plus | Add new device, rack, connection |
| Edit | Pencil | Edit existing item |
| Delete | Trash2 | Delete item |
| Search | Search | Search/filter functionality |
| Clear/Close | X | Clear filters, close dialogs |
| Sort | ArrowUpDown | Sort controls |
| Filter | SlidersHorizontal | Filter controls |

## Navigation & Structure Icons

| Purpose | Icon | Usage |
|---------|------|-------|
| Racks | Warehouse | Rack management page |
| Devices | Server | Device library page |
| Location | MapPin | Physical location indicator |
| Collection | Boxes | Multiple items, groups |

## Metric & Data Icons

| Metric | Icon | Color | Usage |
|--------|------|-------|-------|
| Power | Zap | Amber | Power consumption/capacity |
| Temperature | Thermometer | Red scale | Temperature readings |
| Network | Globe | Cyan | IP address, connectivity |
| Height/Size | Ruler | Gray | Rack units, dimensions |
| Weight | Weight | Gray | Physical weight |
| Utilization | PieChart | Cyan | Percentage usage |
| Statistics | BarChart3 | Amber | Counts, metrics |

## View Mode Icons

| Mode | Icon | Description |
|------|------|-------------|
| Grid View | Grid3x3 | Card grid layout |
| List View | List | List layout |

## Icon Sizing Standards

### Size Classes
- **Extra Large (32px+)**: Page headers, empty states
- **Large (24px)**: Component headers, primary actions
- **Medium (20px)**: Secondary actions, stat cards
- **Small (16px)**: Inline labels, compact displays
- **Extra Small (12-14px)**: Dense information, badges

### Usage Guidelines

#### Page Level Icons (32px)
```tsx
<Warehouse className="h-8 w-8 text-electric" />
```
Use for: Page headers, empty state illustrations

#### Card Header Icons (20-24px)
```tsx
<Server className="h-6 w-6 text-blue-500" />
```
Use for: Card titles, section headers, device type badges

#### Action Button Icons (16-20px)
```tsx
<Plus className="h-5 w-5" />
```
Use for: Buttons, interactive elements

#### Inline Label Icons (14-16px)
```tsx
<Zap className="h-4 w-4 text-amber" />
```
Use for: Metrics, labels, inline information

#### Status Indicators (12px)
```tsx
<Activity className="h-3 w-3 text-lime" />
```
Use for: Status badges, compact displays

## Color Usage Guidelines

### Electric Blue (Primary)
- RGB: `rgb(0, 217, 255)`
- Hex: `#00D9FF`
- Tailwind: `text-electric`, `bg-electric`
- Use for: Selected states, primary actions, emphasis

### Status Colors
- **Success/Active**: Lime `#84CC16`
- **Warning**: Amber `#F59E0B`
- **Error**: Red `#EF4444`
- **Info**: Blue `#3B82F6`

### Device Type Colors
Each device type has a unique color to enable quick visual identification. Use the helper functions from `device-icons.tsx`:

```tsx
import { getDeviceColor, getDeviceBorderColor, getDeviceIcon } from '@/lib/device-icons';

const DeviceIcon = getDeviceIcon(device.device_type);
const color = getDeviceColor(device.device_type);
const borderColor = getDeviceBorderColor(device.device_type);
```

## Icon Accessibility

### Best Practices

1. **Always provide context**
   - Use icon + text for important actions
   - Provide tooltips for icon-only buttons
   - Use ARIA labels when appropriate

2. **Ensure adequate contrast**
   - All colored icons meet WCAG AA standards
   - Use muted colors for secondary information
   - Increase contrast for critical information

3. **Consistent meaning**
   - Same icon = same action throughout app
   - Same color = same meaning throughout app
   - Don't reuse icons for different purposes

4. **Interactive feedback**
   - Hover states on all interactive icons
   - Clear visual feedback for actions
   - Animated states for loading/processing

## Helper Functions

### Device Icons
```typescript
// Get icon component
const Icon = getDeviceIcon('server'); // Returns Server icon

// Get color class
const color = getDeviceColor('server'); // Returns 'text-blue-500'

// Get background color
const bgColor = getDeviceBgColor('server'); // Returns 'bg-blue-500/10'

// Get border color
const borderColor = getDeviceBorderColor('server'); // Returns 'border-blue-500/50'

// Format device type for display
const label = formatDeviceType('kvm_switch'); // Returns 'Kvm Switch'
```

### Usage Example
```tsx
import { getDeviceIcon, getDeviceColor } from '@/lib/device-icons';

function DeviceItem({ device }) {
  const Icon = getDeviceIcon(device.device_type);
  const color = getDeviceColor(device.device_type);

  return (
    <div className="flex items-center gap-2">
      <Icon className={`h-5 w-5 ${color}`} />
      <span>{device.name}</span>
    </div>
  );
}
```

## Quick Reference: Common Patterns

### Device Card Header
```tsx
<div className="flex items-center gap-3">
  <div className="p-3 rounded-lg glass border border-blue-500/50">
    <Server className="h-8 w-8 text-blue-500" />
  </div>
  <div>
    <h3 className="text-lg font-bold">Device Name</h3>
    <p className="text-sm text-muted-foreground">Dell PowerEdge</p>
  </div>
</div>
```

### Metric Display
```tsx
<div className="flex items-center gap-2">
  <Zap className="h-4 w-4 text-amber" />
  <span className="text-sm text-amber font-mono">450W</span>
</div>
```

### Action Button with Tooltip
```tsx
<IconButton
  icon={Pencil}
  variant="outline"
  size="md"
  tooltip="Edit Device"
  onClick={handleEdit}
/>
```

### Status Badge
```tsx
<StatusBadge
  status="active"
  label="Active"
  pulse={true}
  size="md"
/>
```

## Notes

- All icons are from the Lucide React library
- Icons are tree-shakeable (only imported icons are bundled)
- Icons use currentColor by default (inherit text color)
- Sizes use Tailwind classes for consistency
- All colors use CSS custom properties for theme support
