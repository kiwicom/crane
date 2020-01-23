package main

import (
	"fmt"
	"log"
	"os"

	"github.com/urfave/cli/v2"
)

var deployFlags = []cli.Flag{
	&cli.IntFlag{
		Name:    "batch-size",
		Value:   1,
		Usage:   "containers to upgrade at once",
		EnvVars: []string{"CRANE_BATCH_SIZE"},
	},
	&cli.IntFlag{
		Name:    "batch-interval",
		Value:   2,
		Usage:   "seconds to wait between batches",
		EnvVars: []string{"CRANE_BATCH_INTERVAL"},
	},
	&cli.BoolFlag{
		Name:    "start-first",
		Value:   false,
		Usage:   "start new containers before stopping old",
		EnvVars: []string{"CRANE_START_FIRST"},
	},
	&cli.StringFlag{
		Name:    "old-commit",
		Usage:   "commit hash we are upgrading from",
		EnvVars: []string{"CRANE_OLD_COMMIT"},
	},
	&cli.StringFlag{
		Name:    "new-commit",
		Usage:   "commit hash to upgrade to",
		EnvVars: []string{"CRANE_NEW_COMMIT", "CI_COMMIT_SHA"},
	},
	&cli.StringFlag{
		Name:    "new-image",
		Usage:   "image URL to upgrade to",
		EnvVars: []string{"CRANE_NEW_IMAGE"},
	},
	&cli.IntFlag{
		Name:    "sleep-after-upgrade",
		Value:   0,
		Usage:   "seconds to wait after upgrade",
		EnvVars: []string{"CRANE_SLEEP_AFTER_UPGRADE"},
	},
	&cli.BoolFlag{
		Name:    "manual-finish",
		Value:   false,
		Usage:   "skip automatic upgrade finish",
		EnvVars: []string{"CRANE_MANUAL_FINISH"},
	},

	// Rancher options
	&cli.StringFlag{
		Name:     "rancher-url",
		EnvVars:  []string{"RANCHER_URL"},
		Required: true,
		Usage:    "Rancher API URL",
		// TODO: callback=strip_trailing_slash
	},
	&cli.StringFlag{
		Name:     "rancher-access-key",
		EnvVars:  []string{"RANCHER_ACCESS_KEY"},
		Required: true,
		Usage:    "Rancher access key",
	},
	&cli.StringFlag{
		Name:     "rancher-secret-key",
		EnvVars:  []string{"RANCHER_SECRET_KEY"},
		Required: true,
		Usage:    "Rancher secret key",
	},
	&cli.StringFlag{
		Name:     "rancher-env",
		EnvVars:  []string{"RANCHER_ENV_ID"},
		Required: true,
		Usage:    "ID of environment to operate in",
	},
	&cli.StringFlag{
		Name:    "rancher-stack",
		EnvVars: []string{"RANCHER_STACK_NAME", "CI_PROJECT_NAME"},
		Usage:   "stack to upgrade",
	},
	&cli.StringSliceFlag{
		Name:    "rancher-service",
		EnvVars: []string{"RANCHER_SERVICE_NAME"},
		Value:   cli.NewStringSlice("app"),
		Usage:   "services to upgrade",
	},
	&cli.StringFlag{
		Name:    "rancher-sidekick",
		EnvVars: []string{"RANCHER_SIDEKICK_NAME"},
		Usage:   "sidekick to use instead of primary service",
	},
}

var announceFlags = []cli.Flag{
	&cli.StringFlag{
		Name:    "slack-token",
		Usage:   "Slack API token",
		EnvVars: []string{"CRANE_SLACK_TOKEN"},
	},
	&cli.StringSliceFlag{
		Name:    "slack-channel",
		Usage:   "Slack channel to announce in",
		EnvVars: []string{"CRANE_SLACK_CHANNEL"},
	},
	&cli.StringSliceFlag{
		Name:    "slack-link",
		Usage:   "links to mention in Slack",
		EnvVars: []string{"CRANE_SLACK_LINK"},
		// TODO: type=(str, str)
	},
	&cli.StringFlag{
		Name:    "sentry-webhook",
		Usage:   "Sentry release webhook URL",
		EnvVars: []string{"CRANE_SENTRY_WEBHOOK"},
		// TODO: callback=strip_trailing_slash
	},
	&cli.StringSliceFlag{
		Name:    "webhook-url",
		Usage:   "URLs to POST the release status to",
		EnvVars: []string{"CRANE_WEBHOOK_URL"},
		// TODO:  callback=strip_trailing_slash
	},
	&cli.StringFlag{
		Name:    "webhook-token",
		Usage:   "auth token for webhooks",
		EnvVars: []string{"CRANE_WEBHOOK_TOKEN"},
	},
	&cli.StringFlag{
		Name:    "datadog-key",
		Usage:   "key for posting release events",
		EnvVars: []string{"CRANE_DATADOG_KEY"},
	},
}

func main() {
	app := &cli.App{
		Name:    "A CI deploy assistant",
		Usage:   "crane communicates your deployments to your team",
		Version: "4.0.0",
		Commands: []*cli.Command{
			{
				Name:  "deploy",
				Usage: "manage both upgrading the services and announcing the deployment",
				Action: func(c *cli.Context) error {
					fmt.Println("Not implemented yet.")
					return nil
				},
				Flags: deployFlags,
			},
			{
				Name:  "announce",
				Usage: "announce releases while managing upgrading the app yourself",
				Flags: announceFlags,
				Subcommands: []*cli.Command{
					{
						Name:  "start",
						Usage: "start announcement of the deployment",
						Action: func(c *cli.Context) error {
							fmt.Println("start")
							return nil
						},
					},
					{
						Name:  "success",
						Usage: "finish announcement with success",
						Action: func(c *cli.Context) error {
							fmt.Println("finish with success")
							return nil
						},
					},
					{
						Name:  "failure",
						Usage: "finish announcement with failure",
						Action: func(c *cli.Context) error {
							fmt.Println("finish with failure")
							return nil
						},
					},
				},
			},
		},
	}

	err := app.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}
