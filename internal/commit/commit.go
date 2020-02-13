package commit

import (
	"strings"
	"time"

	"github.com/pkg/errors"
)

var (
	ErrHexShaMandatory = errors.New("hexsha_manadatory")
	ErrEmptyCommit     = errors.New("empty_commit")
)

type Commit struct {
	Hexsha  string
	Summary string
	Author  string
	At time.Time
}

func New(hexsha, summary, author string, at time.Time) (Commit, error) {
	if hexsha == "" && summary == "" && author == "" {
		return Commit{}, ErrEmptyCommit
	} else if strings.TrimSpace(hexsha) == "" {
		return Commit{}, ErrHexShaMandatory
	}

	return Commit{hexsha, summary, author, at}, nil
}

type CommitsGetter interface {
	GetCommits(repoId interface{}, oldCommit, newCommit string) ([]Commit, error)
	GetSingle(repoId interface{}, commitSha string) (Commit, error)
	GetHead(repoId interface{}) (Commit, error)
	IsAncestor(repoid interface{}, firstSha, secondSha string) (bool, error)
}
