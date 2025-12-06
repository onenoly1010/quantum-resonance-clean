"""
Pi Forge Quantum Genesis - Main Application Entry Point
A clean installation framework for quantum resonance applications
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI application
app = FastAPI(
    title="Quantum Resonance API",
    description="Pi Forge Quantum Genesis - Quantum Resonance Application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "online",
        "message": "Quantum Resonance API is running",
        "version": "1.0.0",
        "project": "Pi Forge Quantum Genesis"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "supabase_url_configured": bool(os.getenv("SUPABASE_URL"))
    }

@app.get("/api/info")
async def api_info():
    """API information endpoint"""
    return {
        "api": "Quantum Resonance",
        "version": "1.0.0",
        "endpoints": [route.path for route in app.routes]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port, reload=True)
