# Getting Started

Welcome to the Pi Forge Quantum Genesis project!

## Installation

Follow the instructions in the main README.md for installation.

## First Steps

1. **Configure Environment**: Edit the `.env` file with your Supabase credentials
2. **Start the Server**: Run `uvicorn server.main:app --reload`
3. **Access the API**: Navigate to http://localhost:8000/docs

## API Endpoints

### Health Check
```
GET /health
```

Returns the health status of the application.

### API Information
```
GET /api/info
```

Returns information about available API endpoints.

## Development Guide

### Project Structure
- `server/`: Backend FastAPI application
- `frontend/`: Frontend application (to be implemented)
- `docs/`: Documentation files

### Adding New Endpoints

1. Open `server/main.py`
2. Add your endpoint using FastAPI decorators
3. Test using the interactive docs at `/docs`

## Troubleshooting

See the main README.md for common issues and solutions.
