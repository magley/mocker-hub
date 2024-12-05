# server

This is the main API server.

## Getting started

Requires Python 3.10 (version 3.11 and possibly newer will not work due to issues with `aioredis` and `fastapi-cache`).

1) Install the required packages: `pip install -r server/requirements.txt`
2) Run the development server: `fastapi dev server/api/main.py`
3) Check the CLI for the server IP address and the auto-generated OpenAPI docs