# Homerack Migration Scripts

This directory contains scripts for managing data migrations in the Homerack backend.

## Scripts

### 1. migrate_specs_to_catalog.py

**Purpose**: Migrate device specifications from the legacy `device_specifications` table to the new normalized `brands` and `models` catalog structure.

**Usage**:
```bash
# Preview migration (recommended first step)
python3 scripts/migrate_specs_to_catalog.py --dry-run --verbose

# Run migration
python3 scripts/migrate_specs_to_catalog.py --verbose

# Run with custom options
python3 scripts/migrate_specs_to_catalog.py --batch-size 50 --skip-duplicates
```

**Options**:
- `--dry-run`: Preview changes without committing to database
- `--verbose`: Enable detailed logging
- `--batch-size N`: Process N specifications per batch (default: 100)
- `--skip-duplicates`: Skip duplicate entries instead of raising errors

**Documentation**: See [MIGRATION_GUIDE.md](../docs/MIGRATION_GUIDE.md) for detailed instructions.

---

### 2. check_migration_status.py

**Purpose**: Check current migration status and catalog statistics.

**Usage**:
```bash
python3 scripts/check_migration_status.py
```

**Output**:
- Record counts (specifications, brands, models, device types)
- Migration status breakdown (pending, completed, failed)
- Brand catalog with model counts
- Device type distribution
- Model statistics (height, power consumption)
- Data quality metrics (completeness, confidence levels)

**When to Use**:
- Before migration (to see what needs migrating)
- During migration (to check progress)
- After migration (to verify success)
- Anytime (to get catalog statistics)

---

### 3. test_migration.py

**Purpose**: Test migration script with sample data before running on production database.

**Usage**:
```bash
# Create sample test data
python3 scripts/test_migration.py setup

# Verify migration results
python3 scripts/test_migration.py verify

# Clean up test data
python3 scripts/test_migration.py cleanup
```

**Test Workflow**:
1. Run `setup` to create 8 sample device specifications
2. Run the migration script with dry-run to preview
3. Run the migration script to actually migrate
4. Run `verify` to check results
5. Run `cleanup` when done testing

**Sample Data Created**:
- 2 Cisco switches (Catalyst 9300, Nexus 5500)
- 2 Dell servers (PowerEdge R740, R640)
- 1 HPE switch (Aruba 2930F)
- 1 Fortinet firewall (FortiGate 100F)
- 1 APC PDU (AP8868)
- 1 duplicate entry (for testing duplicate handling)

---

## Migration Workflow

### Phase 1: Preparation
1. **Backup database**:
   ```bash
   cp homerack.db homerack.db.backup-$(date +%Y%m%d-%H%M%S)
   ```

2. **Test with sample data**:
   ```bash
   python3 scripts/test_migration.py setup
   python3 scripts/migrate_specs_to_catalog.py --dry-run --verbose
   python3 scripts/migrate_specs_to_catalog.py --verbose --skip-duplicates
   python3 scripts/test_migration.py verify
   python3 scripts/test_migration.py cleanup
   ```

### Phase 2: Dry Run
3. **Preview actual migration**:
   ```bash
   python3 scripts/migrate_specs_to_catalog.py --dry-run --verbose
   ```

4. **Review output** for:
   - Unexpected device type classifications
   - Potential duplicates
   - Any error messages

### Phase 3: Migration
5. **Run migration**:
   ```bash
   python3 scripts/migrate_specs_to_catalog.py --verbose --skip-duplicates
   ```

6. **Verify results**:
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

   print(f'Specifications: {specs}')
   print(f'Brands: {brands}')
   print(f'Models: {models}')
   print(f'Migrated: {migrated}')
   db.close()
   "
   ```

### Phase 4: Rollback (if needed)
7. **Restore from backup** if migration fails:
   ```bash
   cp homerack.db.backup-YYYYMMDD-HHMMSS homerack.db
   ```

---

## Device Type Inference

The migration script automatically infers device types from brand and model names using pattern matching:

### Switch Detection
- Cisco: Catalyst, Nexus
- Dell: PowerConnect
- HPE: Aruba, ProCurve
- Generic: "switch" keyword

### Server Detection
- Dell: PowerEdge
- HPE: ProLiant
- Fujitsu: Primergy
- Lenovo: ThinkServer
- Generic: "server" keyword

### Firewall Detection
- Fortinet: FortiGate
- Palo Alto: (brand name)
- Cisco: ASA, Firepower
- Generic: "firewall" keyword

### Router Detection
- Cisco: ASR, ISR
- Generic: "router" keyword

### Storage Detection
- Dell: PowerStore, PowerVault, Compellent
- HPE: Nimble
- Generic: "storage", "san", "nas" keywords

### Other Types
- PDU: "pdu", "power distribution" keywords
- UPS: "ups", "uninterruptible", "smart-ups" keywords
- Patch Panel: "patch panel", "patch" keywords
- Other: Default fallback for unmatched devices

---

## Troubleshooting

### Common Issues

**Issue**: Script can't find modules
```
ModuleNotFoundError: No module named 'app'
```
**Solution**: Run from backend directory:
```bash
cd /home/calounx/repositories/homerack/backend
python3 scripts/migrate_specs_to_catalog.py
```

---

**Issue**: Wrong device types inferred
```
HPE server detected as "other" instead of "server"
```
**Solution**: Update the patterns in `infer_device_type()` function to add more specific product line matches.

---

**Issue**: Duplicate key errors
```
IntegrityError: UNIQUE constraint failed
```
**Solution**: Use `--skip-duplicates` flag:
```bash
python3 scripts/migrate_specs_to_catalog.py --skip-duplicates
```

---

**Issue**: Database locked
```
OperationalError: database is locked
```
**Solution**:
1. Close all other database connections
2. Stop the application if running
3. Use smaller batch size: `--batch-size 25`

---

## Migration Statistics

After migration, the script displays:

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

**Interpretation**:
- **Total found**: Number of device specifications in database
- **Processed**: Number of specifications processed
- **Migrated**: Successfully migrated to new structure
- **Skipped**: Already migrated or duplicates (with `--skip-duplicates`)
- **Failed**: Errors during migration
- **Brands Created**: New brand records created
- **Brands Reused**: Specifications using existing brands
- **Models Created**: New model records created
- **Duplicates**: Duplicate models skipped

---

## Safety Features

Both scripts include:
- ✅ **Dry-run mode**: Preview without changes
- ✅ **Transaction safety**: Batch commits with rollback on error
- ✅ **Duplicate detection**: Warns or skips duplicates
- ✅ **Progress reporting**: Shows real-time progress
- ✅ **Detailed logging**: Verbose mode for debugging
- ✅ **Error handling**: Graceful failure with error reporting
- ✅ **Migration tracking**: Status field on each specification

---

## Best Practices

1. **Always backup** before running migrations
2. **Test first** using `test_migration.py`
3. **Use dry-run** to preview changes
4. **Review output** carefully before actual migration
5. **Use skip-duplicates** if you have duplicate data
6. **Run verification** after migration
7. **Keep backups** until migration is validated in production

---

## Next Steps

After successful migration:
1. Update API endpoints to use `models` table
2. Update frontend to use new catalog structure
3. Test application with migrated data
4. Monitor for issues
5. Consider deprecating old `device_specifications` table
6. Add brand logos and additional metadata
7. Implement brand management features

---

**Last Updated**: 2026-01-11
**Version**: 1.0.0
