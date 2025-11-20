#!/bin/bash
# Project initialization script

set -e

echo "🚀 Arcana Cloud Python - Project Initialization"
echo "================================================"

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing production dependencies..."
pip install -r requirements.txt

echo "📚 Installing development dependencies..."
pip install -r requirements-dev.txt

# Create .env file
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created, please edit configuration"
else
    echo "✓ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p uploads
mkdir -p /tmp/uploads

echo ""
echo "✅ Project initialization complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file, configure database and Redis"
echo "2. Start MySQL and Redis services"
echo "3. Initialize database: flask db upgrade"
echo "4. Run application: python wsgi.py"
echo ""
echo "🐳 Or use Docker:"
echo "docker-compose up -d"
echo ""
