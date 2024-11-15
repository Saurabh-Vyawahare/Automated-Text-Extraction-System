#!/bin/bash
set -e

# Set the default Airflow database connection string to PostgreSQL
export AIRFLOW_DATABASESQL_ALCHEMY_CONN=${AIRFLOWDATABASE_SQL_ALCHEMY_CONN:-postgresql+psycopg2://airflow:airflow@postgres:5432/airflow}

# Check if the first argument is "webserver"
if [ "$1" = "webserver" ]; then
    echo "Initializing Airflow database..."

    # Initialize the Airflow database
    airflow db init || echo "Airflow DB already initialized"

    echo "Creating Airflow admin user if not already created..."

    # Check if the admin user already exists
    if ! airflow users list | grep -q "admin"; then
        airflow users create \
            --username admin \
            --password admin \
            --firstname Admin \
            --lastname User \
            --role Admin \
            --email admin@example.com
    else
        echo "Admin user already exists."
    fi
fi

# Correctly pass the webserver command to airflow
exec airflow "$@"