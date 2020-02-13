package commit

import (
	"reflect"
	"testing"
	"time"
)

func TestCommitCreate(t *testing.T) {
	now := time.Now()
	var tests = []struct {
		name    string
		hexsha  string
		summary string
		author  string
		at time.Time
		out     Commit
		err     error
	}{
		{"AllAvailable", "sha1", "summary1", "author1", now, Commit{"sha1", "summary1", "author1", now}, nil},
		{"OnlyHexsha", "sha1", "", "", time.Time{}, Commit{"sha1", "", "", time.Time{}}, nil},
		{"HexshaMandatory", "", "summary", "author", now, Commit{}, ErrHexShaMandatory},
		{"EmptyCommit", "", "", "", now, Commit{}, ErrEmptyCommit},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := New(tt.hexsha, tt.summary, tt.author, tt.at)
			if err != tt.err {
				t.Errorf("got %q, want %q", err, tt.err)
			}
			if !reflect.DeepEqual(got, tt.out) {
				t.Errorf("got %q, want %q", got, tt.out)
			}
		})
	}
}
