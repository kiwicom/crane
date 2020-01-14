package announcer

import (
    "github.com/pkg/errors"
    "github.com/kiwicom/crane/internal/slack"
)

type SlackAnnouncer struct {
    client *slack.Client
}

func NewSlackAnnouncer(slack_token string) (*SlackAnnouncer, error) {
    client, err := slack.NewClient(slack_token)
    if err != nil {
    	return nil, errors.Wrap(err, "Error creating slack client")
    }
    
    return &SlackAnnouncer{client}, nil
}

func (n *SlackAnnouncer) Publish(note *Notification) (bool, error) {
    return false, errors.New("NotImplemented") 
}

func (n *SlackAnnouncer) Update(note *Notification) (bool, error) {
    return false, errors.New("NotImplemented")
}