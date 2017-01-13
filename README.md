# crane

A GitLab CI ready image for Rancher upgrades.

## Environment variables and command flags

| CLI flag           | Environment variable     | Required           | Default |
| ------------------ | ------------------------ | ------------------ | ------- |
| `--rancher-url`    | `RANCHER_URL`            | :white_check_mark: |         |
| `--access`         | `RANCHER_ACCESS_KEY`     | :white_check_mark: |         |
| `--secret`         | `RANCHER_SECRET_KEY`     | :white_check_mark: |         |
| `--project`        | `RANCHER_PROJECT_ID`     | :white_check_mark: |         |
| `--service`        | `RANCHER_SERVICE_ID`     | :white_check_mark: |         |
| `--new-image`      | `RANCHER_SERVICE_IMAGE`  | :x:                | None    |
| `--batch-size`     | `RANCHER_BATCH_SIZE`     | :x:                | 1       |
| `--batch-interval` | `RANCHER_BATCH_INTERVAL` | :x:                | 2       |
| `--start-first`    | `RANCHER_START_FIRST`    | :x:                | False   |
| `--sidekick`       | `RANCHER_SIDEKICK_NAME`  | :x:                | None    |
