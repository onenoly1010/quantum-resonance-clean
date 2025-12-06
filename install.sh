#!/bin/bash

# Pi Forge Quantum Genesis - Clean Installation Script
# This script sets up the development environment for the Quantum Resonance project

set -e  # Exit on error

echo "🚀 Starting Pi Forge Quantum Genesis Clean Installation..."
echo ""

# Check if Python 3.8+ is installed
echo "🔍 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✅ Found Python $PYTHON_VERSION"
echo ""

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
if [ -d ".venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping creation."
else
    python3 -m venv .venv
    echo "✅ Virtual environment created."
fi
echo ""

# Activate virtual environment

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip
echo "✅ pip upgraded."
echo ""

# Install dependencies
echo "📚 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Dependencies installed successfully."
else
    echo "⚠️  requirements.txt not found. Skipping dependency installation."
fi
echo ""

# Create .env file from example if it doesn't exist
echo "⚙️  Setting up environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file from .env.example"
        echo "⚠️  Please edit .env file with your Supabase credentials before running the application."
    else
        echo "⚠️  .env.example not found. Please create .env file manually."
    fi
else
    echo "ℹ️  .env file already exists."
fi
echo ""

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p server
mkdir -p frontend
mkdir -p docs
echo "✅ Directories created."
echo ""

echo "✨ Installation complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit .env file with your Supabase credentials"
echo "   2. Activate virtual environment: source .venv/bin/activate"
echo "   3. Run the application: uvicorn server.main:app --reload"
echo ""
echo "🎉 Happy coding!"
