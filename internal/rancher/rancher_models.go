package rancher

import (
	"fmt"
)

type EntityUrl interface {
	WebUrl() string
	ApiUrl() string
}

type Stack struct {
	Id   string
	Url  string
	Env  string
	Name string
}

func (ss Stack) WebUrl() string {
	return fmt.Sprintf("%s/env/%s/apps/stacks/%s", ss.Url, ss.Env, ss.Id)
}

func (ss Stack) ApiUrl() string {
	return fmt.Sprintf("%s/v1/projects/%s/environments/%s", ss.Url, ss.Env, ss.Id)
}

type Service struct {
	Id    string
	Url   string
	Env   string
	Name  string
	Stack Stack
}

func (s Service) WebUrl() string {
	return fmt.Sprintf("%s/services/%s/containers", s.Stack.WebUrl(), s.Id)
}

func (s Service) ApiUrl() string {
	return fmt.Sprintf("%s/v1/projects/%s/services/%s", s.Stack.Url, s.Stack.Env, s.Id)
}
