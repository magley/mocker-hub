#!/bin/sh

echo "Starting FastAPI app..."
fastapi run app/api/main.py --port 8000 --proxy-headers


# if [ "$RUN_TESTS" = "true" ]; then
#   echo "Running tests..."
#   pytest --maxfail=1 --disable-warnings --tb=short

#   if [ $? -eq 0 ]; then
#     echo "Tests passed successfully!"
#   else
#     echo "Tests failed!"
#     exit 1
#   fi
# else
#   echo "Starting FastAPI app..."
#   fastapi run app/api/main.py --port 8000 --proxy-headers
# fi