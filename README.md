# crane

A GitLab CI ready image for Rancher upgrades.

## How to use

- Deploy your application on Rancher manually
- Get a Rancher API key
  - click the `API` button in the environment your app is in, then `Add Environment API key`
  - name it `gitlab/group/project deployment`, or similar
- Add the secret key as a secret variable in the project (`RANCHER_SECRET_KEY`)
  - add the `RANCHER_URL`, `RANCHER_ACCESS_KEY`, `RANCHER_PROJECT_ID`, `RANCHER_SERVICE_ID` either in secret variables, or `.gitlab-ci.yml`
  - <https://gitlab.skypicker.com/group/project/variables>
- Go to your application on Rancher, and note the Project ID / Service ID variables in the URL
  - Example URL: <https://example.com/env/1a81/apps/stacks/1e551/services/1s1456/containers>
    - Project ID: `1a81`, environment ID, starts with `1a`
    - Service ID: `1s1456`, starts with `1s`
- Edit `.gitlab-ci.yml`


```
stages:
 [...]
 - deploy

variables:
  TEST_IMAGE: $CI_REGISTRY_IMAGE:$CI_BUILD_REF
  RANCHER_URL: https://example.com/                         # Change to the Rancher URL
  RANCHER_ACCESS_KEY: 9vQ4fcpn4Kfuvjxkcpc9PoudImzxoj6pQxa   # Change to your Rancher access key
  RANCHER_PROJECT_ID: 1a81                                  # Change to the Project ID of your app
  RANCHER_SERVICE_ID: 1s1456                                # Change to the Service ID of your app

[...]

production:
  stage: deploy
  image: registry.skypicker.com:5005/simone/crane
  variables:
    GIT_STRATEGY: none
  script:
    - crane --new-image $TEST_IMAGE
  environment:
    name: production
    url: https://your-app.example.com/                      # Change to the URL of your app, or remove if none
  when: manual
```

## Environment variables and command flags

| CLI flag                | Environment variable        | Required | Default |
| ----------------------- | --------------------------- | -------- | ------- |
| `--rancher-url`         | `RANCHER_URL`               | Yes      |         |
| `--access`              | `RANCHER_ACCESS_KEY`        | Yes      |         |
| `--secret`              | `RANCHER_SECRET_KEY`        | Yes      |         |
| `--project`             | `RANCHER_PROJECT_ID`        | Yes      |         |
| `--service`             | `RANCHER_SERVICE_ID`        | Yes      |         |
| `--new-image`           | `RANCHER_SERVICE_IMAGE`     | No       | None    |
| `--batch-size`          | `RANCHER_BATCH_SIZE`        | No       | 1       |
| `--batch-interval`      | `RANCHER_BATCH_INTERVAL`    | No       | 2       |
| `--start-first`         | `RANCHER_START_FIRST`       | No       | False   |
| `--sidekick`            | `RANCHER_SIDEKICK_NAME`     | No       | None    |
| `--sleep-after-upgrade` | `CRANE_SLEEP_AFTER_UPGRADE` | No       | 60      |
