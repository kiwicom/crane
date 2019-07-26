# crane

[![Python: 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://python.org)
[![Code style: black](https://img.shields.io/badge/code%20style-black-black.svg)](https://github.com/ambv/black)
[![Discord](https://img.shields.io/discord/427417507276783616.svg)](https://discord.gg/AtwevVQ)
[![Gitlab pipeline status (branch)](https://img.shields.io/gitlab/pipeline/kiwicom/crane/master.svg)](https://gitlab.com/kiwicom/crane/pipelines)

![crane logo - an origami crane](logo.png)

A GitLab CI deploy assistant. Crane communicates your deployments to your team. And it knows how to deploy to some places, too.
See the [origin story on our blog at code.kiwi.com](https://code.kiwi.com/announcing-crane-e8ce911b187b)!

**Crane can announce to:** Slack, Datadog, Sentry, and Generic webhooks

**Crane can deploy to:** Rancher 1.x, or you can bring your own deploy script

## Installation

Crane is meant to run in GitLab CI jobs,
since it gathers lots of context from the GitLab CI environment.

This means there's no installation step:
you use Crane by just creating a CI job with `image: kiwicom/crane:4.0.0`.

## Usage

### `crane announce`

If you want Crane to announce releases
while managing upgrading the app yourself,
your job should be configured something like this:

```yaml
image: kiwicom/crane:4.0.0
variables:
  CRANE_SLACK_TOKEN: xoxp-1234-6789
  CRANE_SLACK_CHANNEL: releases
script:
  - export CRANE_OLD_COMMIT=${./scripts/get_old_tag.sh}
  - crane announce start
  - ./scripts/deploy.sh && crane announce success || crane announce failure
```

- `./scripts/get_old_tag.sh` is a placeholder for code that gets the commit SHA running pre-deploy
- `./scripts/deploy.sh` is a placeholder for code that deploys your code
- Only announcing to Slack is configured here,
  but you could set any and all other targets as well
- The Slack token should actually be set as a secret variable in CI settings

### `crane deploy`

If you want Crane to manage both upgrading the services
and announcing the deployment,
you should use `crane deploy`.
To do this, your job should look like this:

```yaml
image: kiwicom/crane:4.0.0
variables:
  RANCHER_URL: https://rancher.party
  RANCHER_ENV_ID: 1a234
  RANCHER_ACCESS_KEY: secret
  RANCHER_SECRET_KEY: very-very-secret
script:
  - crane deploy rancher1
```

- Before the first run, you need to deploy your app manually
- The API keys, of course, should be set as secret variables in CI settings
- The `RANCHER_ENV_ID` can be seen in the URL.
  In the example URL `https://rancher.example.com/env/1a81/apps/stacks/1e551/services/1s1456/containers`
  the environment ID is `1a81`.

## Configuration

### Global

| CLI flag                | Environment variable        | Required | Default                |
| ----------------------- | --------------------------- | -------- | ---------------------- |
| `--old-commit`          | `CRANE_OLD_COMMIT`          | No       | (Fetched from Rancher) |
| `--new-commit`          | `CRANE_NEW_COMMIT`          | No       | `$CI_COMMIT_SHA`       |
| `--new-image`           | `CRANE_NEW_IMAGE`           | No       | None                   |
| `--batch-size`          | `CRANE_BATCH_SIZE`          | No       | 1                      |
| `--batch-interval`      | `CRANE_BATCH_INTERVAL`      | No       | 2                      |
| `--start-first`         | `CRANE_START_FIRST`         | No       | False                  |
| `--sleep-after-upgrade` | `CRANE_SLEEP_AFTER_UPGRADE` | No       | 0                      |
| `--manual-finish`       | `CRANE_MANUAL_FINISH`       | No       | False                  |

### For Rancher 1.x upgrades

| CLI flag               | Environment variable    | Required | Default            |
| ---------------------- | ----------------------- | -------- | ------------------ |
| `--rancher-url`        | `RANCHER_URL`           | Yes      |                    |
| `--rancher-access-key` | `RANCHER_ACCESS_KEY`    | Yes      |                    |
| `--rancher-secret-key` | `RANCHER_SECRET_KEY`    | Yes      |                    |
| `--rancher-env`        | `RANCHER_ENV_ID`        | Yes      |                    |
| `--rancher-stack`      | `RANCHER_STACK_NAME`    | No       | `$CI_PROJECT_NAME` |
| `--rancher-service`    | `RANCHER_SERVICE_NAME`  | No       | app                |
| `--rancher-sidekick`   | `RANCHER_SIDEKICK_NAME` | No       | None               |

### For Slack announcements

When `--slack-token` is set,
crane will post an announcement to `--slack-channel`
with details about the ongoing deployment.
You can use `--slack-link` to add useful URLs to this announcements
such as Datadog dashboards, Sentry issues, or the project repository.

| CLI flag          | Environment variable  | Details                      |
| ----------------- | --------------------- | ---------------------------- |
| `--slack-token`   | `CRANE_SLACK_TOKEN`   | Slack API token              |
| `--slack-channel` | `CRANE_SLACK_CHANNEL` | Slack channel to announce in |
| `--slack-link`    | `CRANE_SLACK_LINK`    | links to mention in Slack    |

### For Sentry reporting

With `--sentry-webhook`, crane can post release details to Sentry.
[Release tracking](https://docs.sentry.io/learn/releases/#what-is-a-release) is useful
to provide additional context to errors tracked in Sentry.

| CLI flag           | Environment variable   | Details                    |
| ------------------ | ---------------------- | -------------------------- |
| `--sentry-webhook` | `CRANE_SENTRY_WEBHOOK` | Sentry release webhook URL |

### For Datadog reporting

If you set an API key with `--datadog-key`,
Crane will post successful and failed releases to your Datadog event feed.
These events can then be marked on charts and displayed on dashboards.

| CLI flag        | Environment variable | Details                      |
| --------------- | -------------------- | ---------------------------- |
| `--datadog-key` | `CRANE_DATADOG_KEY`  | URLs to post release info to |

### For generic webhook reporting

With the `--webhook-url` option,
you can specify URLs that crane will send release info to,
in its own format.
One use for this is for analytics;
if somebody sets up a listener for these events,
they'll have the data needed to identify correlations
between releases and changes in user behavior or sales numbers.

| CLI flag          | Environment variable  | Details                      |
| ----------------- | --------------------- | ---------------------------- |
| `--webhook-url`   | `CRANE_WEBHOOK_URL`   | URLs to post release info to |
| `--webhook-token` | `CRANE_WEBHOOK_TOKEN` | Auth token for webhooks      |
