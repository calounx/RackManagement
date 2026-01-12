# Seed Data Reference

This document describes the default brands and models seeded by `seed_brands_models.py`.

## Overview

- **15 Brands** - Major technology manufacturers
- **56 Models** - Representative device models across all device types
- All data includes realistic specifications and metadata

## Usage

```bash
# Normal seeding (creates data if not exists)
python3 seed_brands_models.py

# Preview without making changes
python3 seed_brands_models.py --dry-run

# Clear existing data and reseed
python3 seed_brands_models.py --clear

# Show detailed output
python3 seed_brands_models.py --verbose

# Clear and show details
python3 seed_brands_models.py --clear --verbose
```

## Brands (15)

1. **Cisco Systems** (11 models)
   - Website: https://www.cisco.com
   - Founded: 1984, San Jose, California, USA
   - Switches, Servers, Routers, Firewalls

2. **Dell Technologies** (6 models)
   - Website: https://www.dell.com
   - Founded: 1984, Round Rock, Texas, USA
   - Servers, Switches, Storage

3. **Hewlett Packard Enterprise** (6 models)
   - Website: https://www.hpe.com
   - Founded: 2015, Houston, Texas, USA
   - Servers, Switches, Storage

4. **Juniper Networks** (4 models)
   - Website: https://www.juniper.net
   - Founded: 1996, Sunnyvale, California, USA
   - Switches, Routers

5. **Arista Networks** (3 models)
   - Website: https://www.arista.com
   - Founded: 2004, Santa Clara, California, USA
   - High-performance Switches

6. **Ubiquiti Inc.** (2 models)
   - Website: https://www.ui.com
   - Founded: 2005, New York City, New York, USA
   - Switches, Routers

7. **Fortinet** (3 models)
   - Website: https://www.fortinet.com
   - Founded: 2000, Sunnyvale, California, USA
   - Firewalls

8. **Palo Alto Networks** (4 models)
   - Website: https://www.paloaltonetworks.com
   - Founded: 2005, Santa Clara, California, USA
   - Firewalls

9. **Supermicro** (2 models)
   - Website: https://www.supermicro.com
   - Founded: 1993, San Jose, California, USA
   - Servers

10. **Synology Inc.** (2 models)
    - Website: https://www.synology.com
    - Founded: 2000, Taipei, Taiwan
    - Storage (NAS)

11. **APC by Schneider Electric** (5 models)
    - Website: https://www.apc.com
    - Founded: 1981, West Kingston, Rhode Island, USA
    - PDUs, UPS

12. **Raritan** (2 models)
    - Website: https://www.raritan.com
    - Founded: 1985, Somerset, New Jersey, USA
    - PDUs

13. **Eaton Corporation** (3 models)
    - Website: https://www.eaton.com
    - Founded: 1911, Dublin, Ireland
    - PDUs, UPS

14. **MikroTik** (2 models)
    - Website: https://mikrotik.com
    - Founded: 1996, Riga, Latvia
    - Routers, Switches

15. **Netgear Inc.** (1 model)
    - Website: https://www.netgear.com
    - Founded: 1996, San Jose, California, USA
    - Switches

## Models by Device Type

### Switches (15 models)

| Brand | Model | Variant | Height | Power | Ports |
|-------|-------|---------|--------|-------|-------|
| Cisco | Catalyst 2960-X | 48-port | 1U | 140W | 48x 1G + 4x SFP |
| Cisco | Catalyst 3850 | 48-port PoE+ | 1U | 350W | 48x 1G PoE+ + 4x 10G SFP+ |
| Cisco | Catalyst 9300 | 48-port UPOE | 1U | 390W | 48x 1G UPOE + 4x 10G SFP+ |
| Cisco | Nexus 3172PQ | - | 1U | 320W | 48x 10G SFP+ + 6x 40G QSFP+ |
| Cisco | Catalyst 9500 | 40-port | 6U | 1100W | 40x 25G + 8x 100G QSFP28 |
| Arista | 7050S-64 | - | 1U | 300W | 64x 10G SFP+ + 4x 40G QSFP+ |
| Arista | 7280R3 | 32-port 100G | 2U | 550W | 32x 100G QSFP28 |
| Arista | 7060X6 | 64-port | 2U | 950W | 64x 400G QSFP-DD |
| Juniper | EX4300-48T | - | 1U | 200W | 48x 1G + 4x 10G SFP+ |
| Juniper | EX4650 | 48-port | 1U | 420W | 48x 10G SFP+ + 8x 100G QSFP28 |
| Ubiquiti | UniFi Switch Pro 48 PoE | - | 1U | 250W | 48x 1G PoE+ + 4x 10G SFP+ |
| HPE | Aruba 6300M | 48-port | 1U | 180W | 48x 1G + 4x 10G SFP+ |
| Dell | PowerSwitch S4148T-ON | - | 1U | 350W | 48x 10GBase-T + 6x 100G QSFP28 |
| Netgear | M4300-48X | - | 1U | 280W | 48x 10G SFP+ + 4x 40G QSFP+ |
| MikroTik | CRS354-48P-4S+2Q+ | - | 1U | 220W | 48x 1G PoE+ + 4x 10G + 2x 40G |

### Servers (12 models)

| Brand | Model | Height | Power | Description |
|-------|-------|--------|-------|-------------|
| Dell | PowerEdge R640 | 1U | 750W | Dual-socket server for virtualization |
| Dell | PowerEdge R740 | 2U | 1100W | Dual-socket with GPU support for AI/ML |
| Dell | PowerEdge R750 | 2U | 1400W | 3rd Gen Intel Xeon dual-socket |
| Dell | PowerEdge R6525 | 1U | 1000W | AMD EPYC high-density computing |
| HPE | ProLiant DL360 Gen10 | 1U | 800W | Industry-leading 1U dual-socket |
| HPE | ProLiant DL380 Gen10 | 2U | 1600W | Versatile 2U dual-socket |
| HPE | ProLiant DL385 Gen10 Plus | 2U | 1200W | AMD EPYC compute-intensive |
| HPE | ProLiant DL560 Gen10 | 2U | 2000W | 4-socket mission-critical |
| Supermicro | SuperServer 1029P-MTR | 1U | 900W | 1U with NVMe support |
| Supermicro | SuperServer 2029U-TN24R4T | 2U | 1600W | 2U with 24x NVMe bays |
| Cisco | UCS C220 M5 | 1U | 770W | General-purpose workloads |
| Cisco | UCS C240 M5 | 2U | 1200W | Demanding applications and big data |

### Firewalls (8 models)

| Brand | Model | Height | Power | Throughput Class |
|-------|-------|--------|-------|------------------|
| Palo Alto | PA-220 | 1U | 35W | Small office |
| Palo Alto | PA-850 | 1U | 95W | Medium enterprise |
| Palo Alto | PA-3220 | 1U | 340W | Large enterprise |
| Palo Alto | PA-5450 | 2U | 1125W | Data center |
| Fortinet | FortiGate 60F | 1U | 26W | Small business SD-WAN |
| Fortinet | FortiGate 100F | 1U | 45W | Distributed enterprise |
| Fortinet | FortiGate 600E | 1U | 180W | Enterprise high-speed |
| Cisco | Firepower 2130 | 1U | 250W | Advanced malware protection |

### Routers (7 models)

| Brand | Model | Height | Power | Description |
|-------|-------|--------|-------|-------------|
| Cisco | ISR 4331 | 1U | 190W | Branch office with SD-WAN |
| Cisco | ISR 4451 | 2U | 400W | High-performance branch |
| Cisco | ASR 1001-X | 2U | 550W | Service provider edge |
| Juniper | MX204 | 1U | 400W | Compact universal routing |
| Juniper | MX480 | 7U | 2500W | Universal edge with high scalability |
| MikroTik | CCR2004-16G-2S+ | 1U | 65W | Cloud Core Router |
| Ubiquiti | EdgeRouter Infinity | 1U | 150W | High-performance 8x 10G |

### Storage (4 models)

| Brand | Model | Height | Power | Bays | Description |
|-------|-------|--------|-------|------|-------------|
| Dell | PowerVault ME4024 | 2U | 400W | 24 | SAS storage array |
| Synology | RackStation RS3621xs+ | 2U | 226W | 12 | Enterprise NAS with scalable storage |
| Synology | RackStation RS2423+ | 2U | 186W | 12 | SMB data consolidation |
| HPE | MSA 2060 | 2U | 500W | 24 | Hybrid flash storage array |

### PDUs (6 models)

| Brand | Model | Height | Amps | Outlets | Features |
|-------|-------|--------|------|---------|----------|
| APC | AP7921 | 1U | 16A | 8x C13 | Switched, horizontal mount |
| APC | AP8941 | 0U | 32A | 21x C13 + 3x C19 | Metered-by-outlet, vertical |
| APC | AP8959 | 0U | 32A | 16x C13 + 8x C19 | Switched, vertical |
| Raritan | PX3-5190R | 0U | 32A | 24x C13 + 6x C19 | Switched, vertical |
| Raritan | PX2-1100 | 0U | 16A | 20x C13 | Basic, vertical |
| Eaton | ePDU G3 Managed | 0U | 32A | 24x C13 + 6x C19 | Managed, vertical |

### UPS (4 models)

| Brand | Model | Height | Power | Description |
|-------|-------|--------|-------|-------------|
| APC | SMX3000RMHV2U | 2U | 2700W | 3000VA Rack/Tower LCD |
| APC | SMX1500RM2U | 2U | 1200W | 1500VA Rack/Tower LCD |
| Eaton | 5PX 3000VA 2U | 2U | 2700W | Graphical LCD display |
| Eaton | 9PX 6000VA 3U | 3U | 5400W | Hot-swappable batteries |

## Data Specifications

All models include:

- **Physical Dimensions**: Height (U), width type, depth (mm), weight (kg)
- **Power & Thermal**: Power consumption (watts), heat output (BTU/hr), airflow pattern
- **Connectivity**: Typical ports configuration (JSON)
- **Mounting**: Mounting type (2-post, 4-post, vertical)
- **Metadata**: Source confidence, release dates (where available)

## Notes

- All power consumption and heat output values are realistic and based on manufacturer specifications
- Airflow patterns follow industry standards (front_to_back, passive, etc.)
- Port configurations reflect typical production models
- Heights include fractional units (e.g., 0U for vertical PDUs)
- All brands include website URLs and support URLs for reference
