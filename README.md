# Quantum Resonance Clean

**Pi Forge Quantum Genesis** - A clean installation framework for quantum resonance applications

## Overview

This repository provides a clean, production-ready setup for the Pi Forge Quantum Genesis project. It includes automated installation scripts, Docker support, and comprehensive documentation to get you started quickly.

## Features

- 🚀 **Automated Installation**: One-command setup for both Linux/Mac and Windows
- 🐳 **Docker Support**: Containerized deployment with Docker and Docker Compose
- 📦 **Dependency Management**: Pre-configured Python dependencies
- ⚙️ **Environment Configuration**: Template-based configuration system
- 📚 **Comprehensive Documentation**: Clear setup and usage instructions

## Prerequisites

- **Python 3.8+** (3.11 recommended)
- **pip** (Python package manager)
- **Git** (for version control)
- **Docker** (optional, for containerized deployment)

## Quick Start

### Linux / macOS

```bash
# Clone the repository
git clone https://github.com/onenoly1010/quantum-resonance-clean.git
cd quantum-resonance-clean

# Run the installation script
chmod +x install.sh
./install.sh

# Configure your environment
nano .env  # Edit with your Supabase credentials

# Activate virtual environment
source .venv/bin/activate

# Start the application
uvicorn server.main:app --reload
```

### Windows (PowerShell)

```powershell
# Clone the repository
git clone https://github.com/onenoly1010/quantum-resonance-clean.git
cd quantum-resonance-clean

# Run the installation script
.\install.ps1

# Configure your environment
notepad .env  # Edit with your Supabase credentials

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Start the application
uvicorn server.main:app --reload
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or use Docker directly
docker build -t quantum-resonance .
docker run -p 8000:8000 --env-file .env quantum-resonance
```

## Manual Installation

If you prefer manual installation:

1. **Create virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\Activate.ps1  # Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Create project directories**:
   ```bash
   mkdir -p server frontend docs
   ```

## Configuration

Edit the `.env` file to configure your application:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

## Project Structure

```
quantum-resonance-clean/
├── server/           # Backend server code
├── frontend/         # Frontend application
├── docs/             # Documentation
├── .env.example      # Environment template
├── .gitignore        # Git ignore rules
├── requirements.txt  # Python dependencies
├── install.sh        # Linux/Mac installation script
├── install.ps1       # Windows installation script
├── Dockerfile        # Docker configuration
├── docker-compose.yml # Docker Compose configuration
└── README.md         # This file
```

## Development

### Running the Server

```bash
# Development mode with auto-reload
uvicorn server.main:app --reload

# Production mode
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

### Access the Application

Once running, access the application at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Dependencies

Core dependencies include:
- **FastAPI**: Modern web framework for building APIs
- **Uvicorn**: ASGI server implementation
- **Supabase**: Backend as a Service platform
- **Python-dotenv**: Environment variable management

See `requirements.txt` for complete list.

## Troubleshooting

### Python Version Issues
Ensure you have Python 3.8 or higher:
```bash
python3 --version
```

### Virtual Environment Not Activating
Make sure you're in the project directory and run:
```bash
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\Activate.ps1  # Windows
```

### Port Already in Use
If port 8000 is occupied, specify a different port:
```bash
uvicorn server.main:app --port 8001
```

### Supabase Connection Issues
Verify your `.env` file has correct Supabase credentials:
- Check SUPABASE_URL format
- Verify SUPABASE_KEY is the anon/public key

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is part of the Pi Forge Quantum Genesis initiative.

## Support

For issues and questions:
- Create an issue on GitHub
- Check existing documentation in the `docs/` folder

## Acknowledgments

Built as part of the Pi Forge Quantum Genesis project by Kris Olofson.
# Pi Forge Quantum Genesis

This repository contains the Pi Forge Quantum Genesis web project. The backend code lives in `server/` and the frontend assets are in `frontend/`.

## Setup

1.  **Install Python:** Make sure you have Python 3.11 or higher installed and added to your system's PATH.

2.  **Create a virtual environment:**
    ```powershell
    python -m venv .venv
    ```

3.  **Activate the virtual environment:**
    -   On Windows (PowerShell):
        ```powershell
        .\.venv\Scripts\Activate.ps1
        ```

4.  **Install dependencies:**
    ```powershell
    pip install -r server/requirements.txt
    ```

## Running the Application (local)

Run the ASGI server with uvicorn (recommended):

```powershell
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
```

The application will be available at `http://127.0.0.1:8000`.

### Health Check

Check the health endpoint (if available) at `http://127.0.0.1:8000/health`.

Notes:
- This README no longer references a `backend/` directory — the backend lives under `server/`.
- For containerized deployment, see the `Dockerfile` in the repo root.
