#!/bin/bash
# Build script for deployment

echo "📦 Building Worker Management System..."

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Initialize database
echo "🗄️  Initializing database..."
python run.py init_db

# Create static directories if needed
mkdir -p instance
mkdir -p app/static/css
mkdir -p app/static/js

echo "✅ Build completed successfully!"
echo "🚀 Ready for deployment!"
