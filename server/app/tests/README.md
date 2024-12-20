## Running the tests

1) Position yourself to the root of this repository. We need to do this because of ./volume-server-cfg.

```sh
user:.../mocker-hub/server/app/tests$ cd ../../../
user:.../mocker-hub$
```

2) Run the tests. `-s` is to show stdout from `print()`.

```sh
mocker_hub_TEST_ENV=1 pytest server/app/tests/ -s
```