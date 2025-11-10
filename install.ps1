# Pi Forge Quantum Genesis - Clean Installation Script (Windows)
# This script sets up the development environment for the Quantum Resonance project

Write-Host "🚀 Starting Pi Forge Quantum Genesis Clean Installation..." -ForegroundColor Cyan
Write-Host ""

# Check if Python 3.8+ is installed
Write-Host "🔍 Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Found $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python 3 is not installed. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}
Write-Host ""

# Create virtual environment
Write-Host "🐍 Creating Python virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "⚠️  Virtual environment already exists. Skipping creation." -ForegroundColor Yellow
} else {
    python -m venv .venv
    Write-Host "✅ Virtual environment created." -ForegroundColor Green
}
Write-Host ""

# Activate virtual environment
Write-Host "🔌 Activating virtual environment..." -ForegroundColor Yellow
& .venv\Scripts\Activate.ps1
Write-Host "✅ Virtual environment activated." -ForegroundColor Green
Write-Host ""

# Upgrade pip
Write-Host "📦 Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host "✅ pip upgraded." -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "📚 Installing Python dependencies..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
    Write-Host "✅ Dependencies installed successfully." -ForegroundColor Green
} else {
    Write-Host "⚠️  requirements.txt not found. Skipping dependency installation." -ForegroundColor Yellow
}
Write-Host ""

# Create .env file from example if it doesn't exist
Write-Host "⚙️  Setting up environment configuration..." -ForegroundColor Yellow
if (-Not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item .env.example .env
        Write-Host "✅ Created .env file from .env.example" -ForegroundColor Green
        Write-Host "⚠️  Please edit .env file with your Supabase credentials before running the application." -ForegroundColor Yellow
    } else {
        Write-Host "⚠️  .env.example not found. Please create .env file manually." -ForegroundColor Yellow
    }
} else {
    Write-Host "ℹ️  .env file already exists." -ForegroundColor Cyan
}
Write-Host ""

# Create necessary directories
Write-Host "📁 Creating project directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "server" | Out-Null
New-Item -ItemType Directory -Force -Path "frontend" | Out-Null
New-Item -ItemType Directory -Force -Path "docs" | Out-Null
Write-Host "✅ Directories created." -ForegroundColor Green
Write-Host ""

Write-Host "✨ Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Edit .env file with your Supabase credentials"
Write-Host "   2. Activate virtual environment: .venv\Scripts\Activate.ps1"
Write-Host "   3. Run the application: uvicorn server.main:app --reload"
Write-Host ""
Write-Host "🎉 Happy coding!" -ForegroundColor Green
