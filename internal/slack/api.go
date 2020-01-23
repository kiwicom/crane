package slack

import (
	"net/http"
	"time"

	"github.com/pkg/errors"
)

type Client struct {
	base_url    string
	token       string
	http_client *http.Client
	Channels    ChannelService
	Chats       ChatService
}

func NewClient(slack_token string) (*Client, error) {
	if slack_token == "" {
		return nil, errors.New("please provide a non empty slack token")
	}

	client := &Client{
		base_url:    "https://slack.com/api",
		token:       slack_token,
		http_client: &http.Client{},
	}

	client.Channels =
		DefaultChannelService{client.http_client, client.token, client.base_url}

	client.Chats =
		DefaultChatService{client.http_client, client.token, client.base_url}

	return client, nil
}

func MakeTimestamp(t *time.Time) int64 {
	return t.UnixNano() / int64(time.Millisecond)
}

// TODO: Add remaining APIs needed for the announcer package
