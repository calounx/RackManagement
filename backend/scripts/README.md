# Homerack Backend Scripts

This directory contains scripts for managing data migrations, seeding default data, and catalog management in the Homerack backend.

## Quick Start

```bash
# 1. Seed device types (9 predefined types)
python3 scripts/seed_device_types.py

# 2. Seed brands and models (15 brands, 56 models)
python3 scripts/seed_brands_models.py --verbose

# 3. Explore the catalog
python3 scripts/list_catalog.py --stats

# 4. View specific brand's models
python3 scripts/list_catalog.py --brand cisco

# 5. View specific device type's models
python3 scripts/list_catalog.py --type switch
```

---

## Table of Contents

1. [Seed Scripts](#seed-scripts)
   - [seed_device_types.py](#1-seed_device_typespy)
   - [seed_brands_models.py](#2-seed_brands_modelspy)
   - [list_catalog.py](#3-list_catalogpy)
2. [Migration Scripts](#migration-scripts)
   - [migrate_specs_to_catalog.py](#4-migrate_specs_to_catalogpy)
   - [check_migration_status.py](#5-check_migration_statuspy)
   - [test_migration.py](#6-test_migrationpy)

---

## Seed Scripts

### 1. seed_device_types.py

**Purpose**: Seed the 9 predefined device types into the database.

**Usage**:
```bash
python3 scripts/seed_device_types.py
```

**Device Types Created**:
- 🖥️ Server
- 🔀 Switch
- 📡 Router
- 🛡️ Firewall
- 💾 Storage
- ⚡ PDU
- 🔋 UPS
- 🔌 Patch Panel
- 📦 Other

**Note**: This script is idempotent - it won't create duplicates if device types already exist.

---

### 2. seed_brands_models.py

**Purpose**: Seed default brands and representative device models into the catalog.

**Usage**:
```bash
# Normal seeding (creates data if not exists)
python3 scripts/seed_brands_models.py

# Preview without making changes
python3 scripts/seed_brands_models.py --dry-run

# Clear existing data and reseed
python3 scripts/seed_brands_models.py --clear

# Show detailed output
python3 scripts/seed_brands_models.py --verbose

# Clear and show details
python3 scripts/seed_brands_models.py --clear --verbose
```

**Options**:
- `--dry-run`: Preview what would be created without making changes
- `--clear`: Remove all existing brands and models before seeding
- `--verbose, -v`: Show detailed output during seeding

**What Gets Seeded**:
- **15 Brands**: Cisco, Dell, HPE, Juniper, Arista, Ubiquiti, Fortinet, Palo Alto, Supermicro, Synology, APC, Raritan, Eaton, MikroTik, Netgear
- **56 Models**: Representative device models across all device types
  - 15 Switches (Cisco Catalyst, Arista 7050S, Juniper EX4300, etc.)
  - 12 Servers (Dell PowerEdge, HPE ProLiant, Supermicro, Cisco UCS)
  - 8 Firewalls (Palo Alto PA series, Fortinet FortiGate)
  - 7 Routers (Cisco ISR/ASR, Juniper MX, MikroTik CCR)
  - 4 Storage (Dell PowerVault, Synology RackStation, HPE MSA)
  - 6 PDUs (APC, Raritan, Eaton)
  - 4 UPS (APC Smart-UPS, Eaton 5PX/9PX)

**Data Includes**:
- Full brand information (name, website, founded year, headquarters)
- Complete model specifications (height, depth, weight, power, thermal)
- Realistic port configurations
- Airflow patterns
- Mounting types

**Documentation**: See [SEED_DATA_REFERENCE.md](SEED_DATA_REFERENCE.md) for complete list of all seeded data.

---

### 3. list_catalog.py

**Purpose**: List and explore the device catalog (brands and models).

**Usage**:
```bash
# List all brands with model counts (default)
python3 scripts/list_catalog.py

# List all brands with details
python3 scripts/list_catalog.py --brands

# List all models
python3 scripts/list_catalog.py --models

# List models for specific brand
python3 scripts/list_catalog.py --brand cisco

# List models for specific device type
python3 scripts/list_catalog.py --type switch

# Show detailed statistics
python3 scripts/list_catalog.py --stats
```

**Options**:
- `--brands`: Show all brands with detailed information
- `--models`: Show all models with specifications
- `--brand <slug>`: Filter models by brand slug (e.g., cisco, dell, hpe)
- `--type <slug>`: Filter models by device type slug (e.g., switch, server, firewall)
- `--stats`: Show comprehensive catalog statistics

**Example Output**:
```
======================================================================
CATALOG STATISTICS
======================================================================

Total Brands: 15
Total Models: 56
Total Device Types: 9

Models per Brand:
  Cisco Systems                             11 models
  Dell Technologies                          6 models
  Hewlett Packard Enterprise                 6 models
  ...

Models per Device Type:
  🔀 Switch                                  15 models
  🖥️ Server                                 12 models
  🛡️ Firewall                                8 models
  ...

Height Distribution (U):
  Min: 1.0U
  Max: 7.0U
  Average: 1.6U

Power Consumption (W):
  Min: 10.0W
  Max: 5400.0W
  Average: 728W
  Total: 40047W
```

---

## Migration Scripts

### 4. migrate_specs_to_catalog.py

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

### 5. check_migration_status.py

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

### 6. test_migration.py

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
