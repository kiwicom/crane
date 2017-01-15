# crane

A GitLab CI ready image for Rancher upgrades.

## How to use

- Deploy your application on Rancher manually
- Get a Rancher API key
  - click the `API` button in the environment your app is in, then `Add Environment API key`
  - name it `gitlab/group/project deployment`, or similar
- Add the secret key as a secret variable in the project (`RANCHER_SECRET_KEY`)
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
  RANCHER_URL: https://example.com/
  RANCHER_ACCESS_KEY: 9vQ4fcpn4Kfuvjxkcpc9PoudImzxoj6pQxa
  RANCHER_PROJECT_ID: 1a81
  RANCHER_SERVICE_ID: 1s1456

[...]

production:
  stage: deploy
  image: registry.skypicker.com:5005/simone/crane
  variables:
    GIT_STRATEGY: none
  script:
    - crane --new-image $TEST_IMAGE
  when: manual
```

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
