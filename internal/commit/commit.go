package commit

import (
	"github.com/pkg/errors"
	"strings"
)

var (
	HexShaMandatoryError = errors.New("hexsha_manadatory")
	EmptyCommitError     = errors.New("empty_commit")
)

type Commit struct {
	Hexsha  string
	Summary string
	Author  string
}

func New(hexsha, summary, author string) (Commit, error) {
	if hexsha == "" && summary == "" && author == "" {
		return Commit{}, EmptyCommitError
	} else if strings.TrimSpace(hexsha) == "" {
		return Commit{}, HexShaMandatoryError
	}

	return Commit{hexsha, summary, author}, nil
}

type CommitsGetter interface {
	GetCommits(repo_id interface{}, old_commit, new_commit string) ([]Commit, error)
	GetSingle(repo_id interface{}, commit string) (Commit, error)
}
