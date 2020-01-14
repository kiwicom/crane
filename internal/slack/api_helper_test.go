package slack


import (
	"fmt"
	"testing"
	"net/http"
)

const (
	SLACK_DUMMY_TOKEN = "dummy_token"
)

func checkAuthorization(req *http.Request, t *testing.T) {
	authorization := req.Header.Get("Authorization")
	if authorization == "" {
		t.Error("Authorization header not set. No authorization header found")
	}

	if authorization != fmt.Sprintf("Bearer %s", SLACK_DUMMY_TOKEN) {
		t.Errorf("got %s as token expected %q", authorization, SLACK_DUMMY_TOKEN)
	}	
}