#!/bin/bash

# Set database configuration variables
DB_NAME="xscraper"
DB_USER="xscraper"
DB_PASSWORD="obviouslynotthepassword"
DB_PORT=5432

# Remove existing PostgreSQL container (if any)
docker stop postgres-dev || true
docker rm postgres-dev || true

# Start a new PostgreSQL container
docker run -d --name postgres-dev \
  -e POSTGRES_DB=$DB_NAME \
  -e POSTGRES_USER=$DB_USER \
  -e POSTGRES_PASSWORD=$DB_PASSWORD \
  -p $DB_PORT:5432 \
  postgres:latest

# Wait for the database to be ready
sleep 5

# Create the database and grant privileges to the user
docker exec -it postgres-dev psql -U $DB_USER -c "CREATE DATABASE $DB_NAME;"
docker exec -it postgres-dev psql -U $DB_USER -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo "PostgreSQL development database setup completed successfully!"