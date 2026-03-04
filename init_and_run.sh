#!/bin/bash

echo "Waiting for SQL Server to be ready..."
until /opt/mssql-tools/bin/sqlcmd -S $DB_HOST -U $DB_USER -P $DB_PASSWORD -Q "SELECT 1" > /dev/null 2>&1
do
  echo -n "."
  sleep 2
done

echo ""
echo "SQL Server is ready, running init script..."

# Chạy file sql tạo db + bảng
/opt/mssql-tools/bin/sqlcmd -S $DB_HOST -U $DB_USER -P $DB_PASSWORD -i /initdb/Law_ChatBot_DB.sql

echo "Database initialized."

# Chạy FastAPI app
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
