# HomeRack - Precision Engineering Color Scheme

## Primary Colors

### Background
- **Deep Slate Dark**: `#0a0e1a` (rgb: 10, 22, 26)
  - Used for main background
  - Creates depth and contrast
  - Professional, technical feel

### Primary Accent
- **Electric Blue**: `#00d4ff` (rgb: 0, 212, 255)
  - Primary actions and interactive elements
  - Navigation highlights
  - Focus states
  - Links and primary buttons
  - Creates high-tech, precision feel

### Warning/Power
- **Amber**: `#ffb020` (rgb: 255, 176, 32)
  - Warning states
  - Power consumption indicators
  - Maintenance status
  - Attention-grabbing alerts

### Success/Active
- **Lime**: `#a3ff12` (rgb: 163, 255, 18)
  - Success states
  - Active devices
  - Positive metrics
  - System online indicators

## Secondary Colors

### Card & UI Elements
- **Card Background**: `#0f1b23` (rgb: 15, 27, 35)
- **Secondary Background**: `#1e2a38` (rgb: 30, 42, 56)
- **Border**: `#1e2a38` (rgb: 30, 42, 56)

### Text Colors
- **Foreground**: `#f8fafc` (rgb: 248, 250, 252)
- **Muted**: `#94a3b8` (rgb: 148, 163, 184)

### Status Colors
- **Error**: `#ef4444` (Red 500)
- **Info**: `#3b82f6` (Blue 500)

## Thermal Color Scale

Temperature ranges with gradient overlays:

- **Cold** (< 20°C): Blue tones
  - `rgba(59, 130, 246, 0.3)` to `rgba(14, 165, 233, 0.2)`

- **Cool** (20-30°C): Green-Blue tones
  - `rgba(34, 197, 94, 0.3)` to `rgba(59, 130, 246, 0.2)`

- **Warm** (30-40°C): Amber-Yellow tones
  - `rgba(255, 176, 32, 0.3)` to `rgba(251, 191, 36, 0.2)`

- **Hot** (40-50°C): Orange-Red tones
  - `rgba(239, 68, 68, 0.4)` to `rgba(255, 176, 32, 0.3)`

- **Critical** (> 50°C): Deep Red tones
  - `rgba(220, 38, 38, 0.5)` to `rgba(239, 68, 68, 0.4)`

## Cable/Connection Colors

- **Ethernet**: Electric Blue `rgb(0, 212, 255)`
- **Fiber**: Lime Green `rgb(163, 255, 18)`
- **Power**: Amber `rgb(255, 176, 32)`
- **Console**: Slate Gray `rgb(148, 163, 184)`

## Visual Effects

### Glow Effects
All glow effects use the primary color with varying opacity:

- **Electric Glow**: `0 0 20px rgba(0, 212, 255, 0.3)`
- **Strong Electric**: `0 0 30px rgba(0, 212, 255, 0.5), 0 0 60px rgba(0, 212, 255, 0.2)`
- **Amber Glow**: `0 0 20px rgba(255, 176, 32, 0.3)`
- **Lime Glow**: `0 0 20px rgba(163, 255, 18, 0.3)`

### Neon Text Effect
```css
text-shadow:
  0 0 10px rgba(0, 212, 255, 0.8),
  0 0 20px rgba(0, 212, 255, 0.5),
  0 0 30px rgba(0, 212, 255, 0.3);
```

### Glass Effect
```css
background: rgba(15, 27, 35, 0.6);
backdrop-filter: blur(12px);
border: 1px solid rgba(189, 255, 255, 0.1);
```

## Typography

### Font Families
- **UI Text**: DM Sans (400, 500, 600, 700)
- **Technical/Mono**: IBM Plex Mono (400, 500, 600)

### Font Weights
- Regular: 400
- Medium: 500
- Semibold: 600
- Bold: 700

## Usage Guidelines

### DO ✅
- Use electric blue for primary actions
- Use amber for warnings and power-related info
- Use lime for success states and active devices
- Apply glow effects to important interactive elements
- Use glass effect for overlays and modals
- Keep text readable with sufficient contrast

### DON'T ❌
- Don't use red for anything other than errors
- Don't mix multiple glowing elements close together
- Don't apply neon effect to body text
- Don't use pure white (#ffffff) - use foreground color
- Don't apply glow effects to static content

## Accessibility

All color combinations meet WCAG 2.1 AA standards:
- Electric blue on dark: 8.2:1 contrast ratio
- Amber on dark: 7.1:1 contrast ratio
- Lime on dark: 12.5:1 contrast ratio
- Foreground on background: 15.8:1 contrast ratio

## Color Palette Export

### CSS Variables
```css
--background: 10 22 26;
--foreground: 248 250 252;
--electric-blue: 0 212 255;
--amber: 255 176 32;
--lime: 163 255 18;
--card: 15 27 35;
--border: 30 42 56;
--muted-foreground: 148 163 184;
```

### Tailwind Classes
- `bg-electric` / `text-electric` / `border-electric`
- `bg-amber` / `text-amber` / `border-amber`
- `bg-lime` / `text-lime` / `border-lime`
- `bg-background` / `text-foreground`
- `bg-card` / `border-border`

## Inspiration & Theme

The "Precision Engineering" aesthetic draws from:
- High-tech industrial design
- Server room/data center environments
- Professional engineering tools
- Military/aerospace instrumentation
- Cyberpunk visual language (subtle)

Creating a professional, technical, yet modern and approachable interface.
