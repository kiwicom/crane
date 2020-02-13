package commit

import (
	"fmt"

	"github.com/pkg/errors"
	"gopkg.in/src-d/go-git.v4"
	"gopkg.in/src-d/go-git.v4/plumbing"
)

var (
	ErrRepoIdMustBeAPath = errors.New("repo_id must be a string and its assumed to be a path to the local repository")
)

type LocalRepoCommitsGetter struct {}

func NewLocalRepoCommitsGetter() *LocalRepoCommitsGetter {
	return &LocalRepoCommitsGetter{}
}

func (gg *LocalRepoCommitsGetter) GetCommits(repoId interface{}, oldCommit, newCommit string) ([]Commit, error) {
	switch repo_path := repoId.(type) {
	case string:
		r, err := git.PlainOpen(repo_path)
		if err != nil {
			return []Commit{}, errors.Wrap(err, "Failed to open local repository")
		}

		nch := plumbing.NewHash(newCommit)
		ci, err := r.Log(&git.LogOptions{From: nch})
		if err != nil {
			return []Commit{}, errors.Wrap(err, "Failed to fetch commits")
		}

		commits := []Commit{}

		och := plumbing.NewHash(oldCommit)
		for c, err := ci.Next(); err == nil; {
			cmt := Commit{
				Hexsha: c.Hash.String(),
				Summary: c.Message,
				Author: fmt.Sprintf("%s <%s>", c.Author.Name, c.Author.Email),
				At: c.Committer.When,
			}
			commits = append(commits, cmt)

			if c.Hash == och {
				break
			}

			c, err = ci.Next()
		}

		if err != nil {
			return []Commit{}, errors.Wrap(err, "Error fetching commit")
		}

		return commits, nil
	default:
		return []Commit{}, ErrRepoIdMustBeAPath
	}
}

func (gg *LocalRepoCommitsGetter) GetSingle(repoId interface{}, commitSha string) (Commit, error) {
	switch repo_path := repoId.(type) {
	case string:
		r, err := git.PlainOpen(repo_path)
		if err != nil {
			return Commit{}, errors.Wrap(err, "Failed to open local repository")
		}

		cs := plumbing.NewHash(commitSha)
		co, err := r.CommitObject(cs)
		if err != nil {
			return Commit{}, errors.Wrap(err, "Commit not found")
		}

		result := Commit{
			Hexsha: co.Hash.String(),
			Summary: co.Message,
			Author: fmt.Sprintf("%s <%s>", co.Author.Name, co.Author.Email),
			At: co.Committer.When,
		}

		return result, nil
	default:
		return Commit{}, ErrRepoIdMustBeAPath
	}
}

func (gg *LocalRepoCommitsGetter) GetHead(repoId interface{}) (Commit, error) {
	switch repo_path := repoId.(type) {
	case string:
		r, err := git.PlainOpen(repo_path)
		if err != nil {
			return Commit{}, errors.Wrap(err, "Failed to open local repository")
		}

		head, err := r.Head()
		if err != nil {
			return Commit{}, errors.Wrap(err, "Failed to get head commit!")
		}

		co, err := r.CommitObject(head.Hash())
		if err != nil {
			return Commit{}, errors.Wrap(err, "Commit not found")
		}

		result := Commit{
			Hexsha: co.Hash.String(),
			Summary: co.Message,
			Author: fmt.Sprintf("%s <%s>", co.Author.Name, co.Author.Email),
			At: co.Committer.When,
		}

		return result, nil
	default:
		return Commit{}, ErrRepoIdMustBeAPath
	}
}

func (gg *LocalRepoCommitsGetter) IsAncestor(repoId interface{}, firstSha, secondSha string) (bool, error) {
	switch repo_path := repoId.(type) {
	case string:
		r, err := git.PlainOpen(repo_path)
		if err != nil {
			return false, errors.Wrap(err, "Failed to open local repository")
		}

		fcs := plumbing.NewHash(firstSha)
		scs := plumbing.NewHash(secondSha)

		fco, err := r.CommitObject(fcs)
		if err != nil {
			return false, errors.Wrap(err, "Commit not found")
		}
		sco , err := r.CommitObject(scs)
		if err != nil {
			return false, errors.Wrap(err, "Commit not found")
		}

		return fco.IsAncestor(sco)
	default:
		return false, ErrRepoIdMustBeAPath
	}
}
