package commit

import (
    "fmt"

    "github.com/pkg/errors"
    "github.com/xanzy/go-gitlab"
)
type GitlabCommitsGetter struct {
    git *gitlab.Client
}

func NewGitlabCommitsGetter(gitlab_token string) *GitlabCommitsGetter {
    git := gitlab.NewClient(nil, gitlab_token)
    git.SetBaseURL("https://gitlab.skypicker.com/")
    return &GitlabCommitsGetter{git}
}

func (g *GitlabCommitsGetter) GetCommits(repo_id interface{}, old_commit, new_commit string) ([]Commit, error) {
    if old_commit == "" || new_commit == "" {
        return []Commit{}, errors.New("Commit sha can't be empty")
    }

    commit_range := fmt.Sprintf("%s...%s", old_commit, new_commit)
    opts := &gitlab.ListCommitsOptions{RefName: &commit_range}
    commits, _, err := g.git.Commits.ListCommits(repo_id, opts)
    if err != nil {
        return []Commit{}, errors.Wrap(err, "Commits not found")
    }

    var result []Commit
    for _, cmt := range commits {
        author := fmt.Sprintf("%s <%s>", cmt.AuthorName, cmt.AuthorEmail)
        c, err := New(cmt.ID, cmt.Message, author)
        if err != nil {
            return []Commit{}, errors.Wrap(err, "Error fetching commits!")
        }

        result = append(result, c)
    }
    return result, nil
}

func (g *GitlabCommitsGetter) GetSingle(repo_id interface{}, commit_sha string) (Commit, error) {
    if commit_sha == "" {
        return Commit{}, errors.New("commit_sha can't be empty")
    }
    
    cmt, _, err := g.git.Commits.GetCommit(repo_id, commit_sha)
    if err != nil {
        return Commit{}, errors.New("Error fetching commit!")
    }

    author := fmt.Sprintf("%s <%s>", cmt.AuthorName, cmt.AuthorEmail)
    return New(cmt.ID, cmt.Message, author)
}