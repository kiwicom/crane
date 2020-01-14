package slack


import (
	"fmt"
	"time"
	"testing"
	"reflect"
	"net/http"

	"github.com/jarcoal/httpmock"
)

func TestDefaultChannelServiceList(t *testing.T) {
	httpmock.Activate()
	defer httpmock.DeactivateAndReset()

	channelService := &DefaultChannelService{
		&http.Client{},
		SLACK_DUMMY_TOKEN,
		"https://slack.com/api",
	}

	jsonResponse := `{
	    "ok": true,
	    "channels": [
	        {
	            "id": "C0G9QF9GW",
	            "name": "random",
	            "is_channel": true,
	            "created": 1449709280,
	            "creator": "U0G9QF9C6",
	            "is_archived": false,
	            "is_general": false,
	            "name_normalized": "random",
	            "is_shared": false,
	            "is_org_shared": false,
	            "is_member": true,
	            "is_private": false,
	            "is_mpim": false,
	            "members": [
	                "U0G9QF9C6",
	                "U0G9WFXNZ"
	            ],
	            "topic": {
	                "value": "Other stuff",
	                "creator": "U0G9QF9C6",
	                "last_set": 1449709352
	            },
	            "purpose": {
	                "value": "A place for non-work-related flimflam, faffing, hodge-podge or jibber-jabber you'd prefer to keep out of more focused work-related channels.",
	                "creator": "",
	                "last_set": 0
	            },
	            "previous_names": [],
	            "num_members": 2
	        },
	        {
	            "id": "C0G9QKBBL",
	            "name": "general",
	            "is_channel": true,
	            "created": 1449709280,
	            "creator": "U0G9QF9C6",
	            "is_archived": false,
	            "is_general": true,
	            "name_normalized": "general",
	            "is_shared": false,
	            "is_org_shared": false,
	            "is_member": true,
	            "is_private": false,
	            "is_mpim": false,
	            "members": [
	                "U0G9QF9C6",
	                "U0G9WFXNZ"
	            ],
	            "topic": {
	                "value": "Talk about anything!",
	                "creator": "U0G9QF9C6",
	                "last_set": 1449709364
	            },
	            "purpose": {
	                "value": "To talk about anything!",
	                "creator": "U0G9QF9C6",
	                "last_set": 1449709334
	            },
	            "previous_names": [],
	            "num_members": 2
	        }
	    ],
	    "response_metadata": {
	        "next_cursor": "dGVhbTpDMUg5UkVTR0w="
	    }
	}`

	endpoint_url := "https://slack.com/api/channels.list"

	httpmock.RegisterResponder("GET", endpoint_url,
	func(req *http.Request) (*http.Response, error) {
		checkAuthorization(req, t)

		return httpmock.NewStringResponse(200, jsonResponse), nil
	})

	resp, err := channelService.List()
	if err != nil {
		t.Error(err)
	}

	info := httpmock.GetCallCountInfo()
	if info[fmt.Sprintf("GET %s", endpoint_url)] != 1 {
		t.Errorf("%s called 0 times expected 1", endpoint_url)
	}


	if len(resp) == 0 {
        t.Error("Got empty list of channels, expected non empty!")
    }

    expected := []Channel{
    	{"C0G9QF9GW", "random"} ,
    	{"C0G9QKBBL", "general"},
    }

    if !reflect.DeepEqual(resp, expected) {
    	t.Errorf("got %q, want %q", resp, expected)
    }

}

func TestDefaultChannelServiceInfo(t *testing.T) {
    httpmock.Activate()
    defer httpmock.DeactivateAndReset()

	channelService := &DefaultChannelService{
		&http.Client{},
		SLACK_DUMMY_TOKEN,
		"https://slack.com/api",
	}

    jsonResponse := `{
        "ok": true,
        "channel": {
            "id": "C1H9RESGL",
            "name": "busting",
            "is_channel": true,
            "created": 1466025154,
            "creator": "U0G9QF9C6",
            "is_archived": false,
            "is_general": false,
            "name_normalized": "busting",
            "is_shared": false,
            "is_org_shared": false,
            "is_member": true,
            "is_private": false,
            "is_mpim": false,
            "last_read": "1503435939.000101",
            "latest": {
                "text": "Containment unit is 98% full",
                "username": "ecto1138",
                "bot_id": "B19LU7CSY",
                "attachments": [
                    {
                        "text": "Don't get too attached",
                        "id": 1,
                        "fallback": "This is an attachment fallback"
                    }
                ],
                "type": "message",
                "subtype": "bot_message",
                "ts": "1503435956.000247"
            },
            "unread_count": 1,
            "unread_count_display": 1,
            "members": [
                "U0G9QF9C6",
                "U1QNSQB9U"
            ],
            "topic": {
                "value": "Spiritual containment strategies",
                "creator": "U0G9QF9C6",
                "last_set": 1503435128
            },
            "purpose": {
                "value": "Discuss busting ghosts",
                "creator": "U0G9QF9C6",
                "last_set": 1503435128
            },
            "previous_names": [
                "dusting"
            ]
        }
    }`

    jsonErrorResponse := `{
        "ok": false,
        "error": "channel_not_found"
    }`

    endpoint_url := "https://slack.com/api/channels.info"
    httpmock.RegisterResponder("GET", endpoint_url,
    func(req *http.Request) (*http.Response, error) {
        checkAuthorization(req, t)

        channel := req.URL.Query().Get("channel")
        if channel == "" {
            t.Error("Expected channel parameter found none!")
        }

        if channel == "C1H9RESGL" {
            return httpmock.NewStringResponse(200, jsonResponse), nil
        }

        return httpmock.NewStringResponse(200, jsonErrorResponse), nil
    })

    resp, err := channelService.Info("C1H9RESGL")
    if err != nil {
        t.Error(err)
    }

    expected := Channel{"C1H9RESGL", "busting"}

    if !reflect.DeepEqual(resp, expected) {
        t.Errorf("got %q, want %q", resp, expected)
    }

    resp, err = channelService.Info("NonExistingChannelId")
    if err == nil {
        t.Error("Expected channel not found error")
    }

    if err.Error() != "channel_not_found" {
        t.Errorf("Expected `channel_not_found` error got %q", err)
    }
    
    info := httpmock.GetCallCountInfo()

    called := info[fmt.Sprintf("GET %s", endpoint_url)]
    expected_called := 2

    if called != expected_called {
        t.Errorf("%s cexpected to be called %d times got %d ", endpoint_url, expected_called, called)
    }

}

func TestDefaultChannelServiceHistory_Response(t *testing.T) {
    httpmock.Activate()
    defer httpmock.DeactivateAndReset()

	channelService := &DefaultChannelService{
		&http.Client{},
		SLACK_DUMMY_TOKEN,
		"https://slack.com/api",
	}

    jsonResponse := `{
        "ok": true,
        "messages": [
            {
                "type": "message",
                "ts": "1358546515.000008",
                "user": "U2147483896",
                "text": "Hello"
            },
            {
                "type": "message",
                "ts": "1358546515.000007",
                "user": "U2147483896",
                "text": "World",
                "is_starred": true,
                "reactions": [
                    {
                        "name": "space_invader",
                        "count": 3,
                        "users": [
                            "U1",
                            "U2",
                            "U3"
                        ]
                    },
                    {
                        "name": "sweet_potato",
                        "count": 5,
                        "users": [
                            "U1",
                            "U2",
                            "U3",
                            "U4",
                            "U5"
                        ]
                    }
                ]
            },
            {
                "type": "something_else",
                "ts": "1358546515.000007"
            },
            {
                "text": "Containment unit is 98% full",
                "username": "ecto1138",
                "bot_id": "B19LU7CSY",
                "attachments": [
                    {
                        "text": "Don't get too attached",
                        "id": 1,
                        "fallback": "This is an attachment fallback"
                    }
                ],
                "type": "message",
                "subtype": "bot_message",
                "ts": "1503435956.000247"
            }
        ],
        "has_more": false
    }`

    jsonErrorResponse := `{
        "ok": false,
        "error": "channel_not_found"
    }`

    endpoint_url := "https://slack.com/api/channels.history"
    httpmock.RegisterResponder("GET", endpoint_url,
    func(req *http.Request) (*http.Response, error) {
        checkAuthorization(req, t)

        channel := req.URL.Query().Get("channel")
        if channel == "" {
            t.Error("Expected channel parameter found none!")
        }

        if channel != "C1H9RESGL" {
            return httpmock.NewStringResponse(200, jsonErrorResponse), nil
        }

        return httpmock.NewStringResponse(200, jsonResponse), nil
    })  

    resp, err := channelService.History("C1H9RESGL", nil)
    if err != nil {
        t.Error(err)
    }

    expected := []Message{
            Message{
                Type:"message", 
                User:"U2147483896", 
                Text:"Hello", 
                IsStarred:false, 
                Reactions:[]Reaction(nil), 
                Attachments:[]Attachment(nil), 
                Ts:"1358546515.000008",
            }, 
            Message{
                Type:"message", 
                User:"U2147483896", 
                Text:"World", 
                IsStarred:true, 
                Reactions:[]Reaction{
                    Reaction{
                        Name:"space_invader", 
                        Count:3, 
                        Users:[]string{"U1", "U2", "U3"},
                    }, 
                    Reaction{
                        Name:"sweet_potato", 
                        Count:5, 
                        Users:[]string{"U1", "U2", "U3", "U4", "U5"},
                    },
                }, 
                Attachments:[]Attachment(nil), 
                Ts:"1358546515.000007",
            }, 
            Message{
                Type:"something_else", 
                User:"", 
                Text:"", 
                IsStarred:false, 
                Reactions:[]Reaction(nil), 
                Attachments:[]Attachment(nil), 
                Ts:"1358546515.000007",
            }, 
            Message{
                Type:"message", 
                User:"", 
                Text:"Containment unit is 98% full", 
                IsStarred:false, Reactions:[]Reaction(nil), 
                Attachments:[]Attachment{
                    Attachment{
                        Color:"", 
                        Fallback:"This is an attachment fallback", 
                        Text:"Don't get too attached", 
                        AuthorIcon:"", 
                        AuthorLink:"", 
                        AuthorName:"", 
                        Fields:[]Field(nil), 
                        Footer:"", 
                        FooterIcon:"", 
                        ImageUrl:"", 
                        MrkdwnIn:[]string(nil), 
                        Pretext:"", 
                        ThumbUrl:"", 
                        Title:"", 
                        TitleLink:"", 
                        Ts:"",
                    },
                }, 
                Ts:"1503435956.000247",
            },
        }

    if !reflect.DeepEqual(resp, expected) {
        t.Errorf("got %v, want %v", resp, expected)
    }


    resp, err = channelService.History("NonExistingChannelId", nil)
    if err == nil {
        t.Error("Expected channel not found error")
    }

    if err.Error() != "channel_not_found" {
        t.Errorf("Expected `channel_not_found` error got %q", err)
    }   

    info := httpmock.GetCallCountInfo()

    called := info[fmt.Sprintf("GET %s", endpoint_url)]
    expected_called := 2

    if called != expected_called {
        t.Errorf("%s cexpected to be called %d times got %d ", endpoint_url, expected_called, called)
    }   
}


func TestSlackApiChannelHistory_UrlFormating(t *testing.T) {
    now := time.Now()
    yesterday := now.Add(-24 * time.Hour)

    channelService := &DefaultChannelService{
		&http.Client{},
		SLACK_DUMMY_TOKEN,
		"https://slack.com/api",
	}

    var tests = []struct {
        name string
        channel_id string
        opts *ChannelHistoryListOptions
        out string
    }{
        {"ChannelHistoryDefaultSearchOptions", "dummy_channel", 
            nil, "https://slack.com/api/channels.history?channel=dummy_channel",},
        {"ChannelHistoryAllSearchOptions", "dummy_channel",
            &ChannelHistoryListOptions{50, true, &now, &yesterday, true},
            fmt.Sprintf(
                "https://slack.com/api/channels.history?channel=dummy_channel&count=50&inclusive=1&latest=%d&oldest=%d&unreads=1",
                MakeTimestamp(&now), MakeTimestamp(&yesterday)),},
        {"ChannelHistoryInclusiveSearchOptions", "dummy_channel",
            &ChannelHistoryListOptions{0, true, nil, nil, false},
            "https://slack.com/api/channels.history?channel=dummy_channel&inclusive=1"},
        {"ChannelHistoryLatestSearchOptions", "dummy_channel",
            &ChannelHistoryListOptions{0, false, &now, nil, false},
            fmt.Sprintf("https://slack.com/api/channels.history?channel=dummy_channel&latest=%d", MakeTimestamp(&now)),},
        {"ChannelHistoryInclusiveLatestUnreadsSearchOptions", "dummy_channel",
            &ChannelHistoryListOptions{0, true, &now, nil, true},
            fmt.Sprintf(
                "https://slack.com/api/channels.history?channel=dummy_channel&inclusive=1&latest=%d&unreads=1", 
                MakeTimestamp(&now)),},
        {"ChannelHistoryCountSearchOptions", "dummy_channel",
            &ChannelHistoryListOptions{45, false, nil, nil, false},
            "https://slack.com/api/channels.history?channel=dummy_channel&count=45"},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            httpmock.Activate()
            defer httpmock.DeactivateAndReset()

            endpoint_url := "https://slack.com/api/channels.history"
            httpmock.RegisterResponder("GET", endpoint_url,
            func(req *http.Request) (*http.Response, error) {
                checkAuthorization(req, t)

                got := req.URL.String()
                if got != tt.out {
                    t.Errorf("got %q, want %q", got, tt.out)
                }

                return httpmock.NewStringResponse(200, "ok"), nil
            })

            channelService.History(tt.channel_id, tt.opts)           
        })
    }
}