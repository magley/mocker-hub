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

And then `docker compose up --build`.

When you're done testing, remove the ENV variable.

---
---
---
---
## Old (TODO: Remove)

1) Position yourself to the root of this repository. We need to do this because of ./volume-server-cfg.

```sh
user:.../mocker-hub/server/app/tests$ cd ../../../
user:.../mocker-hub$
```

2) Run the tests. `-s` is to show stdout from `print()`.

```sh
mocker_hub_TEST_ENV=1 pytest server/app/tests/ -s
```