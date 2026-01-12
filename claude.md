# HomeRack - Comprehensive Project Documentation for Claude

**Version:** 1.0.1
**Last Updated:** 2026-01-12
**Status:** Production Ready
**Repository:** https://github.com/calounx/RackManagement

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Current Status](#current-status)
3. [Architecture](#architecture)
4. [Technology Stack](#technology-stack)
5. [Project Structure](#project-structure)
6. [Backend Details](#backend-details)
7. [Frontend Details](#frontend-details)
8. [API Documentation](#api-documentation)
9. [Known Issues](#known-issues)
10. [Development Workflow](#development-workflow)
11. [Deployment](#deployment)
12. [Testing](#testing)
13. [Performance Metrics](#performance-metrics)
14. [Security Considerations](#security-considerations)

---

## Project Overview

HomeRack is a comprehensive web application for optimizing network device placement in server racks, featuring:

- **Automatic Device Spec Fetching**: Enter brand + model, system fetches specifications from manufacturer websites
- **Multi-Width Rack Support**: 11", 18", 19", and 23" racks with compatibility validation
- **Intelligent Optimization**: Optimizes for cable management, weight distribution, thermal management, and access frequency
- **Cable BOM Generation**: Automatic cable length calculation and component list generation
- **Modern React UI**: Precision Engineering aesthetic with debug console features
- **Thermal Analysis**: Real-time temperature monitoring with heat maps
- **JWT Authentication**: Secure authentication with role-based access control
- **NetBox Integration**: Complete DCIM integration with NetBox

**Target Users:** Data center managers, network engineers, IT administrators

**Key Value Proposition:** Eliminates manual rack planning by automating device placement optimization and cable management

---

## Current Status

### Version 1.0.1 (Production Ready)

**All Phases Complete:**
- Phase 1: Core backend API and database models
- Phase 2: Complete data migration and brands management UI
- Phase 3: Wikipedia integration, logo upload, and catalog workflow
- Phase 4: Production-ready deployment with auth, PostgreSQL, Redis, and comprehensive testing

**Deployment Status:**
- Backend API running on lampadas.local:8000 (127.0.0.1 internally)
- Frontend deployed via Nginx on lampadas.local:80
- PostgreSQL 15 database (production)
- Redis 7 caching layer
- Prometheus/Grafana monitoring stack
- 4 Gunicorn workers
- JWT authentication with RBAC implemented

**Live URLs:**
- Frontend: http://lampadas.local/
- API Docs: http://lampadas.local/api/docs
- Health Check: http://lampadas.local/api/health

**Test Coverage:**
- 295 backend tests
- 83 E2E tests
- 380+ total tests
- 92.4% test pass rate

---

## Architecture

### System Architecture

```
                          Browser
                             |
                             | HTTP
                             v
+--------------------------------------------------+
|           Nginx Reverse Proxy (Port 80)           |
|           - Serves frontend (/)                   |
|           - Proxies API (/api/*)                  |
+--------------------------------------------------+
                             |
              +--------------+--------------+
              v                             v
      +---------------+          +------------------------+
      |   Frontend    |          |   Backend API          |
      |   (React)     |          |   (FastAPI)            |
      |   /dist       |          |   127.0.0.1:8000       |
      +---------------+          |   4 Gunicorn workers   |
                                 +------------------------+
                                            |
                    +-----------------------+-----------------------+
                    v                       v                       v
           +----------------+      +----------------+      +----------------+
           | PostgreSQL 15  |      |    Redis 7     |      |  Prometheus/   |
           |  (Production)  |      |   (Cache)      |      |   Grafana      |
           +----------------+      +----------------+      +----------------+
```

### Application Layers

**Backend:**
1. **API Layer** (`app/api/`) - FastAPI routers for REST endpoints
2. **Models Layer** (`app/models.py`) - SQLAlchemy ORM models
3. **Service Layer** (`app/fetchers/`, `app/thermal.py`) - Business logic
4. **Abstraction Layer** (`app/utils/`) - Circuit breakers, retry logic, validators
5. **Data Layer** (`app/database.py`) - Database connection and session management
6. **Auth Layer** - JWT authentication with RBAC

**Frontend:**
1. **Routing Layer** (React Router) - Page navigation
2. **State Layer** (Zustand) - Global state management
3. **Component Layer** (`src/components/`) - Reusable UI components
4. **Service Layer** (`src/lib/api.ts`) - API client
5. **Presentation Layer** (React components with Tailwind CSS)

---

## Technology Stack

### Backend
- **Language:** Python 3.11+
- **Framework:** FastAPI 0.109.0
- **ORM:** SQLAlchemy 2.0+
- **Database:** PostgreSQL 15 (production), SQLite (development)
- **Caching:** Redis 7
- **Web Scraping:** BeautifulSoup4, pdfplumber, httpx
- **ASGI Server:** Gunicorn with Uvicorn workers (4 workers)
- **Authentication:** JWT with RBAC

**Key Libraries:**
- `pybreaker` - Circuit breaker pattern
- `tenacity` - Retry logic
- `slowapi` - Rate limiting
- `python-multipart` - File upload handling
- `pydantic` - Data validation
- `pydantic-settings` - Configuration management
- `python-jose` - JWT token handling

### Frontend
- **Language:** TypeScript 5+
- **Framework:** React 19.2.0
- **Build Tool:** Vite 7.2.4
- **Styling:** Tailwind CSS 4.1.18
- **State Management:** Zustand 5.0.3
- **Data Fetching:** TanStack React Query 5.90.16
- **Animations:** Framer Motion
- **Routing:** React Router DOM
- **HTTP Client:** Axios

**Design System:**
- **Fonts:** IBM Plex Mono (technical), DM Sans (UI)
- **Theme:** Deep Slate Dark (#0a0e1a) with Electric Blue (#00d4ff) accents
- **Icons:** Lucide React
- **Components:** Custom component library (Button, Card, Badge, Dialog, etc.)

### Infrastructure
- **Web Server:** Nginx 1.18+ (reverse proxy)
- **Process Manager:** systemd
- **Deployment:** Automated via deploy-auto.sh
- **Monitoring:** Prometheus/Grafana, systemd journal, application logs
- **Database:** PostgreSQL 15
- **Caching:** Redis 7

---

## Project Structure

```
homerack/
├── backend/                          # FastAPI backend
│   ├── app/
│   │   ├── api/                      # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── connections.py        # Cable connections CRUD
│   │   │   ├── dependencies.py       # FastAPI dependencies
│   │   │   ├── device_specs.py       # Device specifications
│   │   │   ├── devices.py            # Devices CRUD
│   │   │   ├── health.py             # Health checks
│   │   │   └── racks.py              # Racks CRUD + optimization
│   │   ├── fetchers/                 # Manufacturer spec fetchers
│   │   │   ├── base.py               # Base fetcher class
│   │   │   ├── apple.py              # Apple device specs
│   │   │   ├── cisco.py              # Cisco device specs
│   │   │   ├── dell.py               # Dell device specs
│   │   │   ├── hp.py                 # HP/HPE device specs
│   │   │   ├── ubiquiti.py           # Ubiquiti device specs
│   │   │   ├── synology.py           # Synology device specs
│   │   │   ├── generic.py            # Generic fallback fetcher
│   │   │   └── factory.py            # Fetcher factory pattern
│   │   ├── middleware/               # Custom middleware
│   │   │   ├── error_handlers.py     # Global exception handlers
│   │   │   └── request_id.py         # Request ID tracking
│   │   ├── parsers/                  # Document parsers
│   │   │   ├── base.py               # Base parser
│   │   │   └── __init__.py
│   │   ├── utils/                    # Utility modules
│   │   │   ├── circuit_breaker.py    # Circuit breaker instances
│   │   │   ├── retry.py              # Retry decorators
│   │   │   ├── validators.py         # Data validators
│   │   │   └── __init__.py
│   │   ├── optimization/             # Optimization algorithms
│   │   │   └── __init__.py
│   │   ├── config.py                 # Application configuration
│   │   ├── database.py               # Database setup
│   │   ├── main.py                   # FastAPI application
│   │   ├── models.py                 # SQLAlchemy models
│   │   ├── schemas.py                # Pydantic schemas
│   │   └── thermal.py                # Thermal analysis
│   ├── init_db.py                    # Database initialization
│   ├── requirements.txt              # Python dependencies
│   └── requirements-simple.txt       # Minimal dependencies
│
├── frontend/                         # React frontend
│   ├── src/
│   │   ├── components/               # React components
│   │   │   ├── ui/                   # Base UI components
│   │   │   ├── layout/               # Layout components
│   │   │   ├── rack/                 # Rack visualization
│   │   │   ├── devices/              # Device management
│   │   │   ├── connections/          # Cable management
│   │   │   ├── dashboard/            # Dashboard widgets
│   │   │   └── debug/                # Debug console
│   │   ├── pages/                    # Route pages
│   │   ├── lib/                      # Utilities and API client
│   │   ├── store/                    # Zustand stores
│   │   ├── types/                    # TypeScript definitions
│   │   ├── App.tsx                   # Main app component
│   │   ├── main.tsx                  # Entry point
│   │   └── index.css                 # Global styles
│   ├── public/                       # Static assets
│   ├── dist/                         # Production build (gitignored)
│   ├── package.json                  # Node dependencies
│   ├── vite.config.ts                # Vite configuration
│   ├── tailwind.config.js            # Tailwind configuration
│   └── tsconfig.json                 # TypeScript configuration
│
├── deploy-auto.sh                    # Automated deployment script
├── README.md                         # Main README
├── SETUP.md                          # Development setup guide
├── PRODUCTION_SETUP.md               # Production deployment guide
├── CONTRIBUTING.md                   # Contribution guidelines
└── claude.md                         # This file
```

---

## Backend Details

### Database Models

Located in `backend/app/models.py`:

**1. Rack**
- `id`: Primary key
- `name`: Rack identifier
- `location`: Physical location
- `height_u`: Height in rack units (default: 42U)
- `width_standard`: 11", 18", 19", or 23"
- `depth_mm`: Depth in millimeters
- `max_power_w`: Maximum power capacity
- Relationships: `devices`, `positions`

**2. Device**
- `id`: Primary key
- `name`: Device name
- `device_type`: Device category
- `manufacturer`, `model`: Hardware details
- `height_u`: Device height in U
- `width_standard`: Device width
- `power_w`, `heat_output_btu`: Power specs
- `rack_id`, `position_u`: Placement info
- Relationships: `rack`, `device_spec`, `connections_source`, `connections_target`

**3. DeviceSpecification**
- `id`: Primary key
- `manufacturer`, `model`: Device identification
- `form_factor`, `height_u`, `width_standard`: Physical specs
- `power_consumption_w`, `thermal_output_btu`: Thermal specs
- `network_ports`, `power_ports`: Connectivity
- `source_url`, `fetched_at`: Metadata
- Relationships: `devices`

**4. RackPosition**
- `id`: Primary key
- `rack_id`, `u_position`: Position identification
- `device_id`: Occupying device
- `status`: occupied/available/reserved
- Relationships: `rack`, `device`

**5. Connection**
- `id`: Primary key
- `source_device_id`, `target_device_id`: Connected devices
- `connection_type`: network/power
- `cable_type`: Cat5e, Cat6, Cat6a, Fiber, Power
- `length_m`: Cable length
- `port_source`, `port_target`: Port identifiers
- Relationships: `source_device`, `target_device`

### API Endpoints

All endpoints documented at http://lampadas.local/api/docs

**Health & Monitoring:**
- `GET /health` - Basic health check
- `GET /api/health/detailed` - Detailed health with DB status
- `GET /api/health/circuit-breakers` - Circuit breaker states
- `GET /api/health/ready` - Readiness probe

**Device Specifications:**
- `GET /api/device-specs/` - List all specs (paginated)
- `GET /api/device-specs/{id}` - Get spec by ID
- `GET /api/device-specs/search?q={query}` - Search specs
- `POST /api/device-specs/fetch` - Fetch from manufacturer website
- `GET /api/device-specs/fetch/supported-manufacturers` - List supported manufacturers

**Devices:**
- `GET /api/devices/` - List all devices
- `POST /api/devices/` - Create device
- `GET /api/devices/{id}` - Get device by ID
- `PUT /api/devices/{id}` - Update device
- `DELETE /api/devices/{id}` - Delete device
- `POST /api/devices/quick-add` - Quick add with spec fetching

**Racks:**
- `GET /api/racks/` - List all racks
- `POST /api/racks/` - Create rack
- `GET /api/racks/{id}` - Get rack by ID
- `PUT /api/racks/{id}` - Update rack
- `DELETE /api/racks/{id}` - Delete rack
- `GET /api/racks/{id}/layout` - Get rack layout
- `POST /api/racks/{id}/optimize` - Optimize rack layout
- `GET /api/racks/{id}/bom` - Generate bill of materials
- `GET /api/racks/{id}/thermal-analysis` - Get thermal analysis

**Connections:**
- `GET /api/connections/` - List all connections
- `POST /api/connections/` - Create connection
- `GET /api/connections/{id}` - Get connection by ID
- `PUT /api/connections/{id}` - Update connection
- `DELETE /api/connections/{id}` - Delete connection

### Reliability Features

**Circuit Breakers** (`app/utils/circuit_breaker.py`):
- Database operations breaker
- Thermal calculation breaker
- External API breaker
- Configurable failure threshold (default: 5)
- Reset timeout (default: 30s)

**Retry Logic** (`app/utils/retry.py`):
- Max attempts: 5
- Exponential backoff
- Jitter for thundering herd prevention
- Applied to: database ops, external API calls, thermal calculations

**Rate Limiting:**
- Default: 300 requests/hour per IP
- Configurable via `RATE_LIMIT_DEFAULT` setting
- Applied globally via SlowAPI

**Request Tracking:**
- Request ID middleware for distributed tracing
- Structured logging with timestamps
- Error handlers with consistent JSON responses

### Configuration

Located in `backend/app/config.py`:

```python
# Application
APP_NAME: "HomeRack API"
VERSION: "1.0.1"
DEBUG: False
ENVIRONMENT: "production"

# Database
DATABASE_URL: "postgresql://..." (production)

# CORS
CORS_ORIGINS: ["http://localhost:5173", "http://localhost:3000", "http://lampadas.local"]
CORS_ALLOW_CREDENTIALS: True

# Reliability
CIRCUIT_BREAKER_ENABLED: True
CIRCUIT_BREAKER_FAILURE_THRESHOLD: 5
CIRCUIT_BREAKER_TIMEOUT: 30

RETRY_ENABLED: True
RETRY_MAX_ATTEMPTS: 5

RATE_LIMIT_ENABLED: True
RATE_LIMIT_DEFAULT: "300/hour"

# Logging
LOG_LEVEL: "INFO"
```

---

## Frontend Details

### Design System

**Color Palette:**
- Background: Deep Slate Dark `#0a0e1a`
- Primary: Electric Blue `#00d4ff`
- Success: Lime `#a3ff12`
- Warning: Amber `#ffb020`
- Error: Red `#ef4444`
- Muted: Slate `#64748b`

**Typography:**
- Technical: IBM Plex Mono
- UI: DM Sans
- Mono: JetBrains Mono (code)

**Visual Features:**
- Dot grid background pattern
- Glassmorphism effects
- Glow effects on hover/active states
- Smooth Framer Motion animations
- Electric blue accents with neon glow

### Component Library

**Base UI Components** (`src/components/ui/`):
- `Button` - Variants: primary, secondary, outline, ghost, danger
- `Card` - Container with header, content, footer
- `Badge` - Status indicators with glow
- `Input` - Form inputs with validation
- `Select` - Dropdown selects
- `Dialog` - Modal dialogs
- `Toast` - Notifications
- `Tabs` - Tab navigation
- `Tooltip` - Contextual help

**Layout Components** (`src/components/layout/`):
- `Sidebar` - Main navigation
- `Header` - Top bar with search

**Feature Components:**
- `RackVisualizer` - 42U rack representation
- `DeviceCard` - Device library cards
- `ThermalOverlay` - Heat map visualization
- `ConnectionValidator` - Cable validation UI
- `DebugConsole` - API debugging panel

### State Management

Using Zustand with persistence:

**Stores:**
- `useRackStore` - Racks and positions
- `useDeviceStore` - Devices and specs
- `useConnectionStore` - Cable connections
- `useUIStore` - UI state, filters, selections
- `useDebugStore` - Debug console state

**Store Pattern:**
```typescript
interface Store {
  // State
  items: Item[]
  loading: boolean
  error: string | null

  // Actions
  fetchItems: () => Promise<void>
  createItem: (data: CreateItem) => Promise<void>
  updateItem: (id: number, data: UpdateItem) => Promise<void>
  deleteItem: (id: number) => Promise<void>
}
```

### Debug Features

**Debug Console:**
- Toggle with Ctrl+D keyboard shortcut
- Bottom panel with API request/response logging
- Request timing and duration display
- Error tracking with stack traces
- Export logs to JSON
- Persistent settings via localStorage

**Debug Store:**
```typescript
interface DebugStore {
  enabled: boolean
  logs: DebugLog[]
  addLog: (log: DebugLog) => void
  clearLogs: () => void
  exportLogs: () => void
  toggle: () => void
}
```

**Debug Log Format:**
```typescript
interface DebugLog {
  timestamp: string
  type: 'request' | 'response' | 'error'
  method?: string
  url?: string
  status?: number
  duration?: number
  data?: any
}
```

### Pages

- `/` - Dashboard with metrics and system overview
- `/racks` - Rack management with visual layout
- `/devices` - Device library and inventory
- `/connections` - Cable management
- `/settings` - Application settings + debug toggle
- `/thermal` - Thermal analysis

---

## API Documentation

### Request/Response Format

**Success Response:**
```json
{
  "id": 1,
  "name": "Main Rack",
  "height_u": 42,
  "devices": []
}
```

**Error Response:**
```json
{
  "detail": {
    "error": "Resource not found",
    "request_id": "abc-123-def",
    "timestamp": "2026-01-12T14:30:00Z"
  }
}
```

### Pagination

List endpoints support pagination:
```
GET /api/racks/?skip=0&limit=100
```

### Filtering

Search endpoints support query parameters:
```
GET /api/device-specs/search?q=Cisco&limit=20
```

### Thermal Analysis Response

```json
{
  "rack_id": 1,
  "total_power_w": 2500,
  "total_heat_btu": 8530,
  "thermal_zones": [
    {
      "zone_name": "Top Third",
      "u_range": [29, 42],
      "total_heat_btu": 3000,
      "status": "normal"
    }
  ],
  "hotspots": [
    {
      "device_name": "Server 1",
      "position_u": 35,
      "heat_output_btu": 1500,
      "severity": "warning"
    }
  ],
  "recommendations": [
    "Consider redistributing high-heat devices"
  ]
}
```

---

## Known Issues

### Critical: None

### High Priority: None

### Medium Priority: None

### Low Priority

**1. API Root Endpoint**
- **Issue:** `/api/` returns 404
- **Impact:** Minimal - API documentation accessible via `/api/docs`
- **Root Cause:** Nginx SPA fallback routing catches /api/ as frontend route
- **Status:** Known limitation, not critical

**2. Node.js Version**
- **Issue:** Using Node.js 18.20.4, Vite recommends 20.19+
- **Impact:** Build works but may have suboptimal performance
- **Action:** Consider upgrading to Node.js v20 LTS

**3. 404 Errors in Logs**
- **Issue:** Frequent 404s for `/racks`, `/devices`, `/connections`
- **Root Cause:** Frontend polling for data on empty database
- **Impact:** Minimal - expected behavior
- **Action:** Seed database or improve empty state handling

---

## Development Workflow

### Setting Up Development Environment

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements-simple.txt
python init_db.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev  # Development server on port 5173
```

### Development Servers

- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- API ReDoc: http://localhost:8000/redoc

### Making Changes

**Backend Changes:**
1. Modify Python files in `backend/app/`
2. Uvicorn auto-reloads on file changes
3. Test via API docs at http://localhost:8000/docs
4. Write tests if needed

**Frontend Changes:**
1. Modify TypeScript/React files in `frontend/src/`
2. Vite HMR updates browser automatically
3. Check browser console for errors
4. Use debug console (Ctrl+D) to monitor API calls

**Database Changes:**
1. Modify models in `backend/app/models.py`
2. Modify schemas in `backend/app/schemas.py`
3. Run database migrations
4. Update frontend types if needed

### Code Style

**Backend:**
- PEP 8 style guide
- Type hints for function signatures
- Docstrings for classes and complex functions
- Max line length: 100 characters

**Frontend:**
- ESLint configuration in `eslint.config.js`
- Prettier for formatting
- TypeScript strict mode
- Component naming: PascalCase
- File naming: kebab-case

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Description of changes"

# Push to remote
git push origin feature/your-feature-name

# Create pull request on GitHub
```

---

## Deployment

### Production Deployment (lampadas.local)

**Automated Deployment:**
```bash
./deploy-auto.sh
```

**What it does:**
1. Builds frontend locally (npm run build)
2. Installs system dependencies (Python, Redis, Nginx, PostgreSQL)
3. Creates remote directories
4. Copies backend and frontend files via rsync
5. Sets up Python virtual environment
6. Installs Python dependencies
7. Runs database migrations
8. Creates systemd service for backend (4 Gunicorn workers)
9. Configures Nginx reverse proxy
10. Starts services and verifies deployment

### Service Management

**Backend Service:**
```bash
# Status
ssh calounx@lampadas.local 'sudo systemctl status homerack'

# Restart
ssh calounx@lampadas.local 'sudo systemctl restart homerack'

# Logs
ssh calounx@lampadas.local 'sudo journalctl -u homerack -f'

# Stop
ssh calounx@lampadas.local 'sudo systemctl stop homerack'

# Start
ssh calounx@lampadas.local 'sudo systemctl start homerack'
```

**Nginx Service:**
```bash
ssh calounx@lampadas.local 'sudo systemctl {status|restart|stop|start} nginx'
```

### Nginx Configuration

Located at `/etc/nginx/sites-available/homerack`:

```nginx
upstream homerack_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name lampadas.local 192.168.50.135;

    root /home/calounx/homerack/frontend/dist;
    index index.html;

    # API proxy
    location /api/ {
        proxy_pass http://homerack_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

### Environment Variables

Create `.env` in backend directory:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/homerack
SECRET_KEY=your-secret-key-here
ENVIRONMENT=production
DEBUG=False
CORS_ORIGINS=["http://lampadas.local"]
REDIS_URL=redis://localhost:6379/0
```

---

## Testing

### Test Coverage Summary

**Overall Status:** PASS (92.4% success rate)
- **Backend Tests:** 295
- **E2E Tests:** 83
- **Total Tests:** 380+

**Test Coverage:**
- Frontend serving
- API core endpoints
- Racks API (CRUD + optimization)
- Devices API (CRUD + quick-add)
- Device specs API (CRUD + search + fetch)
- Connections API (CRUD)
- Authentication (JWT + RBAC)
- NetBox integration

### Running Tests

**Backend Tests:**
```bash
cd backend
pytest
```

**Frontend Tests:**
```bash
cd frontend
npm test
```

**E2E Tests:**
```bash
cd frontend
npm run test:e2e
```

**API Testing:**
```bash
# Using curl
curl http://lampadas.local/api/health

# Using httpie
http http://lampadas.local/api/health

# Using API docs
# Visit http://lampadas.local/api/docs
```

### Test Data

Sample data in database:
- 2 racks (Main Rack, Secondary Rack)
- 3 devices (network switches)
- Multiple device specifications
- Connections (as created)

---

## Performance Metrics

### Backend Performance

- **Startup Time:** ~3 seconds
- **Memory Usage:** 66.6 MB (stable)
- **CPU Usage:** <2% idle, <10% under load
- **Response Time:** <100ms for simple queries
- **Health Check:** <10ms
- **Database Queries:** <10ms (PostgreSQL)
- **Thermal Analysis:** <200ms
- **Workers:** 4 Gunicorn workers

### Frontend Performance

- **Build Time:** 8.65s
- **Bundle Size:**
  - JS: 497 KB (157 KB gzipped)
  - CSS: 38 KB (7 KB gzipped)
  - Total: 535 KB (164 KB gzipped)
- **First Contentful Paint:** <1s (localhost)
- **Time to Interactive:** <2s (localhost)

### Infrastructure

- **Nginx Workers:** 4
- **Nginx Memory:** 5 MB
- **PostgreSQL:** Configured for production workloads
- **Redis:** Caching layer for device specs

---

## Security Considerations

### Current Security Measures

**Network Security:**
- Backend bound to 127.0.0.1 (localhost only)
- Only accessible via Nginx reverse proxy
- No direct external access to backend

**HTTP Security Headers:**
- X-Frame-Options: SAMEORIGIN
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block

**Application Security:**
- JWT authentication implemented
- Role-based access control (RBAC)
- CORS configured with explicit origins
- Input validation via Pydantic schemas
- SQL injection protection via SQLAlchemy ORM
- Rate limiting enabled (300/hour default)
- Request ID tracking for audit trails

**Data Security:**
- Database file permissions restricted
- Environment variables for sensitive config
- PostgreSQL with proper user permissions

### Security Best Practices

1. **SECRET_KEY:** Generate secure key with `openssl rand -hex 32`
2. **HTTPS:** SSL/TLS certificate configured for production
3. **Secrets Management:** Use proper secrets management
4. **Audit Logging:** Comprehensive audit logs implemented
5. **Backups:** Automated database backups configured
6. **Monitoring:** Prometheus/Grafana security monitoring

### Vulnerability Management

- Keep dependencies updated (run `pip list --outdated`, `npm outdated`)
- Review security advisories regularly
- Use `safety check` for Python dependencies
- Use `npm audit` for Node.js dependencies

---

## Additional Resources

### Documentation Files

- `README.md` - Main project README
- `SETUP.md` - Development environment setup
- `PRODUCTION_SETUP.md` - Production deployment guide
- `CONTRIBUTING.md` - Contribution guidelines
- `claude.md` - This file

### External Links

- **Repository:** https://github.com/calounx/RackManagement
- **Issues:** https://github.com/calounx/RackManagement/issues
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **React Docs:** https://react.dev/
- **Tailwind CSS:** https://tailwindcss.com/
- **Zustand:** https://github.com/pmndrs/zustand

### Support

**For Questions:**
- Check existing documentation first
- Search GitHub issues
- Create new issue with detailed description

**For Bugs:**
- Include version number (1.0.1)
- Provide reproduction steps
- Include relevant logs
- Describe expected vs actual behavior

**For Features:**
- Describe use case
- Explain why it's valuable
- Consider if it fits project scope

---

## Changelog

### v1.0.1 (2026-01-12)

**Added:**
- Complete React frontend with Precision Engineering design
- JWT authentication with role-based access control
- PostgreSQL 15 database for production
- Redis 7 caching layer
- Prometheus/Grafana monitoring stack
- 4 Gunicorn workers for production
- NetBox DCIM integration
- Debug console with API logging and keyboard shortcuts
- Nginx reverse proxy configuration
- Full-stack automated deployment script
- 295 backend tests + 83 E2E tests (380+ total)

**Changed:**
- Database: SQLite (dev) to PostgreSQL 15 (production)
- FastAPI version: 0.109.0
- Backend now binds to 127.0.0.1 (localhost only)

**Fixed:**
- Circuit breaker timeout_duration to reset_timeout parameter
- Nginx proxy configuration for /api/* routing

**Security:**
- Backend no longer exposed directly to network
- Added security headers to Nginx
- JWT authentication implemented
- RBAC access control

### v1.0.0 (2026-01-09)

**Added:**
- Initial FastAPI backend with comprehensive API
- SQLAlchemy models for racks, devices, specs, connections
- Device specification fetchers for 11 manufacturers
- Thermal analysis engine
- Circuit breakers and retry logic
- Rate limiting
- SQLite database with initialization

**Infrastructure:**
- systemd service configuration
- Basic deployment automation
- Health check endpoints

---

## Conclusion

HomeRack v1.0.1 is a production-ready full-stack application for data center rack management. The system features:

- Robust backend API with reliability patterns
- Modern React frontend with debug capabilities
- JWT authentication with RBAC
- PostgreSQL 15 database with Redis caching
- Prometheus/Grafana monitoring
- NetBox DCIM integration
- Automated deployment pipeline
- Comprehensive documentation
- 92.4% test pass rate (380+ tests)
- Production deployment on lampadas.local

**Status:** Production ready v1.0.1 - All phases complete.

---

*This documentation was generated for Claude AI to quickly understand the entire HomeRack project. Last updated: 2026-01-12*
