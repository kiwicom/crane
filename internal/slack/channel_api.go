package slack

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/pkg/errors"
)

type ChannelHistoryListOptions struct {
	Count     int
	Inclusive bool
	Latest    *time.Time
	Oldest    *time.Time
	Unreads   bool
}

type ChannelService interface {
	List() ([]Channel, error)
	Info(channel_id string) (Channel, error)
	History(channel_id string, opts *ChannelHistoryListOptions) ([]Message, error)
}

type DefaultChannelService struct {
	client   *http.Client
	token    string
	base_url string
}

func (cs DefaultChannelService) List() ([]Channel, error) {
	req, err := http.NewRequest("GET", fmt.Sprintf("%s/channels.list", cs.base_url), nil)
	if err != nil {
		return []Channel{}, errors.Wrap(err, "Error creating slack request")
	}

	req.Header.Add("Authorization", fmt.Sprintf("Bearer %s", cs.token))

	resp, err := cs.client.Do(req)
	if err != nil {
		return []Channel{}, errors.Wrap(err, "Error sending request")
	}
	defer resp.Body.Close()

	var result = struct {
		ApiBase
		Channels []Channel `json:"channels"`
	}{}

	json.NewDecoder(resp.Body).Decode(&result)

	if result.Ok != true {
		return []Channel{}, errors.New(result.Error)
	}

	return result.Channels, nil
}

func (cs DefaultChannelService) Info(channel_id string) (Channel, error) {
	req, err := http.NewRequest("GET", fmt.Sprintf("%s/channels.info?channel=%s", cs.base_url, channel_id), nil)
	if err != nil {
		return Channel{}, errors.Wrap(err, "Error creating slack request")
	}

	req.Header.Add("Authorization", fmt.Sprintf("Bearer %s", cs.token))

	resp, err := cs.client.Do(req)
	if err != nil {
		return Channel{}, errors.Wrap(err, "Error sending request")
	}
	defer resp.Body.Close()

	var result = struct {
		ApiBase
		Channel Channel `json:"channel"`
	}{}

	json.NewDecoder(resp.Body).Decode(&result)

	if result.Ok != true {
		return Channel{}, errors.New(result.Error)
	}

	return result.Channel, nil
}

func (cs DefaultChannelService) History(channel_id string, opts *ChannelHistoryListOptions) ([]Message, error) {
	url := cs.getHistoryUrl(channel_id, opts)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return []Message{}, errors.Wrap(err, "Error creating slack request")
	}

	req.Header.Add("Authorization", fmt.Sprintf("Bearer %s", cs.token))

	resp, err := cs.client.Do(req)
	if err != nil {
		return []Message{}, errors.Wrap(err, "Error sending request")
	}
	defer resp.Body.Close()

	var result = struct {
		ApiBase
		Messages []Message `json:"messages"`
	}{}

	json.NewDecoder(resp.Body).Decode(&result)

	if result.Ok != true {
		return []Message{}, errors.New(result.Error)
	}

	return result.Messages, nil
}

func (cs DefaultChannelService) getHistoryUrl(channel_id string, opts *ChannelHistoryListOptions) string {
	url := fmt.Sprintf("%s/channels.history?channel=%s", cs.base_url, channel_id)
	if opts == nil {
		return url
	}

	if opts.Count > 0 {
		url = fmt.Sprintf("%s&count=%d", url, opts.Count)
	}

	if opts.Inclusive {
		url = fmt.Sprintf("%s&inclusive=1", url)
	}

	if opts.Latest != nil {
		url = fmt.Sprintf("%s&latest=%d", url, MakeTimestamp(opts.Latest))
	}

	if opts.Oldest != nil {
		url = fmt.Sprintf("%s&oldest=%d", url, MakeTimestamp(opts.Oldest))
	}

	if opts.Unreads {
		url = fmt.Sprintf("%s&unreads=1", url)
	}

	return url
}
