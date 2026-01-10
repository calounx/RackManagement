# HomeRack Setup Guide

## Option 1: Docker (Recommended for Testing)

The easiest way to get started is using Docker Compose:

```bash
# Start all services
docker-compose up

# The API will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

This will:
- Start the FastAPI backend on port 8000
- Start Redis for caching on port 6379
- Initialize the database automatically

## Option 2: Local Development

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher (for frontend)
- Redis (optional, for caching)

### Backend Setup

```bash
cd backend

# Install Python venv package (if needed)
# Ubuntu/Debian: sudo apt install python3.11-venv
# macOS: brew install python@3.11

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Run development server
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

### Frontend Setup (Coming Soon)

```bash
cd frontend
npm install
npm run dev
```

## Testing the API

### Using the Interactive Docs

Visit http://localhost:8000/docs for the interactive API documentation powered by Swagger UI.

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Get API info
curl http://localhost:8000/
```

## Environment Variables

Create a `.env` file in the backend directory:

```bash
DATABASE_URL=sqlite:///./homerack.db
REDIS_URL=redis://localhost:6379
```

## Troubleshooting

### Python venv not available

```bash
# Ubuntu/Debian
sudo apt install python3.11-venv

# macOS (via Homebrew)
brew install python@3.11
```

### Redis not running

Redis is optional for development. The app will work without it but caching will be disabled.

To install Redis:
```bash
# Ubuntu/Debian
sudo apt install redis-server

# macOS
brew install redis
brew services start redis

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### Database initialization fails

Make sure you're in the backend directory and the virtual environment is activated:

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python init_db.py
```

## Next Steps

1. Start the backend server
2. Visit http://localhost:8000/docs to explore the API
3. Try the device specification search endpoints
4. Test the rack optimization features

See README.md for full documentation.
