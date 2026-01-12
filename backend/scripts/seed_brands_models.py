#!/usr/bin/env python3
"""
Seed brands and models into the database
Creates realistic technology brands and representative device models across all device types.

Usage:
    python seed_brands_models.py                    # Normal seeding
    python seed_brands_models.py --dry-run          # Preview without changes
    python seed_brands_models.py --clear            # Clear existing data first
    python seed_brands_models.py --verbose          # Show detailed output
    python seed_brands_models.py --clear --verbose  # Clear and show details
"""
import sys
import argparse
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Brand, Model, DeviceType
from sqlalchemy.exc import IntegrityError


# ============================================================================
# BRAND DATA - 15 major technology brands
# ============================================================================
BRANDS = [
    {
        "name": "Cisco Systems",
        "slug": "cisco",
        "website": "https://www.cisco.com",
        "support_url": "https://www.cisco.com/c/en/us/support/index.html",
        "description": "Global leader in networking equipment, security solutions, and collaboration tools",
        "founded_year": 1984,
        "headquarters": "San Jose, California, USA",
        "fetch_confidence": "high",
        "fetch_source": "manual"
    },
    {
        "name": "Dell Technologies",
        "slug": "dell",
        "website": "https://www.dell.com",
        "support_url": "https://www.dell.com/support",
        "description": "Leading provider of servers, storage solutions, and enterprise computing infrastructure",
        "founded_year": 1984,
        "headquarters": "Round Rock, Texas, USA",
        "fetch_confidence": "high",
        "fetch_source": "manual"
    },
    {
        "name": "Hewlett Packard Enterprise",
        "slug": "hpe",
        "website": "https://www.hpe.com",
        "support_url": "https://support.hpe.com",
        "description": "Enterprise technology company providing servers, storage, networking, and hybrid cloud solutions",
        "founded_year": 2015,
        "headquarters": "Houston, Texas, USA",
        "fetch_confidence": "high",
        "fetch_source": "manual"
    },
    {
        "name": "Juniper Networks",
        "slug": "juniper",
        "website": "https://www.juniper.net",
        "support_url": "https://support.juniper.net",
        "description": "High-performance networking equipment manufacturer specializing in routers, switches, and security",
        "founded_year": 1996,
        "headquarters": "Sunnyvale, California, USA",
        "fetch_confidence": "high",
        "fetch_source": "manual"
    },
    {
        "name": "Arista Networks",
        "slug": "arista",
        "website": "https://www.arista.com",
        "support_url": "https://www.arista.com/en/support",
        "description": "Cloud networking solutions and high-speed Ethernet switches for data centers",
        "founded_year": 2004,
        "headquarters": "Santa Clara, California, USA",
        "fetch_confidence": "high",
        "fetch_source": "manual"
    },
    {
        "name": "Ubiquiti Inc.",
        "slug": "ubiquiti",
        "website": "https://www.ui.com",
        "support_url": "https://help.ui.com",
        "description": "Technology company focused on networking products for service providers and enterprises",
        "founded_year": 2005,
        "headquarters": "New York City, New York, USA",
        "fetch_confidence": "high",
        "fetch_source": "manual"
    },
    {
        "name": "Fortinet",
        "slug": "fortinet",
        "website": "https://www.fortinet.com",
        "support_url": "https://support.fortinet.com",
        "description": "Cybersecurity solutions provider specializing in firewalls, intrusion prevention, and secure SD-WAN",
        "founded_year": 2000,
        "headquarters": "Sunnyvale, California, USA",
        "fetch_confidence": "high",
        "fetch_source": "manual"
    },
    {
        "name": "Palo Alto Networks",
        "slug": "palo-alto",
        "website": "https://www.paloaltonetworks.com",
        "support_url": "https://support.paloaltonetworks.com",
        "description": "Enterprise security company offering next-generation firewalls and cloud-based security solutions",
        "founded_year": 2005,
        "headquarters": "Santa Clara, California, USA",
        "fetch_confidence": "high",
        "fetch_source": "manual"
    },
    {
        "name": "Supermicro",
        "slug": "supermicro",
        "website": "https://www.supermicro.com",
        "support_url": "https://www.supermicro.com/en/support",
        "description": "High-performance server and storage technology manufacturer for data centers",
        "founded_year": 1993,
        "headquarters": "San Jose, California, USA",
        "fetch_confidence": "high",
        "fetch_source": "manual"
    },
    {
        "name": "Synology Inc.",
        "slug": "synology",
        "website": "https://www.synology.com",
        "support_url": "https://www.synology.com/en-global/support",
        "description": "Network-attached storage (NAS) solutions and data management services provider",
        "founded_year": 2000,
        "headquarters": "Taipei, Taiwan",
        "fetch_confidence": "high",
        "fetch_source": "manual"
    },
    {
        "name": "APC by Schneider Electric",
        "slug": "apc",
        "website": "https://www.apc.com",
        "support_url": "https://www.apc.com/us/en/support/",
        "description": "Leading manufacturer of uninterruptible power supplies (UPS) and power distribution units (PDU)",
        "founded_year": 1981,
        "headquarters": "West Kingston, Rhode Island, USA",
        "fetch_confidence": "high",
        "fetch_source": "manual"
    },
    {
        "name": "Raritan",
        "slug": "raritan",
        "website": "https://www.raritan.com",
        "support_url": "https://www.raritan.com/support",
        "description": "Data center infrastructure management and intelligent rack PDU solutions",
        "founded_year": 1985,
        "headquarters": "Somerset, New Jersey, USA",
        "fetch_confidence": "high",
        "fetch_source": "manual"
    },
    {
        "name": "Eaton Corporation",
        "slug": "eaton",
        "website": "https://www.eaton.com",
        "support_url": "https://www.eaton.com/us/en-us/support.html",
        "description": "Power management company providing UPS systems, PDUs, and electrical equipment",
        "founded_year": 1911,
        "headquarters": "Dublin, Ireland",
        "fetch_confidence": "high",
        "fetch_source": "manual"
    },
    {
        "name": "MikroTik",
        "slug": "mikrotik",
        "website": "https://mikrotik.com",
        "support_url": "https://mikrotik.com/support",
        "description": "Manufacturer of routers, switches, and wireless systems for ISPs and network operators",
        "founded_year": 1996,
        "headquarters": "Riga, Latvia",
        "fetch_confidence": "high",
        "fetch_source": "manual"
    },
    {
        "name": "Netgear Inc.",
        "slug": "netgear",
        "website": "https://www.netgear.com",
        "support_url": "https://www.netgear.com/support/",
        "description": "Networking equipment provider for consumers, businesses, and service providers",
        "founded_year": 1996,
        "headquarters": "San Jose, California, USA",
        "fetch_confidence": "high",
        "fetch_source": "manual"
    }
]


# ============================================================================
# MODEL DATA - 50 representative device models across all device types
# ============================================================================
MODELS = [
    # ========== SWITCHES (15 models) ==========
    {
        "brand_slug": "cisco",
        "device_type_slug": "switch",
        "name": "Catalyst 2960-X",
        "variant": "48-port",
        "description": "48-port Gigabit Ethernet stackable managed switch with 4x 1G SFP uplinks",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 445.0,
        "weight_kg": 4.8,
        "power_watts": 140.0,
        "heat_output_btu": 477.68,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 45.0,
        "typical_ports": {"gigabit_ethernet": 48, "sfp": 4},
        "mounting_type": "2-post or 4-post",
        "release_date": date(2013, 8, 1)
    },
    {
        "brand_slug": "cisco",
        "device_type_slug": "switch",
        "name": "Catalyst 3850",
        "variant": "48-port PoE+",
        "description": "Enterprise stackable switch with 48 PoE+ ports, 4x 10G SFP+ uplinks",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 457.0,
        "weight_kg": 8.0,
        "power_watts": 350.0,
        "heat_output_btu": 1194.2,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 45.0,
        "typical_ports": {"gigabit_ethernet_poe": 48, "sfp_plus_10g": 4},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "cisco",
        "device_type_slug": "switch",
        "name": "Catalyst 9300",
        "variant": "48-port UPOE",
        "description": "Next-generation stackable switch with UPOE (60W per port), DNA-ready",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 480.0,
        "weight_kg": 9.5,
        "power_watts": 390.0,
        "heat_output_btu": 1330.68,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 45.0,
        "typical_ports": {"gigabit_ethernet_upoe": 48, "sfp_plus_10g": 4},
        "mounting_type": "4-post",
        "release_date": date(2017, 3, 1)
    },
    {
        "brand_slug": "arista",
        "device_type_slug": "switch",
        "name": "7050S-64",
        "description": "64-port 10GbE SFP+ data center switch with low latency",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 554.0,
        "weight_kg": 11.8,
        "power_watts": 300.0,
        "heat_output_btu": 1023.6,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 50.0,
        "typical_ports": {"sfp_plus_10g": 64, "qsfp_plus_40g": 4},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "arista",
        "device_type_slug": "switch",
        "name": "7280R3",
        "variant": "32-port 100G",
        "description": "32-port 100GbE QSFP28 high-performance data center switch",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 610.0,
        "weight_kg": 18.5,
        "power_watts": 550.0,
        "heat_output_btu": 1876.6,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 55.0,
        "typical_ports": {"qsfp28_100g": 32},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "juniper",
        "device_type_slug": "switch",
        "name": "EX4300-48T",
        "description": "48-port Gigabit Ethernet switch with Virtual Chassis technology",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 470.0,
        "weight_kg": 6.5,
        "power_watts": 200.0,
        "heat_output_btu": 682.4,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 45.0,
        "typical_ports": {"gigabit_ethernet": 48, "sfp_plus_10g": 4},
        "mounting_type": "2-post or 4-post"
    },
    {
        "brand_slug": "juniper",
        "device_type_slug": "switch",
        "name": "EX4650",
        "variant": "48-port",
        "description": "High-density 10GbE switch with 48x 10G SFP+ and 8x 40G/100G QSFP28 ports",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 534.0,
        "weight_kg": 12.3,
        "power_watts": 420.0,
        "heat_output_btu": 1433.04,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 50.0,
        "typical_ports": {"sfp_plus_10g": 48, "qsfp28_100g": 8},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "ubiquiti",
        "device_type_slug": "switch",
        "name": "UniFi Switch Pro 48 PoE",
        "description": "48-port Gigabit PoE+ managed switch with 4x 10G SFP+",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 350.0,
        "weight_kg": 5.9,
        "power_watts": 250.0,
        "heat_output_btu": 853.0,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"gigabit_ethernet_poe": 48, "sfp_plus_10g": 4},
        "mounting_type": "2-post or 4-post"
    },
    {
        "brand_slug": "hpe",
        "device_type_slug": "switch",
        "name": "Aruba 6300M",
        "variant": "48-port",
        "description": "Stackable campus switch with 48x 1G and 4x 10G SFP+ ports",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 403.0,
        "weight_kg": 5.5,
        "power_watts": 180.0,
        "heat_output_btu": 614.16,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 45.0,
        "typical_ports": {"gigabit_ethernet": 48, "sfp_plus_10g": 4},
        "mounting_type": "2-post or 4-post"
    },
    {
        "brand_slug": "dell",
        "device_type_slug": "switch",
        "name": "PowerSwitch S4148T-ON",
        "description": "48-port 10GBase-T and 6x 40/100G QSFP28 switch",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 523.0,
        "weight_kg": 7.8,
        "power_watts": 350.0,
        "heat_output_btu": 1194.2,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 45.0,
        "typical_ports": {"10gbase_t": 48, "qsfp28_100g": 6},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "netgear",
        "device_type_slug": "switch",
        "name": "M4300-48X",
        "description": "48-port 10G Ethernet stackable managed switch",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 425.0,
        "weight_kg": 6.2,
        "power_watts": 280.0,
        "heat_output_btu": 955.36,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 50.0,
        "typical_ports": {"sfp_plus_10g": 48, "qsfp_plus_40g": 4},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "mikrotik",
        "device_type_slug": "switch",
        "name": "CRS354-48P-4S+2Q+",
        "description": "48-port Gigabit PoE+ switch with 4x 10G SFP+ and 2x 40G QSFP+",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 285.0,
        "weight_kg": 3.8,
        "power_watts": 220.0,
        "heat_output_btu": 750.64,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"gigabit_ethernet_poe": 48, "sfp_plus_10g": 4, "qsfp_plus_40g": 2},
        "mounting_type": "2-post or 4-post"
    },
    {
        "brand_slug": "cisco",
        "device_type_slug": "switch",
        "name": "Nexus 3172PQ",
        "description": "Data center switch with 48x 10G SFP+ and 6x 40G QSFP+",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 508.0,
        "weight_kg": 9.2,
        "power_watts": 320.0,
        "heat_output_btu": 1091.84,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 45.0,
        "typical_ports": {"sfp_plus_10g": 48, "qsfp_plus_40g": 6},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "cisco",
        "device_type_slug": "switch",
        "name": "Catalyst 9500",
        "variant": "40-port",
        "description": "Modular core switch with 40x 10/25G ports, expandable",
        "height_u": 6.0,
        "width_type": "19\"",
        "depth_mm": 558.0,
        "weight_kg": 32.0,
        "power_watts": 1100.0,
        "heat_output_btu": 3753.2,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 45.0,
        "typical_ports": {"sfp28_25g": 40, "qsfp28_100g": 8},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "arista",
        "device_type_slug": "switch",
        "name": "7060X6",
        "variant": "64-port",
        "description": "Ultra-low latency 64-port 400GbE switch for high-frequency trading",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 635.0,
        "weight_kg": 24.5,
        "power_watts": 950.0,
        "heat_output_btu": 3241.4,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 55.0,
        "typical_ports": {"qsfpdd_400g": 64},
        "mounting_type": "4-post"
    },

    # ========== SERVERS (12 models) ==========
    {
        "brand_slug": "dell",
        "device_type_slug": "server",
        "name": "PowerEdge R640",
        "description": "Dual-socket 1U server for high-performance computing and virtualization",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 690.0,
        "weight_kg": 18.5,
        "power_watts": 750.0,
        "heat_output_btu": 2559.0,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 35.0,
        "typical_ports": {"gigabit_ethernet": 4, "usb_3_0": 2, "vga": 1},
        "mounting_type": "4-post",
        "release_date": date(2017, 5, 1)
    },
    {
        "brand_slug": "dell",
        "device_type_slug": "server",
        "name": "PowerEdge R740",
        "description": "Dual-socket 2U server with GPU support for AI/ML workloads",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 735.0,
        "weight_kg": 29.4,
        "power_watts": 1100.0,
        "heat_output_btu": 3753.2,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 35.0,
        "typical_ports": {"gigabit_ethernet": 4, "usb_3_0": 2, "vga": 1, "pcie_slots": 8},
        "mounting_type": "4-post",
        "release_date": date(2017, 5, 1)
    },
    {
        "brand_slug": "dell",
        "device_type_slug": "server",
        "name": "PowerEdge R750",
        "description": "3rd Gen Intel Xeon dual-socket 2U server for enterprise workloads",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 719.8,
        "weight_kg": 31.2,
        "power_watts": 1400.0,
        "heat_output_btu": 4776.8,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"10g_ethernet": 2, "gigabit_ethernet": 2, "usb_3_0": 2},
        "mounting_type": "4-post",
        "release_date": date(2021, 4, 1)
    },
    {
        "brand_slug": "hpe",
        "device_type_slug": "server",
        "name": "ProLiant DL360 Gen10",
        "description": "Industry-leading 1U dual-socket server for virtualization and cloud",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 709.9,
        "weight_kg": 17.0,
        "power_watts": 800.0,
        "heat_output_btu": 2729.6,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 35.0,
        "typical_ports": {"gigabit_ethernet": 4, "usb_3_0": 2, "flexiblelom_slots": 1},
        "mounting_type": "4-post",
        "release_date": date(2017, 10, 1)
    },
    {
        "brand_slug": "hpe",
        "device_type_slug": "server",
        "name": "ProLiant DL380 Gen10",
        "description": "Versatile 2U dual-socket server for diverse workloads",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 686.0,
        "weight_kg": 29.0,
        "power_watts": 1600.0,
        "heat_output_btu": 5459.2,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 35.0,
        "typical_ports": {"10g_ethernet": 2, "gigabit_ethernet": 2, "usb_3_0": 2},
        "mounting_type": "4-post",
        "release_date": date(2017, 10, 1)
    },
    {
        "brand_slug": "hpe",
        "device_type_slug": "server",
        "name": "ProLiant DL385 Gen10 Plus",
        "description": "AMD EPYC 2U server for compute-intensive applications",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 722.0,
        "weight_kg": 30.5,
        "power_watts": 1200.0,
        "heat_output_btu": 4094.4,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"10g_ethernet": 2, "gigabit_ethernet": 2, "usb_3_0": 2},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "supermicro",
        "device_type_slug": "server",
        "name": "SuperServer 1029P-MTR",
        "description": "1U dual-socket Intel Xeon Scalable server with NVMe support",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 725.0,
        "weight_kg": 19.0,
        "power_watts": 900.0,
        "heat_output_btu": 3070.8,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 35.0,
        "typical_ports": {"10g_ethernet": 2, "gigabit_ethernet": 1, "usb_3_0": 2},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "supermicro",
        "device_type_slug": "server",
        "name": "SuperServer 2029U-TN24R4T",
        "description": "2U dual-socket server with 24x NVMe drive bays",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 710.0,
        "weight_kg": 35.0,
        "power_watts": 1600.0,
        "heat_output_btu": 5459.2,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 35.0,
        "typical_ports": {"10g_ethernet": 2, "usb_3_0": 2, "nvme_bays": 24},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "cisco",
        "device_type_slug": "server",
        "name": "UCS C220 M5",
        "description": "Enterprise-class 1U server for general-purpose workloads",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 757.0,
        "weight_kg": 21.0,
        "power_watts": 770.0,
        "heat_output_btu": 2627.24,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 35.0,
        "typical_ports": {"10g_ethernet": 2, "gigabit_ethernet": 1, "usb_3_0": 2},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "cisco",
        "device_type_slug": "server",
        "name": "UCS C240 M5",
        "description": "Versatile 2U server for demanding applications and big data",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 812.0,
        "weight_kg": 39.5,
        "power_watts": 1200.0,
        "heat_output_btu": 4094.4,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 35.0,
        "typical_ports": {"10g_ethernet": 2, "gigabit_ethernet": 1, "usb_3_0": 2},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "dell",
        "device_type_slug": "server",
        "name": "PowerEdge R6525",
        "description": "AMD EPYC 1U server for high-density computing",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 715.0,
        "weight_kg": 20.3,
        "power_watts": 1000.0,
        "heat_output_btu": 3412.0,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"10g_ethernet": 2, "gigabit_ethernet": 2, "usb_3_0": 2},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "hpe",
        "device_type_slug": "server",
        "name": "ProLiant DL560 Gen10",
        "description": "4-socket 2U server for mission-critical applications",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 813.0,
        "weight_kg": 45.0,
        "power_watts": 2000.0,
        "heat_output_btu": 6824.0,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 35.0,
        "typical_ports": {"10g_ethernet": 4, "usb_3_0": 2},
        "mounting_type": "4-post"
    },

    # ========== FIREWALLS (8 models) ==========
    {
        "brand_slug": "palo-alto",
        "device_type_slug": "firewall",
        "name": "PA-220",
        "description": "Next-generation firewall for small offices and retail locations",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 279.0,
        "weight_kg": 2.4,
        "power_watts": 35.0,
        "heat_output_btu": 119.42,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"gigabit_ethernet": 8, "console": 1, "usb": 1},
        "mounting_type": "2-post"
    },
    {
        "brand_slug": "palo-alto",
        "device_type_slug": "firewall",
        "name": "PA-850",
        "description": "ML-powered next-generation firewall for medium enterprises",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 368.0,
        "weight_kg": 5.2,
        "power_watts": 95.0,
        "heat_output_btu": 324.14,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"gigabit_ethernet": 16, "sfp": 4, "console": 1},
        "mounting_type": "2-post or 4-post"
    },
    {
        "brand_slug": "palo-alto",
        "device_type_slug": "firewall",
        "name": "PA-3220",
        "description": "High-performance firewall for large enterprises and data centers",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 483.0,
        "weight_kg": 9.1,
        "power_watts": 340.0,
        "heat_output_btu": 1160.08,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"gigabit_ethernet": 16, "sfp_plus_10g": 4, "console": 1},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "palo-alto",
        "device_type_slug": "firewall",
        "name": "PA-5450",
        "description": "Data center firewall with high throughput and advanced threat prevention",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 635.0,
        "weight_kg": 27.0,
        "power_watts": 1125.0,
        "heat_output_btu": 3838.5,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"sfp_plus_10g": 24, "qsfp_plus_40g": 4},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "fortinet",
        "device_type_slug": "firewall",
        "name": "FortiGate 60F",
        "description": "Secure SD-WAN firewall for small businesses",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 270.0,
        "weight_kg": 2.1,
        "power_watts": 26.0,
        "heat_output_btu": 88.71,
        "airflow_pattern": "passive",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"gigabit_ethernet": 10, "usb": 1},
        "mounting_type": "2-post"
    },
    {
        "brand_slug": "fortinet",
        "device_type_slug": "firewall",
        "name": "FortiGate 100F",
        "description": "Next-generation firewall for distributed enterprises",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 300.0,
        "weight_kg": 3.5,
        "power_watts": 45.0,
        "heat_output_btu": 153.54,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"gigabit_ethernet": 16, "sfp": 2, "usb": 2},
        "mounting_type": "2-post"
    },
    {
        "brand_slug": "fortinet",
        "device_type_slug": "firewall",
        "name": "FortiGate 600E",
        "description": "Enterprise firewall with high-speed threat protection",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 430.0,
        "weight_kg": 8.0,
        "power_watts": 180.0,
        "heat_output_btu": 614.16,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 45.0,
        "typical_ports": {"gigabit_ethernet": 18, "sfp_plus_10g": 8},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "cisco",
        "device_type_slug": "firewall",
        "name": "Firepower 2130",
        "description": "Next-generation firewall with advanced malware protection",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 457.0,
        "weight_kg": 9.5,
        "power_watts": 250.0,
        "heat_output_btu": 853.0,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"gigabit_ethernet": 12, "sfp": 4, "console": 1},
        "mounting_type": "4-post"
    },

    # ========== ROUTERS (7 models) ==========
    {
        "brand_slug": "cisco",
        "device_type_slug": "router",
        "name": "ISR 4331",
        "description": "Integrated Services Router for branch offices with SD-WAN support",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 400.0,
        "weight_kg": 6.3,
        "power_watts": 190.0,
        "heat_output_btu": 648.28,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"gigabit_ethernet": 3, "sfp": 2, "usb_3_0": 2, "console": 1},
        "mounting_type": "2-post or 4-post"
    },
    {
        "brand_slug": "cisco",
        "device_type_slug": "router",
        "name": "ISR 4451",
        "description": "High-performance branch router for large enterprises",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 457.0,
        "weight_kg": 13.6,
        "power_watts": 400.0,
        "heat_output_btu": 1364.8,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"gigabit_ethernet": 3, "sfp": 4, "usb_3_0": 2},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "cisco",
        "device_type_slug": "router",
        "name": "ASR 1001-X",
        "description": "Aggregation Services Router for service provider edge",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 508.0,
        "weight_kg": 18.5,
        "power_watts": 550.0,
        "heat_output_btu": 1876.6,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"gigabit_ethernet": 6, "sfp_plus_10g": 8},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "juniper",
        "device_type_slug": "router",
        "name": "MX204",
        "description": "Compact universal routing platform for service providers",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 556.0,
        "weight_kg": 12.7,
        "power_watts": 400.0,
        "heat_output_btu": 1364.8,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 45.0,
        "typical_ports": {"sfp_plus_10g": 8, "qsfp28_100g": 4},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "juniper",
        "device_type_slug": "router",
        "name": "MX480",
        "description": "Universal edge router with high scalability",
        "height_u": 7.0,
        "width_type": "19\"",
        "depth_mm": 600.0,
        "weight_kg": 55.0,
        "power_watts": 2500.0,
        "heat_output_btu": 8530.0,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"modular_slots": 4},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "mikrotik",
        "device_type_slug": "router",
        "name": "CCR2004-16G-2S+",
        "description": "Cloud Core Router with 16 Gigabit and 2x 10G SFP+ ports",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 295.0,
        "weight_kg": 2.8,
        "power_watts": 65.0,
        "heat_output_btu": 221.78,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"gigabit_ethernet": 16, "sfp_plus_10g": 2, "usb": 1},
        "mounting_type": "2-post"
    },
    {
        "brand_slug": "ubiquiti",
        "device_type_slug": "router",
        "name": "EdgeRouter Infinity",
        "description": "High-performance router with 8x 10G SFP+ ports",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 243.0,
        "weight_kg": 3.5,
        "power_watts": 150.0,
        "heat_output_btu": 511.8,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"gigabit_ethernet": 1, "sfp_plus_10g": 8},
        "mounting_type": "2-post"
    },

    # ========== STORAGE (4 models) ==========
    {
        "brand_slug": "dell",
        "device_type_slug": "storage",
        "name": "PowerVault ME4024",
        "description": "24-bay SAS storage array for small to medium businesses",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 650.0,
        "weight_kg": 28.0,
        "power_watts": 400.0,
        "heat_output_btu": 1364.8,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 35.0,
        "typical_ports": {"sas_12gbps": 4, "gigabit_ethernet": 2, "drive_bays": 24},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "synology",
        "device_type_slug": "storage",
        "name": "RackStation RS3621xs+",
        "description": "12-bay enterprise NAS with scalable storage",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 507.0,
        "weight_kg": 15.5,
        "power_watts": 226.0,
        "heat_output_btu": 771.11,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"10g_ethernet": 4, "gigabit_ethernet": 2, "usb_3_2": 4, "drive_bays": 12},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "synology",
        "device_type_slug": "storage",
        "name": "RackStation RS2423+",
        "description": "12-bay rackmount NAS for SMB data consolidation",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 480.0,
        "weight_kg": 12.8,
        "power_watts": 186.0,
        "heat_output_btu": 634.63,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"gigabit_ethernet": 4, "usb_3_2": 4, "drive_bays": 12},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "hpe",
        "device_type_slug": "storage",
        "name": "MSA 2060",
        "description": "Hybrid flash storage array for small to medium enterprises",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 665.0,
        "weight_kg": 30.0,
        "power_watts": 500.0,
        "heat_output_btu": 1706.0,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 35.0,
        "typical_ports": {"sas_12gbps": 4, "sfp_plus_10g": 4, "drive_bays": 24},
        "mounting_type": "4-post"
    },

    # ========== PDUs (6 models) ==========
    {
        "brand_slug": "apc",
        "device_type_slug": "pdu",
        "name": "AP7921",
        "description": "Rack PDU 2G, Switched, 1U, 16A, 100-240V, (8) C13",
        "height_u": 1.0,
        "width_type": "19\"",
        "depth_mm": 437.0,
        "weight_kg": 2.3,
        "power_watts": 10.0,
        "heat_output_btu": 34.12,
        "airflow_pattern": "passive",
        "max_operating_temp_c": 45.0,
        "typical_ports": {"c13_outlets": 8, "ethernet": 1},
        "mounting_type": "2-post"
    },
    {
        "brand_slug": "apc",
        "device_type_slug": "pdu",
        "name": "AP8941",
        "description": "Rack PDU 2G, Metered-by-Outlet, ZeroU, 32A, 230V, (21) C13 & (3) C19",
        "height_u": 0.0,
        "width_type": "19\"",
        "depth_mm": 44.0,
        "weight_kg": 3.2,
        "power_watts": 12.0,
        "heat_output_btu": 40.94,
        "airflow_pattern": "passive",
        "max_operating_temp_c": 60.0,
        "typical_ports": {"c13_outlets": 21, "c19_outlets": 3, "ethernet": 1},
        "mounting_type": "vertical"
    },
    {
        "brand_slug": "apc",
        "device_type_slug": "pdu",
        "name": "AP8959",
        "description": "Rack PDU 2G, Switched, ZeroU, 32A, 230V, (16) C13 & (8) C19",
        "height_u": 0.0,
        "width_type": "19\"",
        "depth_mm": 51.0,
        "weight_kg": 4.5,
        "power_watts": 15.0,
        "heat_output_btu": 51.18,
        "airflow_pattern": "passive",
        "max_operating_temp_c": 60.0,
        "typical_ports": {"c13_outlets": 16, "c19_outlets": 8, "ethernet": 1},
        "mounting_type": "vertical"
    },
    {
        "brand_slug": "raritan",
        "device_type_slug": "pdu",
        "name": "PX3-5190R",
        "description": "Switched PDU, 32A, 230V, (24) C13 & (6) C19 outlets",
        "height_u": 0.0,
        "width_type": "19\"",
        "depth_mm": 57.0,
        "weight_kg": 4.8,
        "power_watts": 14.0,
        "heat_output_btu": 47.77,
        "airflow_pattern": "passive",
        "max_operating_temp_c": 60.0,
        "typical_ports": {"c13_outlets": 24, "c19_outlets": 6, "ethernet": 1, "usb": 1},
        "mounting_type": "vertical"
    },
    {
        "brand_slug": "raritan",
        "device_type_slug": "pdu",
        "name": "PX2-1100",
        "description": "Basic PDU, 16A, 230V, (20) C13 outlets",
        "height_u": 0.0,
        "width_type": "19\"",
        "depth_mm": 45.0,
        "weight_kg": 2.5,
        "power_watts": 0.0,
        "heat_output_btu": 0.0,
        "airflow_pattern": "passive",
        "max_operating_temp_c": 60.0,
        "typical_ports": {"c13_outlets": 20},
        "mounting_type": "vertical"
    },
    {
        "brand_slug": "eaton",
        "device_type_slug": "pdu",
        "name": "ePDU G3 Managed",
        "description": "Managed rack PDU, 32A, 230V, (24) C13 & (6) C19 outlets",
        "height_u": 0.0,
        "width_type": "19\"",
        "depth_mm": 53.0,
        "weight_kg": 4.2,
        "power_watts": 13.0,
        "heat_output_btu": 44.36,
        "airflow_pattern": "passive",
        "max_operating_temp_c": 60.0,
        "typical_ports": {"c13_outlets": 24, "c19_outlets": 6, "ethernet": 1},
        "mounting_type": "vertical"
    },

    # ========== UPS (4 models) ==========
    {
        "brand_slug": "apc",
        "device_type_slug": "ups",
        "name": "SMX3000RMHV2U",
        "description": "Smart-UPS X 3000VA Rack/Tower LCD 200-240V",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 660.0,
        "weight_kg": 59.0,
        "power_watts": 2700.0,
        "heat_output_btu": 9212.4,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"c13_outlets": 6, "c19_outlets": 2, "ethernet": 1, "usb": 1},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "apc",
        "device_type_slug": "ups",
        "name": "SMX1500RM2U",
        "description": "Smart-UPS X 1500VA Rack/Tower LCD 120V",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 559.0,
        "weight_kg": 38.1,
        "power_watts": 1200.0,
        "heat_output_btu": 4094.4,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"c13_outlets": 8, "ethernet": 1, "usb": 1},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "eaton",
        "device_type_slug": "ups",
        "name": "5PX 3000VA 2U",
        "description": "5PX UPS 3000VA 2U Rack/Tower with graphical LCD",
        "height_u": 2.0,
        "width_type": "19\"",
        "depth_mm": 660.0,
        "weight_kg": 34.0,
        "power_watts": 2700.0,
        "heat_output_btu": 9212.4,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"c13_outlets": 6, "c19_outlets": 2, "ethernet": 1, "usb": 2},
        "mounting_type": "4-post"
    },
    {
        "brand_slug": "eaton",
        "device_type_slug": "ups",
        "name": "9PX 6000VA 3U",
        "description": "9PX UPS 6000VA 3U Rack/Tower with hot-swappable batteries",
        "height_u": 3.0,
        "width_type": "19\"",
        "depth_mm": 730.0,
        "weight_kg": 65.0,
        "power_watts": 5400.0,
        "heat_output_btu": 18424.8,
        "airflow_pattern": "front_to_back",
        "max_operating_temp_c": 40.0,
        "typical_ports": {"c13_outlets": 8, "c19_outlets": 4, "ethernet": 1, "usb": 2},
        "mounting_type": "4-post"
    }
]


def clear_data(db, verbose=False):
    """Clear existing brands and models"""
    try:
        model_count = db.query(Model).count()
        brand_count = db.query(Brand).count()

        if model_count > 0 or brand_count > 0:
            if verbose:
                print(f"Clearing {model_count} models and {brand_count} brands...")

            db.query(Model).delete()
            db.query(Brand).delete()
            db.commit()

            print(f"Cleared {model_count} models and {brand_count} brands")
        else:
            print("No existing data to clear")

    except Exception as e:
        print(f"Error clearing data: {e}")
        db.rollback()
        raise


def seed_brands(db, verbose=False):
    """Seed brands into database"""
    created_brands = {}
    skipped = 0

    for brand_data in BRANDS:
        try:
            # Check if brand already exists
            existing = db.query(Brand).filter(Brand.slug == brand_data["slug"]).first()
            if existing:
                created_brands[brand_data["slug"]] = existing
                skipped += 1
                if verbose:
                    print(f"  Skipping existing brand: {brand_data['name']}")
                continue

            brand = Brand(**brand_data)
            db.add(brand)
            db.flush()  # Get ID without committing

            created_brands[brand_data["slug"]] = brand

            if verbose:
                print(f"  Created brand: {brand.name} (ID: {brand.id})")

        except IntegrityError as e:
            db.rollback()
            print(f"  Error creating brand {brand_data['name']}: {e}")
            # Try to get existing
            existing = db.query(Brand).filter(Brand.slug == brand_data["slug"]).first()
            if existing:
                created_brands[brand_data["slug"]] = existing
                skipped += 1

    db.commit()

    created_count = len(created_brands) - skipped
    print(f"Brands: {created_count} created, {skipped} skipped, {len(created_brands)} total")

    return created_brands


def seed_models(db, brands_map, verbose=False):
    """Seed models into database"""
    # Get device types
    device_types = {dt.slug: dt for dt in db.query(DeviceType).all()}

    if not device_types:
        print("ERROR: No device types found. Please run seed_device_types.py first")
        return 0

    created = 0
    skipped = 0
    errors = 0

    for model_data in MODELS:
        try:
            brand_slug = model_data.pop("brand_slug")
            device_type_slug = model_data.pop("device_type_slug")

            # Get brand and device type
            brand = brands_map.get(brand_slug)
            device_type = device_types.get(device_type_slug)

            if not brand:
                print(f"  ERROR: Brand '{brand_slug}' not found for model {model_data.get('name')}")
                errors += 1
                continue

            if not device_type:
                print(f"  ERROR: Device type '{device_type_slug}' not found for model {model_data.get('name')}")
                errors += 1
                continue

            # Check if model already exists
            existing = db.query(Model).filter(
                Model.brand_id == brand.id,
                Model.name == model_data["name"],
                Model.variant == model_data.get("variant")
            ).first()

            if existing:
                skipped += 1
                if verbose:
                    print(f"  Skipping existing model: {brand.name} {model_data['name']}")
                continue

            # Create model
            model = Model(
                brand_id=brand.id,
                device_type_id=device_type.id,
                source="manual",
                confidence="high",
                **model_data
            )
            db.add(model)

            created += 1
            if verbose:
                variant_str = f" ({model.variant})" if model.variant else ""
                print(f"  Created: {brand.name} {model.name}{variant_str} - {device_type.name}")

        except Exception as e:
            print(f"  ERROR creating model {model_data.get('name')}: {e}")
            errors += 1
            db.rollback()
            continue

    db.commit()

    print(f"Models: {created} created, {skipped} skipped, {errors} errors")

    return created


def print_summary(db):
    """Print summary statistics"""
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    # Brand stats
    brands = db.query(Brand).all()
    print(f"\nTotal Brands: {len(brands)}")
    for brand in sorted(brands, key=lambda b: b.name):
        model_count = db.query(Model).filter(Model.brand_id == brand.id).count()
        print(f"  {brand.name}: {model_count} models")

    # Device type stats
    device_types = db.query(DeviceType).all()
    print(f"\nTotal Device Types: {len(device_types)}")
    for dt in sorted(device_types, key=lambda d: d.name):
        model_count = db.query(Model).filter(Model.device_type_id == dt.id).count()
        print(f"  {dt.icon} {dt.name}: {model_count} models")

    # Total models
    total_models = db.query(Model).count()
    print(f"\nTotal Models: {total_models}")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Seed brands and models into HomeRack database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python seed_brands_models.py                    # Normal seeding
  python seed_brands_models.py --dry-run          # Preview without changes
  python seed_brands_models.py --clear            # Clear existing data first
  python seed_brands_models.py --verbose          # Show detailed output
  python seed_brands_models.py --clear --verbose  # Clear and show details
        """
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    parser.add_argument("--clear", action="store_true", help="Clear existing brands and models first")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")

    args = parser.parse_args()

    print("="*60)
    print("HomeRack - Seed Brands & Models")
    print("="*60)

    if args.dry_run:
        print("\nDRY RUN MODE - No changes will be made\n")
        print(f"Would seed:")
        print(f"  - {len(BRANDS)} brands")
        print(f"  - {len(MODELS)} models")
        print(f"\nBrands to be created:")
        for brand in BRANDS:
            print(f"  • {brand['name']} ({brand['slug']})")
        print(f"\nModels breakdown by device type:")
        from collections import Counter
        type_counts = Counter(m["device_type_slug"] for m in MODELS)
        for device_type, count in sorted(type_counts.items()):
            print(f"  • {device_type}: {count} models")
        return

    db = SessionLocal()
    try:
        # Clear existing data if requested
        if args.clear:
            print("\nClearing existing data...")
            clear_data(db, args.verbose)
            print()

        # Seed brands
        print("Seeding brands...")
        brands_map = seed_brands(db, args.verbose)
        print()

        # Seed models
        print("Seeding models...")
        models_created = seed_models(db, brands_map, args.verbose)
        print()

        # Print summary
        print_summary(db)

        print("\n" + "="*60)
        print("Done!")
        print("="*60)

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
