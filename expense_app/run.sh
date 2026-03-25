#!/usr/bin/env bash
set -e

echo ""
echo "╔══════════════════════════════════════╗"
echo "║        ExpenseIQ — Setup             ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Check Python 3
if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3 is required. Install from https://python.org"
  exit 1
fi

PYTHON=$(command -v python3)
echo "✓ Python: $($PYTHON --version)"

# Create virtualenv if missing
if [ ! -d "venv" ]; then
  echo "→ Creating virtual environment..."
  $PYTHON -m venv venv
fi

# Activate
source venv/bin/activate
echo "✓ Virtual environment activated"

# Install deps
echo "→ Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✓ Dependencies installed"

# Seed demo data
if [ ! -f "instance/expense_manager.db" ]; then
  echo "→ Setting up database and seeding demo data..."
  python3 seed_data.py
else
  echo "✓ Database already exists"
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  🚀 ExpenseIQ is ready!                              ║"
echo "║                                                      ║"
echo "║  Open your browser: http://localhost:5000            ║"
echo "║                                                      ║"
echo "║  Demo login:  demo@example.com / demo1234            ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Launch Flask
FLASK_APP=app.py FLASK_ENV=development python3 app.py
