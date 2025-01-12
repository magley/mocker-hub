## Running the tests

To run tests, do
```sh
RUN_TESTS=true docker compose up --build
```

However, I've been having issues with this on WSL,
so instead I've created an `.env` in project root:

```sh
RUN_TESTS=true
```

Build the container:

```sh
# --abort-on-container-exit will exit as soon as backend exits
# --exit-code-from backend will return backend's exit code
#
# We need this in CI/CD.

docker compose up --build backend --abort-on-container-exit --exit-code-from backend
```

When you're done testing and want to run MockerHub regularly, remove the ENV variable.