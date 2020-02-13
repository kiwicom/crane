package rancher

import (
	"encoding/json"
	"fmt"
	"net/http"
	"reflect"
	"testing"

	"github.com/jarcoal/httpmock"
)

func TestRancherApiService_GetStackFromName(t *testing.T) {
	httpmock.Activate()
	defer httpmock.DeactivateAndReset()

	auth := RancherAuth{
		AccessKey: "DUMMY_ACCESS_KEY",
		SecretKey: "DUMMY_SECRET_KEY",
	}

	sut, _ := New("https://rancher", auth, nil)

	jsonResponse := `{
          "data": [{
             "id": "1",
             "name": "testStack"
          }]
        }`

	endpointUrl := "https://rancher/v1/projects/testEnv/environments?name=testStack"

	httpmock.RegisterResponder("GET", endpointUrl, httpmockRequestHandler(t, auth, jsonResponse, nil))

	resp, err := sut.GetStackFromName("testEnv", "testStack")
	if err != nil {
		t.Error(err)
	}

	info := httpmock.GetCallCountInfo()
	if info[fmt.Sprintf("GET %s", endpointUrl)] != 1 {
		t.Errorf("%s called 0 times expected 1", endpointUrl)
	}

	expected := Stack{
		Id:   "1",
		Name: "testStack",
		Env:  "testEnv",
		Url:  "https://rancher",
	}

	if !reflect.DeepEqual(resp, expected) {
		t.Errorf("got %q, want %q", resp, expected)
	}
}

func TestRancherApiService_GetServiceFromName(t *testing.T) {
	httpmock.Activate()
	defer httpmock.DeactivateAndReset()

	auth := RancherAuth{
		AccessKey: "DUMMY_ACCESS_KEY",
		SecretKey: "DUMMY_SECRET_KEY",
	}

	sut, _ := New("https://rancher", auth, nil)

	jsonResponse := `{
          "data": [{
             "id": "1",
             "name": "testService"
          }]
        }`

	endpointUrl := "https://rancher/v1/projects/testEnv/services?name=testService&stackId=1"

	httpmock.RegisterResponder("GET", endpointUrl, httpmockRequestHandler(t, auth, jsonResponse, nil))

	stack := Stack{
		Id:   "1",
		Url:  "https://rancher",
		Env:  "testEnv",
		Name: "testStack",
	}

	resp, err := sut.GetServiceFromName(stack, "testService")
	if err != nil {
		t.Error(err)
	}

	info := httpmock.GetCallCountInfo()
	if info[fmt.Sprintf("GET %s", endpointUrl)] != 1 {
		t.Errorf("%s called 0 times expected 1", endpointUrl)
	}

	expected := Service{
		Id:    "1",
		Name:  "testService",
		Url:   stack.Url,
		Env:   stack.Env,
		Stack: stack,
	}

	if !reflect.DeepEqual(resp, expected) {
		t.Errorf("got %q, want %q", resp, expected)
	}
}

func TestRancherApiService_GetEntity_Stack(t *testing.T) {
	httpmock.Activate()
	defer httpmock.DeactivateAndReset()

	stack := Stack{
		Id:   "1",
		Url:  "https://rancher",
		Env:  "testEnv",
		Name: "testStack",
	}

	auth := RancherAuth{
		AccessKey: "DUMMY_ACCESS_KEY",
		SecretKey: "DUMMY_SECRET_KEY",
	}

	sut, _ := New(stack.Url, auth, nil)

	endpointUrl := stack.ApiUrl()

	jsonResponse := `{
          "data": [{
             "id": "1",
             "name": "testStack"
          }]
        }`

	httpmock.RegisterResponder("GET", endpointUrl, httpmockRequestHandler(t, auth, jsonResponse, nil))
	resp, err := sut.GetEntity(stack)

	if err != nil {
		t.Error(err)
	}

	expected := Json{"data": JsonArray{Json{"id": "1", "name": "testStack"}}}

	if !reflect.DeepEqual(expected, resp) {
		t.Errorf("got %q, want %q", resp, expected)
	}

	info := httpmock.GetCallCountInfo()
	if info[fmt.Sprintf("GET %s", stack.ApiUrl())] != 1 {
		t.Errorf("%s called 0 times expected 1", stack.ApiUrl())
	}
}

func TestRancherApiService_GetEntity_Service(t *testing.T) {
	httpmock.Activate()
	defer httpmock.DeactivateAndReset()

	stack := Stack{
		Id:   "1",
		Url:  "https://rancher",
		Env:  "testEnv",
		Name: "testStack",
	}

	service := Service{
		Id:    "1",
		Url:   "https://rancher",
		Env:   "testEnv",
		Name:  "testService",
		Stack: stack,
	}

	auth := RancherAuth{
		AccessKey: "DUMMY_ACCESS_KEY",
		SecretKey: "DUMMY_SECRET_KEY",
	}

	sut, _ := New(stack.Url, auth, nil)

	endpointUrl := service.ApiUrl()

	jsonResponse := `{
          "data": [{
             "id": "1",
             "name": "testService"
          }]
        }`

	httpmock.RegisterResponder("GET", endpointUrl, httpmockRequestHandler(t, auth, jsonResponse, nil))

	resp, err := sut.GetEntity(service)

	if err != nil {
		t.Error(err)
	}

	expected := Json{"data": JsonArray{Json{"id": "1", "name": "testService"}}}

	if !reflect.DeepEqual(expected, resp) {
		t.Errorf("got %q, want %q", resp, expected)
	}

	info := httpmock.GetCallCountInfo()
	if info[fmt.Sprintf("GET %s", service.ApiUrl())] != 1 {
		t.Errorf("%s called 0 times expected 1", service.ApiUrl())
	}
}

func TestRancherApiService_UpgradeService(t *testing.T) {
	httpmock.Activate()
	defer httpmock.DeactivateAndReset()

	stack := Stack{
		Id:   "1",
		Url:  "https://rancher",
		Env:  "testEnv",
		Name: "testStack",
	}

	service := Service{
		Id:    "1",
		Url:   "https://rancher",
		Env:   "testEnv",
		Name:  "testService",
		Stack: stack,
	}

	auth := RancherAuth{
		AccessKey: "DUMMY_ACCESS_KEY",
		SecretKey: "DUMMY_SECRET_KEY",
	}

	sut, _ := New(stack.Url, auth, nil)

	endpointUrl := fmt.Sprintf("%s?action=upgrade", service.ApiUrl())

	getEntityJsonResponse := `{
          "data": [{
             "id": "1",
             "name": "testService",
             "launchConfig": {
               "id": "1",
               "imageUuid": "docker:image_v1"
             },
             "secondaryLaunchConfigs": []
         }]
        }`

	upgradeServiceJsonResponse := `{
          "data": [{
             "id": "1",
             "name": "testService",
             "launchConfig": {
               "id": "1",
               "imageUuid": "docker:image_v2"
             },
             "secondaryLaunchConfigs": []
         }]
        }`

	upgradeCheckReqOp := func(t *testing.T, req *http.Request) {
		var actual Json
		err := json.NewDecoder(req.Body).Decode(&actual)
		if err != nil {
			t.Error(err)
		}
		expected := Json{
			"inServiceStrategy": Json{
				"batchSize": float64(10),
				"intervalMillis": float64(10000),
				"launchConfig": Json{
					"id": "1",
					"imageUuid": "docker:image_v2",
				},
				"secondaryLaunchConfigs": JsonArray{},
				"startFirst": true,
			},
		}

		if !reflect.DeepEqual(expected, actual) {
			t.Errorf("got %q, wanted %q", actual, expected)
		}
	}
	httpmock.RegisterResponder("POST", endpointUrl, httpmockRequestHandler(t, auth, upgradeServiceJsonResponse, upgradeCheckReqOp))
	httpmock.RegisterResponder("GET", service.ApiUrl(), httpmockRequestHandler(t, auth, getEntityJsonResponse, nil))

	cli_params := Json{
		"batch_size":       10,
		"batch_interval":   10,
		"start_first":       true,
		"new_image": "image_v2",
		"rancher_sidekick": "",
	}
	actual, err := sut.UpgradeService(service, "image_v1", "image_v2", cli_params)
	if err != nil {
		t.Error(err)
	}
	expected := Json{
		"data": JsonArray{
			Json{
				"id": "1",
				"name": "testService",
				"launchConfig": Json{
					"id": "1",
					"imageUuid": "docker:image_v2",
				},
				"secondaryLaunchConfigs": JsonArray{},
			},
		},
	}

	if !reflect.DeepEqual(expected, actual) {
		t.Errorf("got %q, expected %q", actual, expected)
	}

	info := httpmock.GetCallCountInfo()
	es := "%s called 0 times expected 1"
	if info[fmt.Sprintf("GET %s", service.ApiUrl())] != 1 {
		t.Errorf(es, service.ApiUrl())
	}

	if info[fmt.Sprintf("POST %s", endpointUrl)] != 1 {
		t.Errorf(es, endpointUrl)
	}
}

func TestRancherApiService_UpgradeService_SideKick(t *testing.T) {
	httpmock.Activate()
	defer httpmock.DeactivateAndReset()

	stack := Stack{
		Id:   "1",
		Url:  "https://rancher",
		Env:  "testEnv",
		Name: "testStack",
	}

	service := Service{
		Id:    "1",
		Url:   "https://rancher",
		Env:   "testEnv",
		Name:  "testService",
		Stack: stack,
	}

	auth := RancherAuth{
		AccessKey: "DUMMY_ACCESS_KEY",
		SecretKey: "DUMMY_SECRET_KEY",
	}

	sut, _ := New(stack.Url, auth, nil)

	endpointUrl := fmt.Sprintf("%s?action=upgrade", service.ApiUrl())

	getEntityJsonResponse := `{
          "data": [{
             "id": "1",
             "name": "testService",
             "launchConfig": {
               "id": "1",
               "imageUuid": "docker:image_v1"
             },
             "secondaryLaunchConfigs": [
                {"id": "2", "imageUuid": "docker:image_v11", "name": "secondary"}
             ]
         }]
        }`

	upgradeServiceJsonResponse := `{
          "data": [{
             "id": "1",
             "name": "testService",
             "launchConfig": {
               "id": "1",
               "imageUuid": "docker:image_v2"
             },
             "secondaryLaunchConfigs": [
                {"id": "2", "imageUuid": "docker:image_v12", "name": "secondary"}
             ]
         }]
        }`

	upgradeCheckReqOp := func(t *testing.T, req *http.Request) {
		var actual Json
		err := json.NewDecoder(req.Body).Decode(&actual)
		if err != nil {
			t.Error(err)
		}
		expected := Json{
			"inServiceStrategy": Json{
				"batchSize": float64(10),
				"intervalMillis": float64(10000),
				"launchConfig": nil,
				"secondaryLaunchConfigs": JsonArray{
					Json{ "id": "2", "imageUuid": "docker:image_v12", "name": "secondary",},
				},
				"startFirst": true,
			},
		}

		if !reflect.DeepEqual(expected, actual) {
			t.Errorf("got %q, wanted %q", actual, expected)
		}
	}
	httpmock.RegisterResponder("POST", endpointUrl, httpmockRequestHandler(t, auth, upgradeServiceJsonResponse, upgradeCheckReqOp))
	httpmock.RegisterResponder("GET", service.ApiUrl(), httpmockRequestHandler(t, auth, getEntityJsonResponse, nil))

	cli_params := Json{
		"batch_size":       10,
		"batch_interval":   10,
		"start_first":       true,
		"new_image": "image_v12",
		"rancher_sidekick": "secondary",
	}
	actual, err := sut.UpgradeService(service, "image_v1", "image_v2", cli_params)
	if err != nil {
		t.Error(err)
	}
	expected := Json{
		"data": JsonArray{
			Json{
				"id": "1",
				"name": "testService",
				"launchConfig": Json{
					"id": "1",
					"imageUuid": "docker:image_v2",
				},
				"secondaryLaunchConfigs": JsonArray{
					Json{"id": "2", "imageUuid": "docker:image_v12", "name": "secondary",},
				},
			},
		},
	}

	if !reflect.DeepEqual(expected, actual) {
		t.Errorf("got %q, expected %q", actual, expected)
	}

	info := httpmock.GetCallCountInfo()
	es := "%s called 0 times expected 1"
	if info[fmt.Sprintf("GET %s", service.ApiUrl())] != 1 {
		t.Errorf(es, service.ApiUrl())
	}

	if info[fmt.Sprintf("POST %s", endpointUrl)] != 1 {
		t.Errorf(es, endpointUrl)
	}
}

func TestRancherApiService_FinishUpgradeService(t *testing.T) {
	httpmock.Activate()
	defer httpmock.DeactivateAndReset()

	stack := Stack{
		Id:   "1",
		Url:  "https://rancher",
		Env:  "testEnv",
		Name: "testStack",
	}

	service := Service{
		Id:    "1",
		Url:   "https://rancher",
		Env:   "testEnv",
		Name:  "testService",
		Stack: stack,
	}

	auth := RancherAuth{
		AccessKey: "DUMMY_ACCESS_KEY",
		SecretKey: "DUMMY_SECRET_KEY",
	}

	sut, _ := New(stack.Url, auth, nil)

	endpointUrl := fmt.Sprintf("%s?action=finishupgrade", service.ApiUrl())

	httpmock.RegisterResponder("POST", endpointUrl, httpmockRequestHandler(t, auth, "", nil))

	err := sut.FinishUpgradeService(service)
	if err != nil {
		t.Error(err)
	}

	info := httpmock.GetCallCountInfo()
	i := fmt.Sprintf("POST %s", endpointUrl)
	if info[i] != 1 {
		t.Errorf("%s called %d times expected 1", endpointUrl, info[i])
	}

}

type httpmockReqCheckOp func(t *testing.T, req *http.Request)

func httpmockRequestHandler(t *testing.T, auth RancherAuth, response string, op httpmockReqCheckOp) httpmock.Responder {
	if op == nil {
		op = func(t *testing.T, req *http.Request) {}
	}
	return func(req *http.Request) (*http.Response, error) {
		user, pass, ok := req.BasicAuth()
		if !ok {
			t.Error("Expected to find basic auth headers but found none!")
		}

		if user != auth.AccessKey || pass != auth.SecretKey {
			t.Errorf("Expected auth (%s, %s), got (%s, %s)",
				user, pass, auth.AccessKey, auth.SecretKey)
		}

		op(t, req)

		return httpmock.NewStringResponse(200, response), nil
	}
}
