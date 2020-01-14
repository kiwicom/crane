package announcer

import (
    "time"
    "fmt"
    "github.com/kiwicom/crane/internal/commit"
)

type Notification struct {
    Message string
    Channels []string
    Commits []commit.Commit
    Timestamp string
}

type NotificationOption func(*Notification)

func WithChannels(channels ...string) NotificationOption {
    return func(n *Notification) {
        var chs []string
        for _, channel := range channels {
            chs = append(chs, channel)
        }

        n.Channels = chs
    }
}

func WithMessage(text string) NotificationOption {
    return func(n *Notification) {
        n.Message = text
    }
}

func WithCommits(commits ...commit.Commit) NotificationOption {
    return func(n *Notification) {
        var cms []commit.Commit
        for _, commit := range commits {
            cms = append(cms, commit)
        }
        n.Commits = cms
    }
}

func WithTimestamp(now time.Time) NotificationOption {
    return func(n *Notification) {
        n.Timestamp = fmt.Sprintf("%d", now.Unix() * 1000)
    }
}

func NewNotification(opts ...NotificationOption) *Notification {
    n := &Notification{
        Channels: []string{},
        Message: "",
        Commits: []commit.Commit{},
        Timestamp: "",
    }

    for _, opt := range opts {
        opt(n)
    }

    return n
}