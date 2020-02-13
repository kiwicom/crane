package rancher

import (
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"

	"encoding/json"
	"strings"

	log "github.com/sirupsen/logrus"
)

var (
	ErrUpgradeFailed       = errors.New("Upgrade failed!")
	ErrFinishUpgradeFailed = errors.New("Finish upgrade failed!")
	ErrCreatingRequest     = errors.New("Error creating request!")
	ErrFetchStack          = errors.New("Error fetching stack")
	ErrJsonResponseDecode  = errors.New("Error decoding json response!")
	ErrStackNotFound       = errors.New("Error fetching stack!")
	ErrFetchService        = errors.New("Error fetching service!")
	ErrFetchEntity         = errors.New("Error fetching entity!")
	ErrEncodingRequest     = errors.New("Error encoding request!")
	ErrDecodingResponse    = errors.New("Error decoding response!")
)

type Json = map[string]interface{}
type JsonArray = []interface{}
type JsonObject = interface{}

type RancherAuth struct {
	SecretKey string
	AccessKey string
}

type RancherApi interface {
    GetEntity(entity EntityUrl) (Json, error)
    GetStackFromName(env, name string) (Stack, error)
    GetServiceFromName(stack Stack, name string) (Service, error)
    UpgradeService(service Service, oldVersion, newVersion string, cli_params Json) (Json, error)
    FinishUpgradeService(service Service) error
}

type RancherApiService struct {
	rancherUrl string
	auth       RancherAuth
	client     *http.Client
}

func New(rancherUrl string, auth RancherAuth, client *http.Client) (*RancherApiService, error) {
	if client == nil {
		return &RancherApiService{rancherUrl, auth, http.DefaultClient}, nil
	}

	return &RancherApiService{rancherUrl, auth, client}, nil
}

func (ss *RancherApiService) GetEntity(entity EntityUrl) (Json, error) {
	req, err := ss.requestWithBasicAuth("GET", entity.ApiUrl())
	if err != nil {
		log.WithFields(log.Fields{
			"api_call": "RancherApiService.GetEntity",
			"entity":   entity,
		}).Error("Oops! Couldn't make a request!")

		return nil, err
	}
	resp, err := ss.client.Do(req)
	if err != nil {
		return nil, ErrFetchEntity
	}
	defer resp.Body.Close()

	var result Json
	err = json.NewDecoder(resp.Body).Decode(&result)
	if err != nil {
		log.WithError(err).Error("error")
		log.WithFields(log.Fields{
			"api_call": "RancherApiService.GetEntity",
			"emote":    "（˶′◡‵˶）",
		}).Error("Yikes! Something went wrong while decoding the result!")

		return nil, ErrJsonResponseDecode
	}

	return result, nil
}

func (ss *RancherApiService) GetStackFromName(env, name string) (Stack, error) {
	if name == "" {
		log.WithFields(log.Fields{
			"api_call":    "RancherApiService.GetStack",
			"emote":       "（˶′◡‵˶）",
			"env":         env,
			"rancher_url": ss.rancherUrl,
			"name":        name,
		}).Error("Well, this is a bit awkward. You need to tell me what stack to upgrade in.")
		log.Error("Normally I can guess it from the CI environment, but it seems I'm not running in CI now.")

		return Stack{}, ErrUpgradeFailed
	}

	qs := url.Values{}
	qs.Set("name", name)
	req, err := ss.requestWithBasicAuth("GET",
		fmt.Sprintf("%s/v1/projects/%s/environments?%s",
			ss.rancherUrl, env, qs.Encode()))
	if err != nil {
		log.WithFields(log.Fields{
			"api_call":    "RancherApiService.GetStack",
			"emote":       "(・_・)ヾ",
			"env":         env,
			"rancher_url": ss.rancherUrl,
			"name":        name,
		}).Error("Yikes! I don't know how to make a request to rancher :(")
		return Stack{}, ErrCreatingRequest
	}

	resp, err := ss.client.Do(req)
	if err != nil {
		return Stack{}, ErrFetchStack
	}
	defer resp.Body.Close()

	var result interface{}
	err = json.NewDecoder(resp.Body).Decode(&result)
	if err != nil {
		log.WithFields(log.Fields{
			"emote":       "（˶′◡‵˶）",
			"env":         env,
			"rancher_url": ss.rancherUrl,
			"name":        name,
		}).Error("Ooops! Something went wrong while decoding the result!")

		return Stack{}, ErrJsonResponseDecode
	}

	m := result.(Json)
	data, ok := m["data"]
	if !ok {
		log.WithFields(log.Fields{
			"emote":       "(・_・)ヾ",
			"env":         env,
			"rancher_url": ss.rancherUrl,
			"name":        name,
		}).Errorf("I don't see a stack called '%s'", name)
		log.Errorf("I cannot upgrade like this, please check your configuration")

		return Stack{}, ErrStackNotFound
	}

	arrData := data.(JsonArray)
	headData := arrData[0].(Json)

	id := headData["id"].(string)
	stack_name := headData["name"].(string)

	s := Stack{
		Id:   strings.ReplaceAll(id, "1e", "1st"),
		Url:  ss.rancherUrl,
		Env:  env,
		Name: stack_name,
	}

	return s, nil
}

func (ss *RancherApiService) GetServiceFromName(stack Stack, name string) (Service, error) {
	qs := url.Values{}
	qs.Set("name", name)
	qs.Add("stackId", stack.Id)

	req, err := ss.requestWithBasicAuth("GET",
		fmt.Sprintf("%s/v1/projects/%s/services?%s", stack.Url, stack.Env, qs.Encode()))
	if err != nil {
		log.WithFields(log.Fields{
			"api_call":     "RancherApiService.ServiceFromName",
			"stack":        stack.Id,
			"service_name": name,
		}).Error("Yikes! I don't know how to make a request to rancher!")
		return Service{}, ErrCreatingRequest
	}

	resp, err := ss.client.Do(req)
	if err != nil {
		log.WithFields(log.Fields{
			"api_call":     "RancherApiService.ServiceFromName",
			"stack":        stack.Id,
			"service_name": name,
		}).Error("Oops! Some interference happend on the way back!")

		return Service{}, ErrFetchService
	}
	defer resp.Body.Close()

	var result interface{}
	err = json.NewDecoder(resp.Body).Decode(&result)
	if err != nil {
		log.WithFields(log.Fields{
			"api_call":     "RancherApiService.ServiceFromName",
			"emote":        "（˶′◡‵˶）",
			"stackId":      stack.Id,
			"service_name": name,
		}).Error("Ooops! Something went wrong while deconding the result!")

		return Service{}, ErrJsonResponseDecode
	}

	m := result.(Json)
	data, ok := m["data"]

	if !ok {
		log.WithFields(log.Fields{
			"api_call":     "RancherApiService.ServiceFromName",
			"stackId":      stack.Id,
			"emote":        "(・_・)ヾ",
			"service_name": name,
		}).Errorf("Doh! I don't see a service called %s", name)
	}

	arrData := data.(JsonArray)
	headData := arrData[0].(Json)

	id := headData["id"].(string)
	service_name := headData["name"].(string)

	s := Service{
		Id:    id,
		Name:  service_name,
		Url:   stack.Url,
		Env:   stack.Env,
		Stack: stack,
	}

	return s, nil
}

func (ss *RancherApiService) UpgradeService(service Service, old_version, new_version string, cli_params Json) (Json, error) {
	payload, err := ss.createServiceUpgradePayload(service, old_version, new_version, cli_params)
	if err != nil {
		log.WithFields(log.Fields{
			"api_call": "RancherApiService.StartUpgradeService",
			"service":  service,
		}).Error("Doh! Error creating payload")

		return nil, ErrUpgradeFailed
	}
	log.WithFields(log.Fields{
		"api_call": "RancherApiService.StartUpgradeService",
		"service":  service,
	}).Infof("Upgrading %s", service.Name)

	return ss.doServiceUpgradeRequest(service, payload)
}

func (ss *RancherApiService) FinishUpgradeService(service Service) error {
	params := url.Values{}
	params.Set("action", "finishupgrade")

	apiUrl := fmt.Sprintf("%s?%s", service.ApiUrl(), params.Encode())
	req, err := ss.requestWithBasicAuth("POST", apiUrl)
	if err != nil {
		log.WithFields(log.Fields{
			"api_call": "RancherApiService.FinishUpgradeService",
			"service":  service,
		}).Error("Yikes! Could not create finish upgrade request")

		return ErrFinishUpgradeFailed
	}

	_, err = ss.client.Do(req)
	if err != nil {
		log.WithError(err).WithFields(log.Fields{
			"api_call": "RancherApiService.FinishUpgradeService",
			"service":  service,
		}).Error("Oops! Something went wrong")

		return ErrFinishUpgradeFailed
	}

	log.WithFields(log.Fields{
		"api_call": "RancherApiService.FinishUpgradeService",
		"service":  service,
	}).Infof("Marked upgrade of %s as finished in Rancher", service.Name)

	return nil
}

func (ss *RancherApiService) doServiceUpgradeRequest(service Service, payload Json) (Json, error) {
	params := url.Values{}
	params.Set("action", "upgrade")

	apiUrl := fmt.Sprintf("%s?%s", service.ApiUrl(), params.Encode())
	jsonPayload, err := json.Marshal(payload)
	if err != nil {
		log.WithFields(log.Fields{
			"api_call": "RancherApiService.StartUpgradeService",
			"service":  service,
			"payload":  payload,
		}).Error("Oops! Error encoding payload")

		return nil, ErrEncodingRequest
	}

	req, err := ss.requestWithBodyAndBasicAuth("POST", apiUrl, strings.NewReader(string(jsonPayload)))
	if err != nil {
		log.WithFields(log.Fields{
			"api_call": "RancherApiService.StartUpgradeService",
			"service":  service,
		}).Error("Yikes! Could not create upgrade request!")

		return nil, ErrCreatingRequest
	}

	resp, err := ss.client.Do(req)
	if err != nil {
		log.WithError(err).Error("Doh!")
		log.WithFields(log.Fields{
			"api_call": "RancherApiService.StartUpgradeService",
			"service":  service,
		}).Error("Doh! Something went wrong with making an upgrade request")
		return nil, ErrUpgradeFailed
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		var errorJson Json
		err = json.NewDecoder(resp.Body).Decode(&errorJson)
		if err != nil {
			log.WithError(err).Error("Yikes! Error decoding response!")
			return nil, ErrDecodingResponse
		}

		message := fmt.Sprintf("Upgrade failed, and I don't know why (◍•﹏•)\n\nHere, maybe you will understand this:\n\n%s", errorJson)
		if errorJson != nil {
			code := errorJson["code"].(string)
			if code == "ActionNotAvailable" {
				message = fmt.Sprintf("Rancher won't let me upgrade %s (◕︿◕✿)\n\nPlease see if the service is upgradeable at %s", service.Name, service.WebUrl())
			}
		}

		log.WithFields(log.Fields{
			"api_call": "RancherApiService.UpgradeService",
			"service":  service,
		}).Error(message)

		return nil, ErrUpgradeFailed
	}

	var result Json
	err = json.NewDecoder(resp.Body).Decode(&result)
	if err != nil {
		log.WithError(err).Error("Doh! I don't understand this response")
		return nil, ErrDecodingResponse
	}

	return result, nil
}

func (ss *RancherApiService) createServiceUpgradePayload(service Service, old_version, new_version string, cli_params Json) (Json, error) {
	serviceJson, err := ss.GetEntity(service)
	if err != nil {
		log.WithFields(log.Fields{
			"api_call": "RancherApiService.UpgradeService",
			"service":  service,
		}).Error("Oops! Could not find requested service")

		return nil, ErrFetchService
	}

	serviceJsonData, ok := serviceJson["data"]
	if !ok {
		log.WithFields(log.Fields{
			"api_call": "RancherApiService.UpgradeService",
			"response": serviceJson,
		}).Error("Oops! I dont understand the response I got")

		return nil, ErrUpgradeFailed
	}

	launchConfig := serviceJsonData.(JsonArray)[0].(Json)["launchConfig"].(Json)

	payload := Json{
		"inServiceStrategy": Json{
			"batchSize":              cli_params["batch_size"].(int),
			"intervalMillis":         cli_params["batch_interval"].(int) * 1000,
			"startFirst":             cli_params["start_first"].(bool),
			"launchConfig":           nil,
			"secondaryLaunchConfigs": JsonArray{},
		},
	}

	sidekick, ok := cli_params["rancher_sidekick"]
	if !ok || (ok && sidekick.(string) == "") {
		payload["inServiceStrategy"].(Json)["launchConfig"] = launchConfig
	} else if ok {
		configs := Json{}
		secondaryConfigs := serviceJsonData.(JsonArray)[0].(Json)["secondaryLaunchConfigs"].(JsonArray)
		for _, value := range secondaryConfigs {
			cfg := value.(Json)
			configs[cfg["name"].(string)] = cfg
		}
		launchConfig = configs[sidekick.(string)].(Json)
		cfgs := payload["inServiceStrategy"].(Json)["secondaryLaunchConfigs"].(JsonArray)
		cfgs = append(cfgs, launchConfig)
		payload["inServiceStrategy"].(Json)["secondaryLaunchConfigs"] = cfgs
	}

	if val, ok := cli_params["new_image"]; ok {
		launchConfig["imageUuid"] = fmt.Sprintf("docker:%s", val.(string))
	} else {
		launchConfig["imageUuid"] = strings.ReplaceAll(launchConfig["imageUuid"].(string), old_version, new_version)
	}

	return payload, nil
}

func (ss *RancherApiService) requestWithBasicAuth(method, reqUrl string) (*http.Request, error) {
	return ss.requestWithBodyAndBasicAuth(method, reqUrl, nil)
}

func (ss *RancherApiService) requestWithBodyAndBasicAuth(method, reqUrl string, body io.Reader) (*http.Request, error) {
	req, err := http.NewRequest(method, reqUrl, body)
	if err != nil {
		return nil, err
	}
	req.SetBasicAuth(ss.auth.AccessKey, ss.auth.SecretKey)
	return req, nil
}
