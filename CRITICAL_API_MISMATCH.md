# CRITICAL: API Mismatch - Device Positioning

**Date:** 2026-01-11
**Status:** 🔴 BLOCKING ISSUE
**Impact:** Device management UI deployed but non-functional

---

## Issue Summary

The frontend device management UI has been successfully implemented and deployed, but **it cannot function** due to a fundamental API design mismatch between frontend and backend.

### Frontend Expectation

The frontend calls:
```
POST /api/devices/{device_id}/move
Body: {"rack_id": number, "start_unit": number}
```

To remove a device from rack:
```
POST /api/devices/{device_id}/move
Body: {"rack_id": null, "start_unit": null}
```

### Backend Reality

The backend uses a **completely different API structure**:

**To add device to rack:**
```
POST /api/racks/{rack_id}/positions
Body: {"device_id": number, "start_u": number, "is_locked": boolean}
```

**To remove device from rack:**
```
DELETE /api/racks/{rack_id}/positions/{position_id}
```

---

## Root Cause

The backend uses a `RackPosition` model to track device placement:
- Each placement is a separate `RackPosition` record
- Devices can exist without being placed in any rack
- Placement is managed through rack positions, not device properties

This is actually a **better design** than the frontend assumed, but requires frontend refactoring.

---

## Impact Assessment

### ✅ Working Features
1. **Devices Page**
   - List devices ✅
   - Add new device ✅
   - Edit device ✅
   - Delete device ✅

2. **Racks Page**
   - List racks ✅
   - Add rack ✅
   - Edit rack ✅
   - Delete rack ✅
   - View rack visualizer ✅

3. **Other Pages**
   - Connections page ✅
   - Thermal analysis page ✅
   - Debug panel ✅

### ❌ Non-Working Features

1. **Device Assignment** (on Racks page)
   - "Add Device" button opens dialog ✅
   - Dialog UI renders correctly ✅
   - Submit calls wrong API endpoint ❌
   - **Result:** 404 error when trying to assign device

2. **Device Movement**
   - Click device → actions menu opens ✅
   - "Move Device" option available ✅
   - Submit calls wrong API endpoint ❌
   - **Result:** 404 error when trying to move device

3. **Device Removal**
   - Click device → "Remove from Rack" ✅
   - Confirmation dialog shows ✅
   - Submit calls wrong API endpoint ❌
   - **Result:** 404 error when trying to remove device

---

## Solution Options

### Option 1: Update Frontend (Recommended)

**Effort:** Medium (2-3 hours)
**Risk:** Low
**Benefits:** Aligns with better backend design

**Required Changes:**

1. **Update `api.ts`:**
```typescript
// Remove moveDevice method
// Add new methods:
async addDeviceToRack(rackId: number, deviceId: number, startU: number): Promise<RackPosition> {
  const response = await this.client.post(`/racks/${rackId}/positions`, {
    device_id: deviceId,
    start_u: startU,
    is_locked: false
  });
  return response.data;
}

async removeDeviceFromRack(rackId: number, positionId: number): Promise<void> {
  await this.client.delete(`/racks/${rackId}/positions/${positionId}`);
}

async getRackPositions(rackId: number): Promise<RackPosition[]> {
  const response = await this.client.get(`/racks/${rackId}/layout`);
  return response.data.positions;
}
```

2. **Update DeviceAssignDialog.tsx:**
   - Change API call from `moveDevice()` to `addDeviceToRack()`
   - Use `rack_id`, `device_id`, `start_u` parameters

3. **Update DeviceActionsMenu.tsx:**
   - For move: Delete old position, create new position
   - For remove: Call `removeDeviceFromRack()` with position ID
   - Need to track `position_id` in device data

4. **Update data transformer:**
   - Backend returns devices without `rack_id`/`start_unit` directly
   - Need to fetch `/racks/{id}/layout` to get positions
   - Transform positions into device placement data

### Option 2: Update Backend

**Effort:** Low (1 hour)
**Risk:** Medium (breaks existing API contract)
**Benefits:** Simpler frontend

**Required Changes:**

Add new endpoint to backend `/api/devices/{id}/move`:
```python
@router.post("/{device_id}/move", response_model=DeviceResponse)
async def move_device(
    device_id: int,
    move_data: DeviceMoveRequest,
    db: Session = Depends(get_db)
):
    # If rack_id is null, remove all positions for this device
    # If rack_id is set, create/update position
    pass
```

This is **not recommended** because:
- Backend's `RackPosition` model is better design
- Allows devices to be in multiple racks (future feature)
- Tracks position metadata (is_locked, etc.)
- More flexible for future enhancements

---

## Recommended Action Plan

### Immediate (Today)

1. ✅ Deploy current UI (already done - shows the issue)
2. ✅ Document this issue (this file)
3. ⬜ Create GitHub issue to track the fix
4. ⬜ Update user documentation to note limitation

### Short Term (Next Session)

1. ⬜ Implement Option 1 (Update Frontend)
2. ⬜ Add proper TypeScript types for RackPosition
3. ⬜ Update store to fetch rack layout data
4. ⬜ Test device assignment workflow end-to-end
5. ⬜ Redeploy with working device management

### Long Term

1. ⬜ Add position_id to DeviceCard for easier removal
2. ⬜ Implement drag-and-drop device movement
3. ⬜ Add position locking feature UI
4. ⬜ Show position conflicts visually in rack visualizer

---

## Workaround (Until Fixed)

Users can manually manage device positions via API:

**Add device to rack:**
```bash
curl -X POST http://lampadas.local/api/racks/1/positions \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 1,
    "start_u": 5,
    "is_locked": false
  }'
```

**Get rack layout (to find position_id):**
```bash
curl http://lampadas.local/api/racks/1/layout | jq '.positions'
```

**Remove device from rack:**
```bash
curl -X DELETE http://lampadas.local/api/racks/1/positions/{position_id}
```

---

## Testing Commands

After fix is implemented, test:

```bash
# 1. Add device 1 to rack 1 at unit 10
curl -X POST http://lampadas.local/api/racks/1/positions \
  -H "Content-Type: application/json" \
  -d '{"device_id": 1, "start_u": 10, "is_locked": false}'

# 2. Verify it appears in layout
curl http://lampadas.local/api/racks/1/layout | jq '.positions'

# 3. Remove it (use position_id from step 2)
curl -X DELETE http://lampadas.local/api/racks/1/positions/1

# 4. Verify removed
curl http://lampadas.local/api/racks/1/layout | jq '.positions'
```

---

## Files Affected

**Need Updates:**
- `frontend/src/lib/api.ts` - API methods
- `frontend/src/store/useStore.ts` - Store actions
- `frontend/src/components/rack/DeviceAssignDialog.tsx` - Assignment logic
- `frontend/src/components/rack/DeviceActionsMenu.tsx` - Move/remove logic
- `frontend/src/types/index.ts` - Add RackPosition type

**Already Correct:**
- `frontend/src/pages/Devices.tsx` - Device CRUD
- `frontend/src/pages/Racks.tsx` - Rack CRUD
- All other pages

---

## Conclusion

**Current Status:** UI is beautiful and functional, but calls wrong API endpoints.

**Next Step:** Implement Option 1 to align frontend with backend's superior API design.

**ETA:** 2-3 hours of focused development to make device positioning fully functional.

**Priority:** HIGH - This is the main value proposition of the rack management feature.

---

**Report By:** Claude Code
**Last Updated:** 2026-01-11 10:45 UTC
