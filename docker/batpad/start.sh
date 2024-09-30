#!/bin/bash

until PGPASSWORD=$POSTGRES_PASSWORD psql -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\q"; do
  echo "Waiting for database to be ready..."
  sleep 5
done


python /app/manage.py migrate
python /app/manage.py runserver 0.0.0.0:8000
