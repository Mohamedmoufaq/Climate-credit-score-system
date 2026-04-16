#!/bin/bash
set -e

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating default locations..."
python manage.py shell << EOF
from core.views import seed_default_locations
seed_default_locations()
print("Default locations seeded successfully")
EOF

echo "Build complete!"
