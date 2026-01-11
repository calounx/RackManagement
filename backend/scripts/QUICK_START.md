# Phase 2 Migration - Quick Start Guide

## Prerequisites
```bash
cd /home/calounx/repositories/homerack/backend
```

## 5-Minute Test Run

### Step 1: Create Test Data (10 seconds)
```bash
python3 scripts/test_migration.py setup
```
**Output**: Creates 8 sample device specifications

### Step 2: Preview Migration (5 seconds)
```bash
python3 scripts/migrate_specs_to_catalog.py --dry-run --verbose
```
**Output**: Shows what would be created (no changes)

### Step 3: Check Status Before (2 seconds)
```bash
python3 scripts/check_migration_status.py
```
**Output**: 8 pending specifications, 0 brands, 0 models

### Step 4: Run Migration (10 seconds)
```bash
echo "yes" | python3 scripts/migrate_specs_to_catalog.py --skip-duplicates
```
**Output**: Creates 5 brands, 7 models, migrates 8 specs

### Step 5: Check Status After (2 seconds)
```bash
python3 scripts/check_migration_status.py
```
**Output**: 8 completed, 5 brands, 7 models with statistics

### Step 6: Verify Results (5 seconds)
```bash
python3 scripts/test_migration.py verify
```
**Output**: Detailed verification of migration

### Step 7: Cleanup (2 seconds)
```bash
python3 scripts/test_migration.py cleanup
```
**Output**: Removes all test data

---

## Production Migration

### 1. Backup First! (CRITICAL)
```bash
cp homerack.db homerack.db.backup-$(date +%Y%m%d-%H%M%S)
```

### 2. Check Current Status
```bash
python3 scripts/check_migration_status.py
```

### 3. Dry Run
```bash
python3 scripts/migrate_specs_to_catalog.py --dry-run --verbose
```

### 4. Review Output
- Check device type classifications
- Look for duplicates
- Verify brand slugs

### 5. Run Migration
```bash
python3 scripts/migrate_specs_to_catalog.py --verbose --skip-duplicates
```

### 6. Verify Success
```bash
python3 scripts/check_migration_status.py
```

### 7. If Issues - Rollback
```bash
cp homerack.db.backup-YYYYMMDD-HHMMSS homerack.db
```

---

## One-Liner Test
```bash
python3 scripts/test_migration.py setup && \
python3 scripts/migrate_specs_to_catalog.py --dry-run && \
echo "yes" | python3 scripts/migrate_specs_to_catalog.py --skip-duplicates && \
python3 scripts/check_migration_status.py && \
python3 scripts/test_migration.py cleanup
```

---

## Common Options

### Migrate Script Options
```bash
--dry-run           # Preview only, no changes
--verbose           # Show detailed logs
--batch-size 50     # Process 50 at a time
--skip-duplicates   # Skip instead of error on dupes
```

### Test Script Options
```bash
setup    # Create test data
verify   # Check migration results
cleanup  # Remove test data
```

---

## Quick Troubleshooting

**Problem**: Can't find python
```bash
# Use python3 instead
python3 scripts/...
```

**Problem**: Module not found
```bash
# Make sure you're in backend directory
cd /home/calounx/repositories/homerack/backend
```

**Problem**: Database locked
```bash
# Stop the app, use smaller batches
python3 scripts/migrate_specs_to_catalog.py --batch-size 25
```

**Problem**: Duplicate errors
```bash
# Use skip-duplicates flag
python3 scripts/migrate_specs_to_catalog.py --skip-duplicates
```

---

## Expected Output

### Successful Migration
```
======================================================================
MIGRATION SUMMARY
======================================================================
Duration: 2.45 seconds

Specifications:
  Total found:     150
  Processed:       150
  Migrated:        150
  Skipped:         0
  Failed:          0

Brands:
  Created:         8
  Reused:          142

Models:
  Created:         150
  Duplicates:      0
======================================================================
```

### Status Check After Migration
```
Record Counts:
  Device Specifications: 150
  Brands: 8
  Models: 150
  Device Types: 9

Specification Migration Status:
  Completed:   150 (100.0%)

  ✓ All specifications have been migrated!
```

---

## Need Help?

1. **Full Documentation**: `docs/MIGRATION_GUIDE.md`
2. **Script Details**: `scripts/README.md`
3. **Delivery Summary**: `PHASE2_DELIVERY.md`

---

**Last Updated**: 2026-01-11
