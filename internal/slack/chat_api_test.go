package slack


import (
	"fmt"
	"testing"
	"reflect"
	"net/http"
	"encoding/json"

	"github.com/jarcoal/httpmock"
)

func TestDefaultChatServicePost(t *testing.T) {
	httpmock.Activate()
	defer httpmock.DeactivateAndReset()

	chatService := &DefaultChatService{
		&http.Client{},
		SLACK_DUMMY_TOKEN,
		"https://slack.com/api",
	}

	jsonResponse := `{
	    "ok": true,
	    "channel": "C1H9RESGL",
	    "ts": "1503435956.000247",
	    "message": {
	        "text": "Here's a message for you",
	        "username": "ecto1",
	        "bot_id": "B19LU7CSY",
	        "attachments": [
	            {
	                "text": "This is an attachment",
	                "id": 1,
	                "fallback": "This is an attachment's fallback"
	            }
	        ],
	        "type": "message",
	        "subtype": "bot_message",
	        "ts": "1503435956.000247"
	    }
	}`

	errorResponse := `{
	    "ok": false,
	    "error": "channel_not_found"
	}`

	endpoint_url := "https://slack.com/api/chat.postMessage"

	message := PostChatMessage{
	    Channel: "C1H9RESGL",
	    Text: "Here's a message for you",
	    AsUser: true,
	    Attachments: []Attachment{
	    	Attachment{Text: "This is an attachment", Fallback: "This is an attachment's fallback",},
	    },			
	}

	httpmock.RegisterResponder("POST", endpoint_url,
	func(req *http.Request) (*http.Response, error) {
		checkAuthorization(req, t)

		var result PostChatMessage
		json.NewDecoder(req.Body).Decode(&result)

		if result.Channel != "C1H9RESGL" {
			return httpmock.NewStringResponse(200, errorResponse), nil
		} 
		
		if !reflect.DeepEqual(result, message) {
			t.Errorf("got %#v, want %#v", result, message)
		}



		return httpmock.NewStringResponse(200, jsonResponse), nil
	})


	resp, err := chatService.Post(message)
	if err != nil {
		t.Error(err)
	}

	expectedMessage := "Here's a message for you" 
	if resp.Text !=  expectedMessage {
		t.Errorf("got %q, want %q", resp.Text, expectedMessage)
	}

	gotAttach := len(resp.Attachments)
	expectedAttach := 1
	if gotAttach != expectedAttach {
		t.Errorf("got %d, want %d attachments", gotAttach, expectedAttach)
	}

	message.Channel = "NonExistingChannelId"
	resp, err = chatService.Post(message)
    if err == nil {
        t.Error("Expected channel not found error")
    }

    if err.Error() != "channel_not_found" {
        t.Errorf("Expected `channel_not_found` error got %q", err)
    }  	

	info := httpmock.GetCallCountInfo()
	if info[fmt.Sprintf("POST %s", endpoint_url)] != 2 {
		t.Errorf("%s called 0 times expected 2", endpoint_url)
	}
}

func TestDefaultChatServiceUpdate(t *testing.T) {
	httpmock.Activate()
	defer httpmock.DeactivateAndReset()

	chatService := &DefaultChatService{
		&http.Client{},
		SLACK_DUMMY_TOKEN,
		"https://slack.com/api",
	}

	jsonResponse := `{
	    "ok": true,
	    "channel": "C024BE91L",
	    "ts": "1401383885.000061",
	    "text": "Updated text you carefully authored"
	}`

	errorResponse := `{
	    "ok": false,
	    "error": "channel_not_found"
	}`

	endpoint_url := "https://slack.com/api/chat.update"

	message := UpdateChatMessage{
	    Channel: "C1H9RESGL",
	    Text: "Updated text you carefully authored",
	    Ts: "1401383885.000061",
	    AsUser: true,		
	}

	httpmock.RegisterResponder("POST", endpoint_url,
	func(req *http.Request) (*http.Response, error) {
		checkAuthorization(req, t)

		var result UpdateChatMessage
		json.NewDecoder(req.Body).Decode(&result)

		if result.Channel != "C1H9RESGL" {
			return httpmock.NewStringResponse(200, errorResponse), nil
		} 
		
		if !reflect.DeepEqual(result, message) {
			t.Errorf("got %#v, want %#v", result, message)
		}

		return httpmock.NewStringResponse(200, jsonResponse), nil
	})


	ts, text, err := chatService.Update(message)
	if err != nil {
		t.Error(err)
	}

	expectedTs := "1401383885.000061"
	if ts != expectedTs {
		t.Errorf("got %q, want %q", ts, expectedTs)
	}

	expectedMessage := "Updated text you carefully authored" 
	if text !=  expectedMessage {
		t.Errorf("got %q, want %q", text, expectedMessage)
	}


	message.Channel = "NonExistingChannelId"
	_, _, err = chatService.Update(message)
    if err == nil {
        t.Error("Expected channel not found error")
    }

    if err.Error() != "channel_not_found" {
        t.Errorf("Expected `channel_not_found` error got %q", err)
    }  	

	info := httpmock.GetCallCountInfo()
	if info[fmt.Sprintf("POST %s", endpoint_url)] != 2 {
		t.Errorf("%s called 0 times expected 2", endpoint_url)
	}
}

