#!/usr/bin/env bash
set -euo pipefail

echo "Starting PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

echo "Creating database user and database..."
sudo -u postgres psql -c "CREATE USER ssot WITH PASSWORD 'password';" 2>&1 || echo "User may already exist"
sudo -u postgres psql -c "CREATE DATABASE ssot OWNER ssot;" 2>&1 || echo "Database may already exist"

echo "PostgreSQL setup complete"
