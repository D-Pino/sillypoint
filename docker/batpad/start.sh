#!/bin/bash

# We only rely on sillypoint for now (not odata)
until PGPASSWORD=$SILLYPOINT_DB_PASSWORD psql -h db_sillypoint -U "$SILLYPOINT_DB_USER" -d "$SILLYPOINT_DB_NAME" -c "\q"; do
  echo "Waiting for database to be ready..."
  sleep 5
done


python /app/manage.py migrate
python /app/manage.py runserver 0.0.0.0:8000
