package announcer

type Result int

const (
	Ok Result = iota
	Error
)

func (r Result) String() string {
	names := [...]string{"Ok", "Error"}

	if r < Ok || r > Error {
		return "Unknown"
	}

	return names[r]
}

func (r Result) IsErr() bool {
	return !r.IsOk()
}

func (r Result) IsOk() bool {
	return r == Ok
}

type Response struct {
	Response Result
	Err      error
}

type Announcer interface {
	Start(note *Notification) Response
	Success(note *Notification) Response
	Failure(note *Notification) Response
}
