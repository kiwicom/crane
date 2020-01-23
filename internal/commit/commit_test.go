package commit

import (
	"reflect"
	"testing"
)

func TestCommitCreate(t *testing.T) {
	var tests = []struct {
		name    string
		hexsha  string
		summary string
		author  string
		out     Commit
		err     error
	}{
		{"AllAvailable", "sha1", "summary1", "author1", Commit{"sha1", "summary1", "author1"}, nil},
		{"OnlyHexsha", "sha1", "", "", Commit{"sha1", "", ""}, nil},
		{"HexshaMandatory", "", "summary", "author", Commit{}, HexShaMandatoryError},
		{"EmptyCommit", "", "", "", Commit{}, EmptyCommitError},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := New(tt.hexsha, tt.summary, tt.author)
			if err != tt.err {
				t.Errorf("got %q, want %q", err, tt.err)
			}
			if !reflect.DeepEqual(got, tt.out) {
				t.Errorf("got %q, want %q", got, tt.out)
			}
		})
	}
}
