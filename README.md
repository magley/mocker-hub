# mocker-hub

## Getting started

Build and run:

```sh
docker compose up --watch --build
```

Run without rebuilding (in case Dockerfile hasn't changed):

```sh
docker compose up --watch
```

You can access the server through at [localhost:8000](http://localhost:8000/docs).

You can access the database manager at [localhost:8002](http://localhost:8002). Check `compose.yaml` for the login credentials.