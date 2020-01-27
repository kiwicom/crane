package commit

import (
	"fmt"

	"github.com/pkg/errors"
	"gopkg.in/src-d/go-git.v4"
	"gopkg.in/src-d/go-git.v4/plumbing"	
)

type LocalRepoCommitsGetter struct {}

func NewLocalRepoCommitsGetter() *LocalRepoCommitsGetter {
	return &LocalRepoCommitsGetter{}
}

func (gg *LocalRepoCommitsGetter) GetCommits(repo_id interface{}, old_commit, new_commit string) ([]Commit, error) {
	switch repo_path := repo_id.(type) {
	case string:
		r, err := git.PlainOpen(repo_path)
		if err != nil {
			return []Commit{}, errors.Wrap(err, "Failed to open local repository")
		}

		nch := plumbing.NewHash(new_commit)
		ci, err := r.Log(&git.LogOptions{From: nch})
		if err != nil {
			return []Commit{}, errors.Wrap(err, "Failed to fetch commits")	
		}

		commits := []Commit{}

		och := plumbing.NewHash(old_commit)
		for c, err := ci.Next(); err == nil; {
			if err != nil {
				return []Commit{}, errors.Wrap(err, "Error fetching commit")
			}

			cmt := Commit{
				Hexsha: c.Hash.String(),
				Summary: c.Message,
				Author: fmt.Sprintf("%s <%s>", c.Author.Name, c.Author.Email),
			}
			commits = append(commits, cmt)

			if c.Hash == och {
				break		
			}	

			c, err = ci.Next()		
		}

		return commits, nil
	default:
		return []Commit{}, errors.New("repo_id must should be a string path to the local repository")
	} 
}

func (gg *LocalRepoCommitsGetter) GetSingle(repo_id interface{}, commit_sha string) (Commit, error) {
	switch repo_path := repo_id.(type) {
	case string:
		r, err := git.PlainOpen(repo_path)
		if err != nil {
			return Commit{}, errors.Wrap(err, "Failed to open local repository")
		}

		cs := plumbing.NewHash(commit_sha)
		co, err := r.CommitObject(cs)
		if err != nil {
			return Commit{}, errors.Wrap(err, "Commit not found")
		}

		result := Commit{
			Hexsha: co.Hash.String(),
			Summary: co.Message,
			Author: fmt.Sprintf("%s <%s>", co.Author.Name, co.Author.Email),
		}

		return result, nil
	default:
		return Commit{}, errors.New("repo_id must should be a string path to the local repository")
	}
}