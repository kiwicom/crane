package announcer

import (
	"testing"
)

func TestAnnouncerResultEnumStringer(t *testing.T) {
	var tests = []struct {
		name string
		in   Result
		out  string
	}{
		{"Ok", Ok, "Ok"},
		{"Error", Error, "Error"},
		{"Unknown", Ok + 100, "Unknown"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := tt.in.String()
			if got != tt.out {
				t.Errorf("got %q, want %q", got, tt.out)
			}
		})
	}
}
