# Phase 2 Data Migration Guide

## Table of Contents
1. [Overview](#overview)
2. [Why Migration is Needed](#why-migration-is-needed)
3. [What Data is Being Migrated](#what-data-is-being-migrated)
4. [Pre-Migration Checklist](#pre-migration-checklist)
5. [How to Run the Migration](#how-to-run-the-migration)
6. [Verifying Success](#verifying-success)
7. [Rollback Procedure](#rollback-procedure)
8. [Troubleshooting](#troubleshooting)
9. [Technical Details](#technical-details)

---

## Overview

This guide covers the Phase 2 data migration from the legacy `device_specifications` table to the new normalized `brands` and `models` catalog structure. This migration is essential for improving data consistency, reducing duplication, and enabling advanced features like brand management and device type categorization.

**Migration Script Location:** `/home/calounx/repositories/homerack/backend/scripts/migrate_specs_to_catalog.py`

---

## Why Migration is Needed

### Current Problem
The existing `device_specifications` table stores brand names as free-text strings, leading to:
- **Data inconsistency**: Same brand stored with different capitalizations ("Cisco", "cisco", "CISCO")
- **Duplication**: No way to deduplicate brands across specifications
- **Limited metadata**: Cannot store brand-level information (website, support URL, etc.)
- **Poor organization**: Difficult to browse devices by manufacturer
- **No categorization**: Cannot categorize devices by type (Switch, Server, Router, etc.)

### New Structure Benefits
The new normalized structure provides:
- **Unique brand records**: One canonical record per brand with metadata
- **Device type categorization**: Proper classification (Server, Switch, Router, etc.)
- **Better relationships**: Clean foreign key relationships between brands, models, and devices
- **Enhanced metadata**: Support for URLs, logos, lifecycle dates, and more
- **Future-proof**: Enables features like brand-based filtering, model comparisons, and catalog browsing

---

## What Data is Being Migrated

### Source: `device_specifications` Table
All records from the `device_specifications` table will be migrated. Each specification contains:
- Brand name (free text)
- Model name
- Physical specifications (height, width, depth, weight)
- Power and thermal properties
- Port configurations
- Source metadata

### Target: `brands` + `models` Tables

#### 1. `brands` Table
Unique brand records will be created for each distinct brand found in device specifications:
- **name**: Canonical brand name (e.g., "Cisco")
- **slug**: URL-friendly identifier (e.g., "cisco")
- **Metadata fields**: website, support_url, logo_url (populated later)

#### 2. `models` Table
Each device specification becomes a model record with:
- **Foreign keys**: Links to `brand_id` and `device_type_id`
- **Model identification**: name, variant
- **All specification data**: Physical dimensions, power, thermal, ports, mounting
- **Source metadata**: Preserved from original specification

### Data Transformations

```
device_specifications.brand → Brand.name + Brand.slug
device_specifications.model → Model.name
device_specifications.variant → Model.variant
device_specifications.* → Model.* (all other fields)

Device Type inferred from brand + model name:
  - "Cisco Catalyst 9300" → device_type = "Switch"
  - "Dell PowerEdge R740" → device_type = "Server"
  - "Fortinet FortiGate 100F" → device_type = "Firewall"
```

### Migration Tracking
Each `device_specification` record is updated with:
- **migrated_to_model_id**: Links to the new Model record
- **migration_status**: Set to "COMPLETED" after successful migration

---

## Pre-Migration Checklist

### 1. Backup Your Database
**CRITICAL**: Always backup before running migrations!

```bash
# Create backup
cp homerack.db homerack.db.backup-$(date +%Y%m%d-%H%M%S)

# Verify backup
ls -lh homerack.db*
```

### 2. Verify Database State
Check current counts:

```bash
python3 -c "
from app.database import SessionLocal
from app.models import DeviceSpecification, Brand, Model

db = SessionLocal()
print(f'Device Specifications: {db.query(DeviceSpecification).count()}')
print(f'Brands: {db.query(Brand).count()}')
print(f'Models: {db.query(Model).count()}')
db.close()
"
```

### 3. Check for Potential Issues
```bash
# Check for specs with missing brand/model
python3 -c "
from app.database import SessionLocal
from app.models import DeviceSpecification

db = SessionLocal()
invalid = db.query(DeviceSpecification).filter(
    (DeviceSpecification.brand == None) |
    (DeviceSpecification.model == None)
).count()
print(f'Invalid specifications (missing brand/model): {invalid}')
db.close()
"
```

### 4. Ensure Prerequisites
- Python 3.8+
- All dependencies installed (`pip install -r requirements.txt`)
- Database accessible (`homerack.db` exists)
- Write permissions in database directory

---

## How to Run the Migration

### Step 1: Dry Run (RECOMMENDED)
Always start with a dry run to preview changes without committing:

```bash
cd /home/calounx/repositories/homerack/backend
python3 scripts/migrate_specs_to_catalog.py --dry-run --verbose
```

This will:
- Show what brands would be created
- Show what models would be created
- Display device type inference results
- Report potential duplicates
- No database changes made

**Review the output carefully!** Look for:
- Unexpected device type classifications
- Duplicate warnings
- Any error messages

### Step 2: Run Migration
If dry run looks good, run the actual migration:

```bash
python3 scripts/migrate_specs_to_catalog.py --verbose
```

You'll be prompted to confirm:
```
This will modify the database. Continue? (yes/no):
```

Type `yes` to proceed.

### Step 3: Monitor Progress
The script will display:
- Batch processing progress
- Brands created/reused
- Models created
- Any errors encountered

Example output:
```
Found 150 device specifications to migrate

Processing batch 1 (1-100 of 150)
  Created brand: Cisco (ID: 1)
  Migrated: Cisco Catalyst 9300 → Model ID 1 (Device Type: 2)
  Migrated: Cisco Catalyst 3850 → Model ID 2 (Device Type: 2)
  ...
  Committed batch 1

Processing batch 2 (101-150 of 150)
  Reused brand: Cisco (ID: 1)
  Migrated: Cisco Nexus 5500 → Model ID 51 (Device Type: 2)
  ...
  Committed batch 2

Migration completed successfully
```

### Command-Line Options

```bash
# Dry run (preview only)
python3 scripts/migrate_specs_to_catalog.py --dry-run

# Verbose logging
python3 scripts/migrate_specs_to_catalog.py --verbose

# Custom batch size (default: 100)
python3 scripts/migrate_specs_to_catalog.py --batch-size 50

# Skip duplicates instead of failing
python3 scripts/migrate_specs_to_catalog.py --skip-duplicates

# Combine options
python3 scripts/migrate_specs_to_catalog.py --dry-run --verbose --batch-size 25
```

---

## Verifying Success

### 1. Check Migration Summary
The script prints a summary at the end:

```
======================================================================
MIGRATION SUMMARY
======================================================================
Duration: 2.45 seconds

Specifications:
  Total found:     150
  Processed:       150
  Migrated:        145
  Skipped:         5
  Failed:          0

Brands:
  Created:         8
  Reused:          142

Models:
  Created:         145
  Duplicates:      5
======================================================================
```

### 2. Verify Database Counts
```bash
python3 -c "
from app.database import SessionLocal
from app.models import DeviceSpecification, Brand, Model

db = SessionLocal()

specs = db.query(DeviceSpecification).count()
brands = db.query(Brand).count()
models = db.query(Model).count()
migrated = db.query(DeviceSpecification).filter(
    DeviceSpecification.migration_status == 'COMPLETED'
).count()

print(f'Total Specifications: {specs}')
print(f'Migrated Specifications: {migrated}')
print(f'Total Brands: {brands}')
print(f'Total Models: {models}')
print(f'Migration Rate: {migrated/specs*100:.1f}%' if specs > 0 else 'N/A')
db.close()
"
```

### 3. Verify Relationships
Check that models are properly linked:

```bash
python3 -c "
from app.database import SessionLocal
from app.models import Model, Brand, DeviceType

db = SessionLocal()

# Check a sample model
model = db.query(Model).first()
if model:
    print(f'Sample Model: {model.name}')
    print(f'  Brand: {model.brand.name if model.brand else \"None\"}')
    print(f'  Type: {model.device_type.name if model.device_type else \"None\"}')
    print(f'  Height: {model.height_u}U')
else:
    print('No models found')

db.close()
"
```

### 4. Check for Failed Migrations
```bash
python3 -c "
from app.database import SessionLocal
from app.models import DeviceSpecification, MigrationStatus

db = SessionLocal()

failed = db.query(DeviceSpecification).filter(
    DeviceSpecification.migration_status == MigrationStatus.FAILED
).all()

print(f'Failed migrations: {len(failed)}')
for spec in failed:
    print(f'  ID {spec.id}: {spec.brand} {spec.model}')

db.close()
"
```

### 5. Verify Brand Uniqueness
```bash
python3 -c "
from app.database import SessionLocal
from app.models import Brand
from sqlalchemy import func

db = SessionLocal()

# Check for duplicate slugs
duplicates = db.query(Brand.slug, func.count(Brand.slug)).group_by(Brand.slug).having(func.count(Brand.slug) > 1).all()

if duplicates:
    print(f'WARNING: Found {len(duplicates)} duplicate brand slugs:')
    for slug, count in duplicates:
        print(f'  {slug}: {count} occurrences')
else:
    print('✓ All brand slugs are unique')

db.close()
"
```

---

## Rollback Procedure

### Option 1: Restore from Backup (RECOMMENDED)
If migration fails or produces incorrect results:

```bash
# Stop the application if running
# pkill -f uvicorn

# Restore backup
cp homerack.db.backup-YYYYMMDD-HHMMSS homerack.db

# Verify restoration
python3 -c "
from app.database import SessionLocal
from app.models import Brand, Model

db = SessionLocal()
print(f'Brands: {db.query(Brand).count()}')
print(f'Models: {db.query(Model).count()}')
db.close()
"

# Restart application
```

### Option 2: Manual Rollback (If no backup)
If you need to reverse the migration manually:

```bash
python3 -c "
from app.database import SessionLocal
from app.models import DeviceSpecification, Brand, Model, MigrationStatus

db = SessionLocal()

# Clear migration status
db.query(DeviceSpecification).update({
    'migrated_to_model_id': None,
    'migration_status': None
})

# Delete all models
db.query(Model).delete()

# Delete all brands
db.query(Brand).delete()

db.commit()
print('Rollback completed')
db.close()
"
```

**WARNING**: Option 2 should only be used if:
- No other data depends on the brands/models
- You understand the consequences
- You have verified the cleanup script works

---

## Troubleshooting

### Problem: Script fails with "python: command not found"
**Solution**: Use `python3` instead:
```bash
python3 scripts/migrate_specs_to_catalog.py --dry-run
```

### Problem: "ModuleNotFoundError: No module named 'app'"
**Solution**: Ensure you're running from the backend directory:
```bash
cd /home/calounx/repositories/homerack/backend
python3 scripts/migrate_specs_to_catalog.py --dry-run
```

### Problem: Duplicate key errors during migration
**Solution**: Use the `--skip-duplicates` flag:
```bash
python3 scripts/migrate_specs_to_catalog.py --skip-duplicates
```

### Problem: Wrong device types inferred
**Solution**: The device type inference logic can be adjusted in the script. Edit the `infer_device_type()` function to add more keywords or patterns.

Example fix:
```python
# Add more specific patterns
keywords = [
    ('catalyst', 'switch'),  # Cisco Catalyst switches
    ('powerconnect', 'switch'),  # Dell PowerConnect
    ('poweredge', 'server'),  # Dell PowerEdge servers
    # ... existing patterns
]
```

### Problem: Migration runs but no data appears
**Solution**: Check that device_specifications table has data:
```bash
python3 -c "
from app.database import SessionLocal
from app.models import DeviceSpecification

db = SessionLocal()
count = db.query(DeviceSpecification).count()
print(f'Specifications in database: {count}')

if count > 0:
    spec = db.query(DeviceSpecification).first()
    print(f'Sample: {spec.brand} {spec.model}')
db.close()
"
```

### Problem: Transaction deadlock or lock timeout
**Solution**:
1. Close all other database connections
2. Use a smaller batch size:
   ```bash
   python3 scripts/migrate_specs_to_catalog.py --batch-size 25
   ```

### Problem: Some specifications fail to migrate
**Solution**: Check the error summary and logs. Common causes:
- Missing required fields (brand, model)
- Invalid enum values
- Foreign key constraint violations

View failed specs:
```bash
python3 -c "
from app.database import SessionLocal
from app.models import DeviceSpecification, MigrationStatus

db = SessionLocal()
failed = db.query(DeviceSpecification).filter(
    DeviceSpecification.migration_status == MigrationStatus.FAILED
).all()

for spec in failed:
    print(f'ID {spec.id}: {spec.brand} {spec.model}')
    print(f'  Height: {spec.height_u}, Width: {spec.width_type}')
db.close()
"
```

---

## Technical Details

### Device Type Inference Logic

The script uses keyword matching to infer device types:

```python
def infer_device_type(brand: str, model: str) -> int:
    combined = f"{brand} {model}".lower()

    # Keywords checked in order:
    if 'switch' in combined: return SWITCH_TYPE_ID
    if 'router' in combined: return ROUTER_TYPE_ID
    if 'firewall' in combined: return FIREWALL_TYPE_ID
    if 'server' in combined: return SERVER_TYPE_ID
    if 'storage' in combined: return STORAGE_TYPE_ID
    if 'pdu' in combined: return PDU_TYPE_ID
    if 'ups' in combined: return UPS_TYPE_ID
    if 'patch' in combined: return PATCH_PANEL_TYPE_ID

    return OTHER_TYPE_ID  # Default fallback
```

### Brand Slug Generation

Brands are assigned URL-friendly slugs:

```python
def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[\s_]+', '-', text)  # Spaces/underscores → hyphens
    text = re.sub(r'[^a-z0-9-]', '', text)  # Remove special chars
    text = re.sub(r'-+', '-', text)  # Remove duplicate hyphens
    return text.strip('-')

# Examples:
# "Cisco Systems" → "cisco-systems"
# "Dell EMC" → "dell-emc"
# "HPE / HP Enterprise" → "hpe-hp-enterprise"
```

### Duplicate Handling

The script detects duplicates by checking:
```sql
SELECT * FROM models
WHERE brand_id = ?
  AND name = ?
  AND variant = ?
```

With `--skip-duplicates`:
- Existing model is reused
- Specification is linked to existing model
- No error is raised

Without `--skip-duplicates`:
- Migration fails with IntegrityError
- Transaction is rolled back
- Error is logged

### Transaction Safety

- Each batch is a separate transaction
- If a batch fails, it rolls back automatically
- Previous batches remain committed
- Use smaller `--batch-size` for more granular commits

### Migration Status Tracking

DeviceSpecification migration_status values:
- `null` - Not yet migrated
- `PENDING` - Queued for migration
- `IN_PROGRESS` - Currently being migrated
- `COMPLETED` - Successfully migrated
- `FAILED` - Migration failed

---

## Post-Migration Steps

After successful migration:

1. **Update Application Code**: Switch from using `device_specifications` to `models` in API endpoints
2. **Update Frontend**: Update UI to use new catalog structure
3. **Deprecate Old Tables**: Mark `device_specifications` as deprecated (don't delete yet)
4. **Monitor**: Watch for issues in production use
5. **Clean Up**: After validation period, consider archiving old specifications

---

## Support

If you encounter issues not covered in this guide:

1. Check the script's verbose output: `--verbose`
2. Review the error logs in the migration summary
3. Verify database integrity
4. Restore from backup if needed
5. Contact the development team with:
   - Migration summary output
   - Error messages
   - Database statistics (specs, brands, models counts)

---

## Migration Checklist

- [ ] Database backed up
- [ ] Pre-migration checks completed
- [ ] Dry run executed successfully
- [ ] Dry run output reviewed
- [ ] Actual migration executed
- [ ] Migration summary reviewed
- [ ] Database counts verified
- [ ] Sample relationships tested
- [ ] No failed migrations
- [ ] Brand uniqueness verified
- [ ] Application tested with new structure

---

**Last Updated**: 2026-01-11
**Script Version**: 1.0.0
**Compatible with**: Homerack Backend v1.0.1+
