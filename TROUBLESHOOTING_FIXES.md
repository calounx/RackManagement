# HomeRack Troubleshooting & Fixes Report

## Issues Found and Fixed

### 1. ✅ CRITICAL: Data Model Mismatch (Blank Devices Page)

**Problem:** The devices page appeared blank because the frontend and backend used different data models.

**Root Cause:**
- Backend returns: `{ custom_name: "...", specification: { brand: "...", model: "..." } }`
- Frontend expected: `{ name: "...", manufacturer: "...", model: "..." }`

**Solution:** Added data transformation layer in `frontend/src/lib/api.ts`:
- `transformDevice()` - Converts backend device format to frontend format
- `transformRack()` - Converts backend rack format to frontend format
- `inferDeviceType()` - Determines device type from brand/model
- `inferDeviceStatus()` - Provides default device status

**Files Modified:**
- `frontend/src/lib/api.ts` - Added transformer methods

### 2. ✅ Rack Management Functionality

**Problem:** No way to add/edit/delete racks - buttons had no onClick handlers.

**Solution:** Created full CRUD functionality for racks:
- Created `RackDialog` component for add/edit operations
- Added delete confirmation dialog
- Added edit/delete buttons on hover for each rack
- Connected all buttons to proper handlers

**Files Modified:**
- `frontend/src/components/rack/RackDialog.tsx` - NEW FILE
- `frontend/src/pages/Racks.tsx` - Added dialog integration and handlers

### 3. ⚠️ Debug Panel Status

**Status:** Debug panel is fully implemented and working.

**How to Use:**
1. Go to Settings page (`/settings`)
2. Toggle "Enable Debug Mode" switch
3. Press `Ctrl+D` to open/close debug console
4. OR click the Terminal button in Settings to open console
5. Make API requests - they will be logged automatically
6. Export logs as JSON if needed

**Files Involved:**
- `frontend/src/components/debug/DebugPanel.tsx` - Debug console UI
- `frontend/src/lib/debug-store.ts` - Debug state management
- `frontend/src/lib/api.ts` - API logging integration
- `frontend/src/pages/Settings.tsx` - Debug settings UI

### 4. ❌ Thermal Analysis Page

**Status:** Currently a placeholder showing "coming soon".

**Next Steps:** This page needs backend thermal analysis API implementation. The endpoint exists (`/racks/{id}/thermal`) but needs real thermal calculation logic.

### 5. ✅ Connections Page

**Status:** Fully implemented and functional.

## Device & Rack Management Workflow

### How to Add a Rack

1. Navigate to **Racks** page (`/racks`)
2. Click **"Add Rack"** button (top right)
3. Fill in the form:
   - **Rack Name*** (required)
   - **Location*** (required)
   - **Rack Units** (default: 42)
   - **Max Power (W)** (default: 5000)
   - **Max Weight (kg)** (default: 500)
4. Click **"Create Rack"**

### How to Edit a Rack

1. Go to **Racks** page
2. Hover over a rack in the left sidebar
3. Click the **pencil icon** (edit button)
4. Modify the form fields
5. Click **"Save Changes"**

### How to Delete a Rack

1. Go to **Racks** page
2. Hover over a rack in the left sidebar
3. Click the **trash icon** (delete button)
4. Confirm deletion in the dialog
5. **Note:** This will remove all devices in that rack!

### How to Add a Device to a Rack

⚠️ **CURRENT LIMITATION:** The frontend does not yet have a "Create Device" dialog implemented.

**Current Backend Workflow:**
1. First create a Device Specification (brand/model specs)
2. Then create a Device instance referencing that specification
3. Use the backend API directly:

```bash
# Create device specification
curl -X POST http://lampadas.local/api/device-specs/ \
  -H "Content-Type: application/json" \
  -d '{
    "brand": "Cisco",
    "model": "Catalyst 2960",
    "height_u": 1,
    "power_watts": 25
  }'

# Create device
curl -X POST http://lampadas.local/api/devices/ \
  -H "Content-Type: application/json" \
  -d '{
    "specification_id": 1,
    "custom_name": "My Switch"
  }'
```

**TODO:** Create `DeviceDialog` component similar to `RackDialog`.

### How to Remove/Delete a Device from a Rack

⚠️ **CURRENT LIMITATION:** No device delete UI implemented yet.

**Via API:**
```bash
curl -X DELETE http://lampadas.local/api/devices/{device_id}
```

**TODO:** Add delete button to DeviceCard component.

### How to Move a Device Between Racks

**Current Implementation:** The `RackVisualizer` component likely supports drag-and-drop for moving devices, but this needs to be verified.

**Via API:**
```bash
curl -X POST http://lampadas.local/api/devices/{device_id}/move \
  -H "Content-Type: application/json" \
  -d '{
    "rack_id": 2,
    "start_unit": 10
  }'
```

## Backend API Structure

### Device Model
```json
{
  "id": 1,
  "custom_name": "Core Switch 1",
  "specification_id": 1,
  "access_frequency": "medium",
  "notes": null,
  "specification": {
    "id": 1,
    "brand": "Cisco",
    "model": "Catalyst 2960-48TT-L",
    "height_u": 1.0,
    "power_watts": 25.0,
    "heat_output_btu": 85.0,
    "airflow_pattern": "front_to_back",
    "max_operating_temp_c": 45.0,
    "typical_ports": {
      "gigabit_ethernet": 48,
      "sfp": 2
    }
  }
}
```

### Rack Model
```json
{
  "id": 1,
  "name": "Main Rack",
  "location": "Server Room A",
  "total_height_u": 42,
  "width_inches": "19\"",
  "depth_mm": 700.0,
  "max_weight_kg": 500.0,
  "max_power_watts": 5000.0,
  "cooling_type": "front-to-back",
  "cooling_capacity_btu": 17000.0,
  "ambient_temp_c": 22.0,
  "max_inlet_temp_c": 27.0
}
```

## Deployment Instructions

### Build Frontend

```bash
cd /home/calounx/repositories/homerack/frontend
npm run build
```

### Deploy to lampadas.local

Use the existing deployment script:

```bash
cd /home/calounx/repositories/homerack
./deploy-auto.sh
```

OR manually:

```bash
# Build frontend locally
cd frontend
npm run build

# Copy to lampadas
rsync -avz --delete dist/ calounx@lampadas.local:/home/calounx/homerack/frontend/dist/

# Restart nginx on lampadas
ssh calounx@lampadas.local 'sudo systemctl restart nginx'
```

## Testing Checklist

After deployment, test:

- [ ] Devices page shows device cards (not blank)
- [ ] Can add a new rack via dialog
- [ ] Can edit a rack
- [ ] Can delete a rack
- [ ] Debug panel opens with Ctrl+D
- [ ] Debug panel logs API requests when enabled
- [ ] Settings page shows correct debug status
- [ ] Connections page displays connections
- [ ] Thermal Analysis page shows placeholder message

## Known Limitations & TODOs

1. **No Device Create/Edit UI** - Devices can only be managed via API
2. **No Device Delete Button** - Must use API to delete devices
3. **Thermal Analysis** - Placeholder only, needs implementation
4. **No drag-and-drop verification** - Device movement UI needs testing
5. **Backend does not store device status** - Frontend defaults all to "active"
6. **Backend does not track temperature** - Frontend defaults to 25°C

## API Endpoint Reference

All endpoints use `/api/` prefix:

### Racks
- `GET /api/racks/` - List all racks
- `GET /api/racks/{id}` - Get rack details
- `POST /api/racks/` - Create rack
- `PUT /api/racks/{id}` - Update rack
- `DELETE /api/racks/{id}` - Delete rack

### Devices
- `GET /api/devices/` - List all devices
- `GET /api/devices/{id}` - Get device details
- `POST /api/devices/` - Create device
- `PUT /api/devices/{id}` - Update device
- `DELETE /api/devices/{id}` - Delete device
- `POST /api/devices/{id}/move` - Move device to rack

### Device Specifications
- `GET /api/device-specs/` - List specifications
- `POST /api/device-specs/` - Create specification
- `PUT /api/device-specs/{id}` - Update specification
- `DELETE /api/device-specs/{id}` - Delete specification

### Connections
- `GET /api/connections/` - List connections
- `POST /api/connections/` - Create connection
- `PUT /api/connections/{id}` - Update connection
- `DELETE /api/connections/{id}` - Delete connection

### Health & Docs
- `GET /api/health` - Backend health check
- `GET /api/docs` - OpenAPI documentation UI
