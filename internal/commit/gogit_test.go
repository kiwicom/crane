package commit

import (
	"testing"
)

func TestLocalRepoCommitsGetter(t *testing.T) {
	newCommitSha := "9d6792a8fa9fb40e13a20060ae0d57dee115e4d0"
	oldCommitSha := "a53c89ae30919af7556a28b660b997b8bf0df492"
	repoPath := "../../"

	commitsGetter := NewLocalRepoCommitsGetter()
	cs, err := commitsGetter.GetCommits(repoPath, oldCommitSha, newCommitSha)
	if err != nil {
		t.Error(err)
	} 

	for _, c := range cs {
		t.Logf("%#v\n", c)
	}

	if len(cs) != 3 {
		t.Errorf("got %q, want %q", len(cs), 3)
	}
}
