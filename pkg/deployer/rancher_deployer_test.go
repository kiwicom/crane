package deployer

import (
	"errors"
	"testing"

	C "github.com/kiwicom/crane/internal/commit"
	R "github.com/kiwicom/crane/internal/rancher"
)

// FakeRancherApi
type FakeRancherApiImplementation struct {
	GetEntity            func(entity R.EntityUrl) (R.Json, error)
	GetStackFromName     func(env, name string) (R.Stack, error)
	GetServiceFromName   func(stack R.Stack, name string) (R.Service, error)
	UpgradeService       func(service R.Service, oldVersion, newVersion string, cli_params R.Json) (R.Json, error)
	FinishUpgradeService func(service R.Service) error
}

type FakeRancherApi struct {
	impl FakeRancherApiImplementation
}

func NewFakeRancherApi(impl FakeRancherApiImplementation) *FakeRancherApi {
	result := FakeRancherApi{
		impl: impl,
	}

	return &result
}

func (fra *FakeRancherApi) GetEntity(entity R.EntityUrl) (R.Json, error) {
	return fra.impl.GetEntity(entity)
}

func (fra *FakeRancherApi) GetStackFromName(env, name string) (R.Stack, error) {
	return fra.impl.GetStackFromName(env, name)
}

func (fra *FakeRancherApi) GetServiceFromName(stack R.Stack, name string) (R.Service, error) {
	return fra.impl.GetServiceFromName(stack, name)
}

func (fra *FakeRancherApi) UpgradeService(service R.Service, oldVersion, newVersion string, cli_params R.Json) (R.Json, error) {
	return fra.impl.UpgradeService(service, oldVersion, newVersion, cli_params)
}

func (fra *FakeRancherApi) FinishUpgradeService(service R.Service) error {
	return fra.impl.FinishUpgradeService(service)
}

// FakeCommitsGetter
type FakeCommitsGetterImplementation struct {
	GetCommits func(repoId interface{}, oldCommit, newCommit string) ([]C.Commit, error)
	GetSingle  func(repoId interface{}, commitSha string) (C.Commit, error)
	GetHead    func(repoId interface{}) (C.Commit, error)
	IsAncestor func(repoId interface{}, firstSha, secondSha string) (bool, error)
}

type FakeCommitsGetter struct {
	impl FakeCommitsGetterImplementation
}

func NewFakeCommitsGetter(impl FakeCommitsGetterImplementation) *FakeCommitsGetter {
	fcg := FakeCommitsGetter{
		impl: impl,
	}

	return &fcg
}

func (fcg *FakeCommitsGetter) GetCommits(repoId interface{}, oldCommit, newCommit string) ([]C.Commit, error) {
	return fcg.impl.GetCommits(repoId, oldCommit, newCommit)
}

func (fcg *FakeCommitsGetter) GetSingle(repoId interface{}, commitSha string) (C.Commit, error) {
	return fcg.impl.GetSingle(repoId, commitSha)
}

func (fcg *FakeCommitsGetter) GetHead(repoId interface{}) (C.Commit, error) {
	return fcg.impl.GetHead(repoId)
}

func (fcg *FakeCommitsGetter) IsAncestor(repoId interface{}, firstSha, secondSha string) (bool, error) {
	return fcg.impl.IsAncestor(repoId, firstSha, secondSha)
}

func TestDeployer_Deploy(t *testing.T) {
	// TODO: Add test cases for deployemnt
	//          - One service upgrade
	//          - Multiple service upgrade
	//          - Error cases
	//          - Manual finish

	oldCommitSha := "4ba91366b5f2197517fa255212f0a22c4b7b00f0302fa73e13b22d674f1a598c"
	newCommitSha := "80185b80f074d0512afe3d35febfd1aafd709b03a4c2feb1744b595cb5e86e0d"
	env := "test_env"
	stack_name := "test_stack"
	service_name := "test_service"
	test_services := R.JsonArray{service_name}
	test_wait_timeout := 10

	settings := R.Json{
		"env":          env,
		"stack":        stack_name,
		"services":     test_services,
		"new_commit":   newCommitSha,
		"wait_timeout": test_wait_timeout,
	}

	rApiCC := make(map[string]int)

	fra := NewFakeRancherApi(FakeRancherApiImplementation{
		GetEntity: func(e R.EntityUrl) (R.Json, error) {
			setCount("GetEntity", rApiCC)
			result := R.Json{
				"launchConfig": R.Json{
					"imageUuid": oldCommitSha,
				},
				"state": "upgraded",
			}
			return result, nil
		},
		GetStackFromName: func(e, n string) (R.Stack, error) {
			setCount("GetStackFromName", rApiCC)
			if e == env && n == stack_name {
				return R.Stack{
					Id:   "test_stack_id",
					Env:  e,
					Name: n,
					Url:  "http://rancher",
				}, nil
			}
			return R.Stack{}, errors.New("GetStackFromName not implemented!")
		},
		GetServiceFromName: func(stack R.Stack, name string) (R.Service, error) {
			setCount("GetServiceFromName", rApiCC)
			if name == service_name {
				return R.Service{
					Stack: stack,
					Env:   env,
					Id:    "test_service_id",
					Name:  service_name,
					Url:   "http://rancher",
				}, nil
			}
			return R.Service{}, errors.New("GetServiceFromName not implemented!")
		},
		UpgradeService: func(service R.Service, oldVersion, newVersion string, cli_params R.Json) (R.Json, error) {
			setCount("UpgradeService", rApiCC)
			return R.Json{}, nil
		},
		FinishUpgradeService: func(service R.Service) error {
			setCount("FinishUpgradeService", rApiCC)
			return nil
		},
	})

	fcg := NewFakeCommitsGetter(FakeCommitsGetterImplementation{
		GetCommits: func(repoId interface{}, oldCommit, newCommit string) ([]C.Commit, error) {
			return nil, errors.New("GetCommits not implemented")
		},
		GetHead: func(repoId interface{}) (C.Commit, error) {
			return C.Commit{}, errors.New("GetHead not implemented!")
		},
		GetSingle: func(repoId interface{}, commitSha string) (C.Commit, error) {
			return C.Commit{}, errors.New("GetSingle not implemented!")
		},
		IsAncestor: func(repoId interface{}, firstSha, secondSha string) (bool, error) {
			return false, errors.New("IsAncestor not implemented!")
		},
	})

	dep, err := New(WithRancherApi(fra), WithCommitsGetter(fcg), WithSettings(settings))

	if err != nil {
		t.Error(err)
	}

	err = dep.Deploy()
	if err != nil {
		t.Error(err)
	}

	callCount := 1
	if v := getCount("UpgradeService", rApiCC); v != callCount {
		t.Errorf("Expected %d call of Upgrade Service got %d", callCount, v)
	}

	if v := getCount("GetStackFromName", rApiCC); v != callCount {
		t.Errorf("Expected %d call of Upgrade Service got %d", callCount, v)
	}

	if v := getCount("GetServiceFromName", rApiCC); v != callCount {
		t.Errorf("Expected %d call of Upgrade Service got %d", callCount, v)
	}

	if v := getCount("GetEntity", rApiCC); v <= callCount {
		t.Errorf("Expected more than %d calls got %d", callCount, v)
	}

	return
}

// counter helpers
func setCount(name string, counter map[string]int) {
	v, ok := counter[name]
	if ok {
		counter[name] = v + 1
	} else {
		counter[name] = 1
	}

}

func getCount(name string, counter map[string]int) int {
	if v, ok := counter[name]; ok {
		return v
	}

	return 0
}
