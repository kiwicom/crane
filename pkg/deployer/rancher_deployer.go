package deployer

import (
	"errors"
	"os"
	"strings"
	"time"

	"regexp"

	"github.com/kiwicom/crane/internal/commit"
	"github.com/kiwicom/crane/internal/rancher"
	log "github.com/sirupsen/logrus"
)

var (
	ErrCreatingRancherApiService  = errors.New("Error creating rancher api service!")
	ErrExpectedRancherContextType = errors.New("Expected RancherContext but got something I do not understand!")
	ErrDeployFailed               = errors.New("I failed running deploy!")
	ErrLimitedDeploy              = errors.New("Crane is running in limited mode")
)

type deployer struct {
	api        rancher.RancherApi
	settings   rancher.Json
	newVersion string
	oldVersion string
	repo       commit.CommitsGetter
	limited    bool
}

type timeouts struct {
	WaitTimeout time.Duration
	FailTimeout int
}

type option func(*deployer) error

func WithRancherApi(api rancher.RancherApi) option {
	return func(d *deployer) error {
		d.api = api
		return nil
	}
}

func WithSettings(settings rancher.Json) option {
	return func(d *deployer) error {
		d.settings = settings
		return nil
	}
}

func WithCommitsGetter(commitsGetter commit.CommitsGetter) option {
	return func(d *deployer) error {
		d.repo = commitsGetter
		return nil
	}
}

func New(opts ...option) (*deployer, error) {
	rd := deployer{
		newVersion: "",
		oldVersion: "",
		limited:    false,
	}

	for _, opt := range opts {
		err := opt(&rd)
		if err != nil {
			return nil, err
		}
	}

	return &rd, nil
}

func (d *deployer) Deploy() error {
	stack, err := d.getStack()
	if err != nil {
		return err
	}

	services, err := d.getServices(stack)
	if err != nil {
		return err
	}

	err = d.checkPreconditions(services)
	if err == ErrLimitedDeploy {
		log.WithFields(log.Fields{
			"api_call": "deployer.Deploy",
			"emote":    ":(",
		}).Warn("Oops! Some preconditions are not met. Working in limited mode")
		d.limited = true
	}

	if err == ErrDeployFailed {
		log.WithFields(log.Fields{
			"api_call": "deployer.Deploy",
			"emote":    ":(",
		}).Error("Yikes! Some preconditions failed! Check the logs for details!")

		return err
	}

	json, err := d.getJson(services[0])
	if err != nil {
		return err
	}

	oldImage := json["launchConfig"].(rancher.Json)["imageUuid"].(string)
	err = d.getVersions(oldImage)
	if err != nil {
		log.WithError(err).Error("Oops! Something went wrong while fetching versions!")
		return ErrDeployFailed
	}

	err = d.startUpgrade(services)
	if err != nil {
		return err
	}

	tmt := timeouts{
		WaitTimeout: 60 * time.Second,
		FailTimeout: 20,
	}
	if v, ok := d.settings["wait_timeout"]; ok {
		tmt.WaitTimeout = time.Duration(v.(int)) * time.Second
	}
	if v, ok := d.settings["fail_timeout"]; ok {
		tmt.FailTimeout = v.(int)
	}

	err = d.waitForUpgrade(services, tmt)

	if err != nil {
		return err
	}

	return d.finishUpgrade(services)
}

func (d *deployer) checkPreconditions(services []rancher.Service) error {
	_, err := d.repo.GetHead(os.Getenv("CI_PROJECT_DIR"))

	if err != nil {
		log.WithError(err).
			WithFields(log.Fields{
				"api_call": "deployer.checkPreconditions",
				"repo":     os.Getenv("CI_PROJECT_DIR"),
			}).Error("You are not running crane in a Git repository. " +
			"crane is running in limited mode, all hooks have been disabled. " +
			"It is highly recommended you use Git references for your deployments")
		return ErrLimitedDeploy
	}

	_, err = d.newCommit()
	if err != nil {
		log.WithError(err).
			WithFields(log.Fields{}).Errorf("The new version you specified, %s is not a valid git reference! "+
			"crane is running in limited mode, all hooks have been disabled. "+
			"It is highly recommended you use Git references for your deployments.", d.newVersion)
		return ErrLimitedDeploy
	}

	for _, service := range services {
		jsR, err := d.api.GetEntity(service)
		if err != nil {
			log.WithError(err).
				Errorf("Yikes! I could not query service %s", service.Name)
			return ErrLimitedDeploy
		}

		imageUuid := jsR["launchConfig"].(rancher.Json)["imageUuid"].(string)

		_, ok := d.settings["new_image"]
		if !strings.Contains(imageUuid, d.oldVersion) && !ok {
			log.WithFields(log.Fields{
				"api_call": "deployer.checkPreconditions",
				"service":  service,
			}).Error("All selected services must have the same commit SHA. " +
				"Please manually change their versions so they are all the same, and then retry the upgrade.")

			return ErrDeployFailed
		}
	}
	return nil
}

func (d *deployer) commits() ([]commit.Commit, error) {
	var result []commit.Commit

	isd, err := d.isDisconnected()
	if err != nil {
		return nil, err
	}

	isrb, err := d.isRollback()
	if err != nil {
		return nil, err
	}

	if isd {
		nc, err := d.newCommit()
		if err != nil {
			return nil, err
		}
		result = append(result, nc)
	} else if d.isRedeploy() {
		return []commit.Commit{}, nil
	} else if isrb {
		return d.repo.GetCommits(os.Getenv("CI_PROJECT_DIR"), d.newVersion, d.oldVersion)
	}

	return result, nil
}

func (d *deployer) isRollback() (bool, error) {
	nc, err := d.newCommit()
	oc, err := d.oldCommit()

	if err != nil {
		log.WithError(err).
			Errorf("Doh! I can't calculate if this is a rollback with commits %s and %s",
				d.oldVersion, d.newVersion)
		return false, err
	}
	return nc.At.Before(oc.At), nil
}

func (d *deployer) isRedeploy() bool {
	return d.oldVersion == d.newVersion
}

func (d *deployer) isDisconnected() (bool, error) {
	result, err := d.repo.IsAncestor(os.Getenv("CI_PROJECT_DIR"), d.oldVersion, d.newVersion)
	if err != nil {
		log.WithError(err).Errorf("Yikes! I can't determine of %s and %s commit are ancestors", d.oldVersion, d.newVersion)
		return false, err
	}
	return !result, nil
}

func (d *deployer) newCommit() (commit.Commit, error) {
	c, err := d.repo.GetSingle(os.Getenv("CI_PROJECT_DIR"), d.newVersion)
	if err != nil {
		log.WithFields(log.Fields{
			"api_call":   "deployer.newCommit",
			"commit_sha": d.newVersion,
		}).Errorf("Yikes! Could not fetch commit with hash %s", d.newVersion)
		return commit.Commit{}, err
	}

	return c, nil
}

func (d *deployer) oldCommit() (commit.Commit, error) {
	c, err := d.repo.GetSingle(os.Getenv("CI_PROJECT_DIR"), d.oldVersion)
	if err != nil {
		log.WithFields(log.Fields{
			"api_call":   "deployer.oldCommit",
			"commit_sha": d.oldVersion,
		}).Errorf("Yikes! Could not fetch commit with hash %s", d.oldVersion)
		return commit.Commit{}, err
	}

	return c, nil
}

func (d *deployer) getStack() (rancher.Stack, error) {
	env, ok := d.settings["env"]
	if !ok {
		log.WithFields(log.Fields{
			"api_call": "deployer.getStack",
			"settings": d.settings,
		}).Errorf("OooOps! Env not found in settings %v", d.settings)
		return rancher.Stack{}, ErrDeployFailed
	}

	stk, ok := d.settings["stack"]
	if !ok {
		log.WithFields(log.Fields{
			"api_call": "deployer.getStack",
			"settings": d.settings,
		}).Errorf("OooOps! Stack not found in settings %v", d.settings)
		return rancher.Stack{}, ErrDeployFailed
	}

	stack, err := d.api.GetStackFromName(env.(string), stk.(string))
	if err != nil {
		log.WithFields(log.Fields{
			"api_call": "rancherDeployer.Deploy",
			"env":      d.settings["env"].(string),
			"stack":    d.settings["stack"].(string),
		}).Error("Yikes! I could not find that stack!")

		return rancher.Stack{}, ErrDeployFailed
	}

	return stack, nil
}

func (d *deployer) getServices(stack rancher.Stack) ([]rancher.Service, error) {
	var services []rancher.Service
	for _, service := range d.settings["services"].(rancher.JsonArray) {
		s, err := d.api.GetServiceFromName(stack, service.(string))
		if err != nil {
			log.WithFields(log.Fields{
				"api_call": "rancherDeployer.Deploy",
				"stack":    stack,
				"service":  service,
			}).Errorf("Oops! Could not get service %s", service)

			return nil, ErrDeployFailed
		}

		services = append(services, s)
	}

	return services, nil
}

func (d *deployer) getJson(service rancher.Service) (rancher.Json, error) {
	json, err := d.api.GetEntity(service)
	if err != nil {
		log.WithFields(log.Fields{
			"api_call": "rancherDeployer.Deploy",
			"service":  service,
		}).Errorf("Doh! I could not find service %s", service.Name)

		return nil, ErrDeployFailed
	}

	return json, nil
}

func (d *deployer) getVersions(oldImage string) error {
	oldVersion := ""
	newVersion := ""
	if v, ok := d.settings["new_image"]; ok {
		oc := strings.Split(oldImage, ":")
		oldVersion = oc[len(oc)-1]

		nc := strings.Split(v.(string), ":")
		newVersion = nc[len(nc)-1]
	} else {
		re := regexp.MustCompile("[0-9a-f]{40}")
		matches := re.FindAllString(oldImage, -1)

		if matches == nil {
			oc := strings.Split(oldImage, ":")
			tag := oc[len(oc)-1]
			log.WithFields(log.Fields{
				"api_call":  "deployer.Deploy",
				"old_image": oldImage,
			}).Errorf("Your existing image seems to habe no commit hash in its tag "+
				"for me to be able to upgrade to the new commit, "+
				"but it's currently tagged as just %s", tag)

			return ErrDeployFailed
		} else if len(matches) > 1 {
			log.WithFields(log.Fields{
				"api_call": "deployer.Deploy",
				"matches":  matches,
			}).Errorf("Your existing image seems to have multiple commit hashes in its tag, "+
				"I don't know which one to replace, %#v !", matches)

			return ErrDeployFailed
		}
		oldVersion = matches[0]
		newVersion = d.settings["new_commit"].(string)

	}

	d.newVersion = newVersion
	d.oldVersion = oldVersion

	return nil
}

func (d *deployer) startUpgrade(services []rancher.Service) error {
	for _, service := range services {
		_, err := d.api.UpgradeService(service, d.oldVersion, d.newVersion, d.settings)
		if err != nil {
			log.WithFields(log.Fields{
				"api_call": "deployer.startUpgrade",
				"service":  service,
			}).Errorf("Oops! I couldn't upgrade service %s", service.Name)
			return ErrDeployFailed
		}
	}
	return nil
}

func (d *deployer) waitForUpgrade(services []rancher.Service, tmt timeouts) error {
	c := make(chan error, 1)

	go func() {
		fails := 0
		done := make(map[rancher.Service]struct{})
		all := make(map[rancher.Service]struct{})
		exists := struct{}{}

		for _, service := range services {
			all[service] = exists
		}
		for len(done) != len(all) {
			if fails >= tmt.FailTimeout {
				log.WithFields(log.Fields{
					"api_call": "deployer.waitForUpgrade",
				}).Error("Yikes! Maximum number of failures fetching upgrade status reached")
				c <- ErrDeployFailed
				return
			}
			time.Sleep(3 * time.Second)
			for _, service := range services {
				if v, ok := done[service]; ok && v == exists {
					continue
				}
				j, err := d.getJson(service)
				if err != nil {
					log.WithFields(log.Fields{
						"api_call": "deployer.waitForUpgrade",
						"service":  service,
					}).Errorf("Doh! Couldn't retrieve service info %s", service.Name)
					fails = fails + 1
					continue
				}
				state := j["state"].(string)
				if state != "upgrading" {
					log.WithFields(log.Fields{
						"api_call": "deployer.waitForUpgrade",
						"service":  service,
					}).Infof("Rancher says %s is now '%s'", service.Name, state)
					if state != "upgraded" {
						log.WithFields(log.Fields{
							"api_call": "deployer.waitForUpgrade",
							"service":  service,
						}).Errorf("But I don't know what %s's '%s' means!"+
							" Please fix it for me (´;︵;`)", service.Name, state)
						fails = fails + 1
						continue
					}
					done[service] = exists
				}
			}
		}
		c <- nil
	}()

	select {
	case res := <-c:
		return res
	case <-time.After(tmt.WaitTimeout):
		log.WithFields(log.Fields{
			"api_call": "deployer.waitForUpgrade",
			"timeout":  tmt.WaitTimeout,
		}).Errorf("Doh! Bailed out after timeout expired %v", tmt.WaitTimeout)
		return ErrDeployFailed
	}

	return nil
}

func (d *deployer) finishUpgrade(services []rancher.Service) error {
	if v, ok := d.settings["sleep_after_upgrade"]; ok {
		sau := v.(int)
		d := time.Duration(sau) * time.Second
		time.Sleep(d)
	}
	if v, ok := d.settings["manual_finish"]; (ok && v.(bool) == false) || !ok {
		for _, service := range services {
			err := d.api.FinishUpgradeService(service)
			if err != nil {
				log.WithFields(log.Fields{
					"api_call": "deployer.finishUpgrade",
					"service":  service,
				}).Errorf("Yikes! Couldn't finish upgrading service %s", service.Name)
				return ErrDeployFailed
			}
		}
	}

	return nil
}
