# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## 1.0.0 - 2017-10-11

Complete project rewrite, but backwards compatibility with 0.x should be retained.

### Added

- A hooks/plugin system, which can be used to easily extend crane with code.
  - Sentry, Slack, and generic webhook hooks are included.

### Changed

- Output is now way more readable, and makes use of the hook system
  - And also includes cute emoticons
- Upgrade of multiple services now happens in parallel
- Failures are handled a bit more gracefully

### Deprecated

Some 0.x options and environment variables are still supported
but have been renamed and will be removed within the next few weeks.
Please pin to the `kiwicom/crane:1` image
if you don't want to update your configuration.

- `--rancher-url` renamed to `--url`
- `--access` renamed to `--access-key`
- `--secret` renamed to `--secret-key`
- `--project` renamed to `--env`
- `--no-finish-upgrade` renamed to `--manual-finish`
- `RANCHER_PROJECT_ID` renamed to `RANCHER_ENV_ID`
- `RANCHER_SERVICE_ID` renamed to `RANCHER_SERVICE_NAME`
- `RANCHER_BATCH_SIZE` renamed to `CRANE_BATCH_SIZE`
- `RANCHER_BATCH_INTERVAL` renamed to `CRANE_BATCH_INTERVAL`
- `RANCHER_START_FIRST` renamed to `CRANE_START_FIRST`
- `RANCHER_SERVICE_IMAGE` renamed to `CRANE_NEW_IMAGE`
- `CRANE_NO_FINISH_UPGRADE` renamed to `CRANE_MANUAL_FINISH`
