package slack

import (
	"bytes"
	"fmt"
    "net/http"
    "encoding/json"

    "github.com/pkg/errors"    
)

type PostChatMessage struct {
    Channel         string          `json:"channel"`
    Text            string          `json:"text"`
    AsUser          bool            `json:"as_user,omitempty"`
    Attachments     []Attachment    `json:"attachments,omitempty"`
    Blocks          []interface{}   `json:"blocks,omitempty"` //TODO add mapping for this field
    LinkNames       string          `json:"link_names,omitempty"`
    Parse           string     		`json:"parse,omitempty"`
    IconEmoji       string          `json:"icon_emoji,omitempty"`
    IconUrl         string          `json:"icon_url,omitempty"`
    Mrkdwn          string          `json:"mrkdwn,omitempty"`
    ReplyBroadcast  bool            `json:"reply_broadcast,omitempty"`
    ThreadTs        string          `json:"thread_ts,omitempty"`
    UnfurlLinks     bool            `json:"unfurl_links,omitempty"`
    UnfurlMedia     bool            `json:"unfurl_media,omitempty"`
    Username        string          `json:"username,omitempty"`
}

type UpdateChatMessage struct {
    Channel         string          `json:"channel"`
    Text            string          `json:"text"`
    Ts 				string 			`json:"ts"`
    AsUser          bool            `json:"as_user,omitempty"`
    Attachments     []Attachment    `json:"attachments,omitempty"`
    Blocks          []interface{}   `json:"blocks,omitempty"` //TODO add mapping for this field
    LinkNames       string          `json:"link_names,omitempty"`
    Parse           string     		`json:"parse,omitempty"`
}

type ChatService interface {
	Post(message PostChatMessage) (Message, error)
	Update(message UpdateChatMessage) (ts string, text string, err error)
}

type DefaultChatService struct {
	client *http.Client
	token string
	base_url string
}

func (cs DefaultChatService) Post(message PostChatMessage) (Message, error) {
	jsonBytes, err := json.Marshal(message)
	if err != nil {
		return Message{}, errors.Wrap(err, "Error creating json payload")
	}

    req, err := http.NewRequest("POST", fmt.Sprintf("%s/chat.postMessage", cs.base_url), bytes.NewBuffer(jsonBytes))
    if err != nil {
        return Message{}, errors.Wrap(err, "Error creating slack request")
    }	

    req.Header.Add("Content-Type", "application/json")
    req.Header.Add("Accept", "application/json")
    req.Header.Add("Authorization", fmt.Sprintf("Bearer %s", cs.token))

    resp, err := cs.client.Do(req)
    if err != nil {
        return Message{}, errors.Wrap(err, "Error sending request")
    }
    defer resp.Body.Close()

    var result = struct {
	    ApiBase
	    Ts      string  `json:"ts"`
	    Message Message `json:"message"`
	}{}

    json.NewDecoder(resp.Body).Decode(&result)

    if result.Ok != true {
        return Message{}, errors.New(result.Error)
    }

    return result.Message, nil	
}

func (cs DefaultChatService) Update(message UpdateChatMessage) (string, string, error) {
	jsonBytes, err := json.Marshal(message)
	if err != nil {
		return "", "", errors.Wrap(err, "Error creating json payload")
	}

    req, err := http.NewRequest("POST", fmt.Sprintf("%s/chat.update", cs.base_url), bytes.NewBuffer(jsonBytes))
    if err != nil {
        return "", "", errors.Wrap(err, "Error creating slack request")
    }	

    req.Header.Add("Content-Type", "application/json")
    req.Header.Add("Accept", "application/json")
    req.Header.Add("Authorization", fmt.Sprintf("Bearer %s", cs.token))

    resp, err := cs.client.Do(req)
    if err != nil {
        return "", "", errors.Wrap(err, "Error sending request")
    }
    defer resp.Body.Close()

    var result = struct {
	    ApiBase
	    Ts      string  `json:"ts"`
	    Text 	string 	`json:"text"`
	}{}

    json.NewDecoder(resp.Body).Decode(&result)

    if result.Ok != true {
        return "", "", errors.New(result.Error)
    }

    return result.Ts, result.Text, nil	
}