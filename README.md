# HomeRack - Network Rack Optimization System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![Status](https://img.shields.io/badge/status-production--ready-success.svg)]()
[![Version](https://img.shields.io/badge/version-1.0.1-blue.svg)]()

A comprehensive web application for optimizing network device placement in server racks, featuring automatic device specification fetching from 13+ brands, intelligent multi-objective optimization, thermal analysis, and cable bill of materials generation.

## Features

### Device Management
- **Automatic Device Spec Fetching**: Enter brand + model, system fetches specifications from manufacturer websites (supports 13+ brands)
- **Wikipedia Integration**: Automatic device information enrichment from Wikipedia
- **Brand/Model Catalog**: Complete catalog management with logo uploads
- **Multi-Width Rack Support**: 11", 18", 19", and 23" racks with compatibility validation

### Optimization & Analysis
- **Multi-Objective Optimization**: Optimizes for thermal management, power distribution, cable routing, and access frequency
- **Thermal Analysis**: Heat distribution visualization with configurable parameters
- **Cable BOM Generation**: Automatic cable length calculation and component list generation

### Integration & Security
- **NetBox DCIM Integration**: Sync with NetBox for data center infrastructure management
- **JWT Authentication**: Secure authentication with role-based access control (RBAC)
- **Full Monitoring Stack**: Prometheus metrics and Grafana dashboards

### User Interface
- **Modern React 19 Frontend**: Responsive design with TailwindCSS 4
- **Interactive Rack Designer**: Visual rack layout with drag-and-drop support
- **Real-time Updates**: Live optimization feedback and status updates

## Technology Stack

### Backend
- **Framework**: FastAPI 0.109
- **Language**: Python 3.11+
- **ORM**: SQLAlchemy 2.0
- **Database**: PostgreSQL 15
- **Caching**: Redis 7
- **Web Scraping**: BeautifulSoup4, pdfplumber, httpx

### Frontend
- **Framework**: React 19
- **Language**: TypeScript
- **Build Tool**: Vite 7
- **Styling**: TailwindCSS 4

### Infrastructure
- **Containerization**: Docker with Docker Compose
- **Reverse Proxy**: Nginx
- **Monitoring**: Prometheus + Grafana
- **Authentication**: JWT with RBAC

### Testing
- **Backend**: pytest (295 tests)
- **E2E**: Playwright (83 tests)
- **Total**: 380+ tests at 92.4% pass rate

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (production) or SQLite (development)
- Redis 7+ (optional for development, required for production)
- Docker and Docker Compose (for containerized deployment)

### Development Setup

#### Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Run development server
uvicorn app.main:app --reload
```

API available at: http://localhost:8000
API documentation: http://localhost:8000/docs

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

UI available at: http://localhost:5173

### Production Deployment

For production deployment with PostgreSQL, Redis, authentication, and monitoring, see [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md).

## Project Structure

```
homerack/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── fetchers/       # Web scraping for device specs (13+ brands)
│   │   ├── parsers/        # HTML/PDF parsers
│   │   ├── optimization/   # Multi-objective optimization algorithms
│   │   ├── thermal/        # Thermal analysis engine
│   │   ├── auth/           # JWT authentication and RBAC
│   │   ├── models.py       # Database models
│   │   └── main.py         # FastAPI application
│   ├── tests/              # pytest test suite (295 tests)
│   └── requirements.txt
├── frontend/                # React 19 frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API client
│   │   └── types/          # TypeScript types
│   ├── e2e/                # Playwright E2E tests (83 tests)
│   └── package.json
├── docker/                  # Docker configuration
├── monitoring/              # Prometheus/Grafana configuration
└── README.md
```

## API Endpoints

### Core Endpoints
- `GET /health` - Health check with dependency status
- `POST /api/auth/login` - JWT authentication
- `POST /api/auth/register` - User registration

### Device Management
- `POST /api/device-specs/fetch` - Fetch device specs from manufacturer
- `GET /api/device-specs/search` - Search cached specifications
- `POST /api/devices/quick-add` - Quick add devices to rack

### Rack Operations
- `POST /api/racks/{id}/optimize` - Run multi-objective optimization
- `GET /api/racks/{id}/thermal` - Get thermal analysis
- `GET /api/racks/{id}/bom` - Generate cable bill of materials

### Catalog Management
- `GET /api/brands` - List all brands
- `POST /api/brands/{id}/logo` - Upload brand logo
- `GET /api/models` - List device models

Full API documentation available at `/docs` when running the server.

## Testing

### Backend Tests

```bash
cd backend
source venv/bin/activate
pytest
```

### Frontend E2E Tests

```bash
cd frontend
npx playwright test
```

### Full Test Suite

```bash
# Run all tests
cd backend && pytest && cd ../frontend && npx playwright test
```

## Documentation

- [SETUP.md](SETUP.md) - Development environment setup
- [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md) - Production deployment guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) before submitting PRs.

### Quick Contribution Steps

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Production Ready v1.0.1** - Built with FastAPI, React 19, and Claude AI
