#!/bin/bash
# Setup script for LLM Analysis Quiz project (Linux/Mac)

echo "========================================"
echo "LLM Analysis Quiz - Setup Script"
echo "========================================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

echo "[1/5] Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create virtual environment"
    exit 1
fi

echo "[2/5] Activating virtual environment..."
source venv/bin/activate

echo "[3/5] Installing Python dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo "[4/5] Installing Playwright browsers..."
playwright install chromium
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install Playwright browsers"
    exit 1
fi

echo "[5/5] Setting up environment file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "========================================"
    echo "IMPORTANT: Configure your .env file"
    echo "========================================"
    echo "Please edit .env and add:"
    echo "  - STUDENT_EMAIL"
    echo "  - STUDENT_SECRET"
    echo "  - OPENAI_API_KEY"
    echo ""
else
    echo ".env file already exists, skipping..."
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Run: uvicorn app:app --reload"
echo "3. Test: python test_endpoint.py"
echo ""
