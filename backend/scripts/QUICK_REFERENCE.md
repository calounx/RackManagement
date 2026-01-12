# HomeRack Seed Scripts - Quick Reference Card

## Scripts Overview

| Script | Purpose | Run Time |
|--------|---------|----------|
| `seed_device_types.py` | Seed 9 device types | < 1 sec |
| `seed_brands_models.py` | Seed 15 brands + 56 models | < 2 sec |
| `list_catalog.py` | Explore catalog data | < 1 sec |

---

## Essential Commands

### Initial Setup (First Time)
```bash
cd /home/calounx/repositories/homerack/backend
python3 scripts/seed_device_types.py
python3 scripts/seed_brands_models.py --verbose
python3 scripts/list_catalog.py --stats
```

### Preview Before Seeding
```bash
python3 scripts/seed_brands_models.py --dry-run
```

### Clear and Reseed
```bash
python3 scripts/seed_brands_models.py --clear --verbose
```

### Explore Data
```bash
# List all brands
python3 scripts/list_catalog.py

# Show statistics
python3 scripts/list_catalog.py --stats

# Filter by brand
python3 scripts/list_catalog.py --brand cisco

# Filter by device type
python3 scripts/list_catalog.py --type switch

# Show all models
python3 scripts/list_catalog.py --models
```

---

## Command Flags

### seed_brands_models.py
- `--dry-run` - Preview without changes
- `--clear` - Clear existing data first
- `--verbose` or `-v` - Show detailed output

### list_catalog.py
- `--brands` - List all brands with details
- `--models` - List all models with specs
- `--brand <slug>` - Filter by brand (e.g., cisco, dell)
- `--type <slug>` - Filter by type (e.g., switch, server)
- `--stats` - Show detailed statistics

---

## What Gets Seeded

| Category | Count | Examples |
|----------|-------|----------|
| **Brands** | 15 | Cisco, Dell, HPE, Juniper, Arista |
| **Switches** | 15 | Catalyst 9300, Arista 7050S |
| **Servers** | 12 | PowerEdge R740, ProLiant DL380 |
| **Firewalls** | 8 | PA-3220, FortiGate 100F |
| **Routers** | 7 | ISR 4331, MX204 |
| **Storage** | 4 | PowerVault ME4024, RackStation RS3621xs+ |
| **PDUs** | 6 | APC AP8941, Raritan PX3-5190R |
| **UPS** | 4 | SMX3000RMHV2U, 5PX 3000VA |
| **Total Models** | 56 | Across all device types |

---

## Data Specifications

All models include:
- ✅ Physical dimensions (height U, depth mm, weight kg)
- ✅ Power consumption (watts)
- ✅ Heat output (BTU/hr)
- ✅ Airflow patterns
- ✅ Port configurations (JSON)
- ✅ Mounting types
- ✅ Descriptions
- ✅ Release dates (where applicable)

---

## Verification

```bash
# Quick check
python3 -c "
from app.database import SessionLocal
from app.models import Brand, Model, DeviceType

db = SessionLocal()
print(f'Brands: {db.query(Brand).count()}')
print(f'Models: {db.query(Model).count()}')
print(f'Device Types: {db.query(DeviceType).count()}')
db.close()
"
```

Expected output:
```
Brands: 15
Models: 56
Device Types: 9
```

---

## Troubleshooting

### Script can't find modules
```bash
# Solution: Always run from backend directory
cd /home/calounx/repositories/homerack/backend
python3 scripts/seed_brands_models.py
```

### Want to start fresh
```bash
# Solution: Use --clear flag
python3 scripts/seed_brands_models.py --clear --verbose
```

### See duplicate messages
```bash
# Solution: This is normal - script is idempotent
# Run once more to confirm no duplicates created
python3 scripts/seed_brands_models.py
```

---

## Common Workflows

### Development Setup
```bash
python3 scripts/seed_device_types.py
python3 scripts/seed_brands_models.py
```

### Testing
```bash
python3 scripts/seed_brands_models.py --dry-run
python3 scripts/list_catalog.py --stats
```

### Reset Data
```bash
python3 scripts/seed_brands_models.py --clear
python3 scripts/list_catalog.py --stats
```

### Explore Catalog
```bash
# By brand
python3 scripts/list_catalog.py --brand cisco
python3 scripts/list_catalog.py --brand dell
python3 scripts/list_catalog.py --brand hpe

# By device type
python3 scripts/list_catalog.py --type switch
python3 scripts/list_catalog.py --type server
python3 scripts/list_catalog.py --type firewall
```

---

## Documentation

- **Full Documentation**: [README.md](README.md)
- **Complete Data Reference**: [SEED_DATA_REFERENCE.md](SEED_DATA_REFERENCE.md)
- **Implementation Details**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

---

## Statistics

```
Total Brands: 15
Total Models: 56
Total Device Types: 9

Height Range: 1.0U - 7.0U
Power Range: 10W - 5400W
Average Height: 1.6U
Average Power: 728W
Total Power: 40,047W

Data Quality: 100% complete specifications
Confidence Level: High (all models)
```

---

## Help

```bash
# Get help for any script
python3 scripts/seed_brands_models.py --help
python3 scripts/list_catalog.py --help
```

---

**Version**: 1.0.0
**Last Updated**: 2026-01-11
**Status**: Production Ready ✓
