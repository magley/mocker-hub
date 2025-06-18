#!/bin/sh

echo "RUN_TESTS: $RUN_TESTS"  # Debugging line

if [ ! -f "/code/certs/cert.pem" ]; then
  echo "cert.pem not found..."

  if [ -f "/code/certs/certs.zip" ]; then
    echo "certs.zip found. Extracting certificates..."
    7z e /code/certs/certs.zip -o/code/certs/ -y
    echo "Certificates extracted."
  else
    echo "Neither cert.pem nor certs.zip found!"
    exit 1
  fi
fi

if [ "$RUN_TESTS" = "true" ]; then
  echo "Running tests..."
  ls -l
  mocker_hub_TEST_ENV=1 pytest /code/app/tests -s --maxfail=1 --disable-warnings --tb=short

  if [ $? -eq 0 ]; then
    echo "Tests passed successfully!"
    exit 0
  else
    echo "Tests failed!"
    exit 1
  fi
else
  echo "Starting FastAPI app..."
  fastapi run app/api/main.py --port 8000 --proxy-headers
fi