#!/bin/sh

echo "Starting FastAPI app..."
fastapi run app/api/main.py --port 8000 --proxy-headers