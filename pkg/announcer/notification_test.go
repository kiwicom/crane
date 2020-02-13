package announcer

import "testing"
import "reflect"
import "fmt"
import "time"
import "github.com/kiwicom/crane/internal/commit"

func TestNewNotification(t *testing.T) {
	now := time.Now()
	var tests = []struct {
		name string
		in   []NotificationOption
		out  *Notification
	}{
		{"WithChannels", []NotificationOption{WithChannels("release")},
			&Notification{
				Channels:  []string{"release"},
				Message:   "",
				Commits:   []commit.Commit{},
				Timestamp: "",
			},
		},
		{"WithMessage", []NotificationOption{WithMessage("Hello, release!")},
			&Notification{
				Channels:  []string{},
				Message:   "Hello, release!",
				Commits:   []commit.Commit{},
				Timestamp: "",
			},
		},
		{"WithTimestamp_NullParameter", []NotificationOption{WithTimestamp(now)},
			&Notification{
				Channels:  []string{},
				Message:   "",
				Commits:   []commit.Commit{},
				Timestamp: fmt.Sprintf("%d", now.Unix()*1000),
			},
		},
		{"WithCommits", []NotificationOption{WithCommits(commit.Commit{"sha1", "summary1", "author1", now},
			commit.Commit{"sha2", "summary2", "author2", now},
			commit.Commit{"sha3", "summary3", "author3", now})},
			&Notification{
				Channels: []string{},
				Message:  "",
				Commits: []commit.Commit{commit.Commit{"sha1", "summary1", "author1", now},
					commit.Commit{"sha2", "summary2", "author2", now},
					commit.Commit{"sha3", "summary3", "author3", now}},
				Timestamp: "",
			},
		},
		{"Misc", []NotificationOption{WithChannels("release", "staging"), WithMessage("release text")},
			&Notification{
				Channels:  []string{"release", "staging"},
				Message:   "release text",
				Commits:   []commit.Commit{},
				Timestamp: "",
			},
		},
		{"NoArgs", nil, &Notification{Channels: []string{}, Message: "", Commits: []commit.Commit{}, Timestamp: ""}},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := NewNotification(tt.in...)
			if !reflect.DeepEqual(got, tt.out) {
				t.Errorf("got %q, want %q", got, tt.out)
			}
		})
	}
}
