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