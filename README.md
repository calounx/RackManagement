# RackManagement - Network Rack Optimization System

[![GitHub](https://img.shields.io/badge/github-calounx%2FRackManagement-blue?logo=github)](https://github.com/calounx/RackManagement)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128.0-green.svg)](https://fastapi.tiangolo.com/)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

A comprehensive web application for optimizing network device placement in server racks, featuring automatic device specification fetching, intelligent placement optimization, and cable bill of materials generation.

**🌐 Live Demo**: [API Docs](http://lampadas.local:8000/docs) (if accessible on your network)

## Features

- **Automatic Device Spec Fetching**: Enter brand + model, system fetches specifications from manufacturer websites
- **Multi-Width Rack Support**: 11", 18", 19", and 23" racks with compatibility validation
- **Intelligent Optimization**: Optimizes for cable management, weight distribution, thermal management, and access frequency
- **Cable BOM Generation**: Automatic cable length calculation and component list generation
- **Web-Based UI**: Modern React interface with drag-and-drop rack designer

## Technology Stack

- **Backend**: FastAPI (Python 3.11+), SQLAlchemy, Redis
- **Frontend**: React + TypeScript, TailwindCSS, Vite
- **Database**: SQLite (development), PostgreSQL-ready
- **Web Scraping**: BeautifulSoup4, pdfplumber, httpx

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Redis (optional, for caching)

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements-simple.txt

# Initialize database
python init_db.py

# Run development server
uvicorn app.main:app --reload
```

API will be available at: http://localhost:8000
API docs at: http://localhost:8000/docs

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

UI will be available at: http://localhost:5173

## Project Structure

```
homerack/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── fetchers/       # Web scraping for device specs
│   │   ├── parsers/        # HTML/PDF parsers
│   │   ├── optimization/   # Optimization algorithms
│   │   ├── models.py       # Database models
│   │   └── main.py         # FastAPI app
│   └── requirements.txt
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API client
│   │   └── types/          # TypeScript types
│   └── package.json
└── README.md
```

## Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

### End-to-End Testing

See [verification section in plan](/home/calounx/.claude/plans/clever-tickling-spark.md#verification--testing)

## API Endpoints

- `GET /` - API root
- `GET /health` - Health check
- `POST /api/device-specs/fetch` - Fetch device specs from web
- `GET /api/device-specs/search` - Search cached specs
- `POST /api/devices/quick-add` - Quick add devices
- `POST /api/racks/{id}/optimize` - Optimize rack layout
- `GET /api/racks/{id}/bom` - Generate bill of materials

Full API documentation: http://localhost:8000/docs

## Development Status

Current implementation phase: **Phase 1 - Backend Foundation**

- [x] Project structure
- [x] Database models
- [ ] Web fetching system
- [ ] Optimization engine
- [ ] Frontend UI

See [implementation plan](https://github.com/calounx/RackManagement/blob/main/DEPLOYMENT.md) for complete roadmap.

## Documentation

- [Setup Guide](SETUP.md) - Development environment setup
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [API Test Report](API_TEST_REPORT.md) - Test results and metrics
- [Contributing Guide](CONTRIBUTING.md) - How to contribute

## Repository

- **GitHub**: [https://github.com/calounx/RackManagement](https://github.com/calounx/RackManagement)
- **Issues**: [https://github.com/calounx/RackManagement/issues](https://github.com/calounx/RackManagement/issues)
- **Author**: [calounx](https://github.com/calounx)

## License

MIT License - see [LICENSE](LICENSE) file for details

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) before submitting PRs.

### Quick Contribution Steps
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

**Built with ❤️ using FastAPI, React, and Claude AI**
