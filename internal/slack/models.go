package slack

type ApiBase struct {
	Ok    bool   `json:"ok"`
	Error string `json:"error"`
}

type Message struct {
	Type        string       `json:"type"`
	User        string       `json:"user"`
	Text        string       `json:"text"`
	IsStarred   bool         `json:"is_starred"`
	Reactions   []Reaction   `json:"reactions"`
	Attachments []Attachment `json:"attachments"`
	Ts          string       `json:"ts"`
}

type Reaction struct {
	Name  string   `json:"name"`
	Count int      `json:"count"`
	Users []string `json:"users"`
}

type Attachment struct {
	Color      string   `json:"color"`
	Fallback   string   `json:"fallback"`
	Text       string   `json:"text"`
	AuthorIcon string   `json:"author_icon"`
	AuthorLink string   `json:"author_link"`
	AuthorName string   `json:"author_name"`
	Fields     []Field  `json:"fields"`
	Footer     string   `json:"footer"`
	FooterIcon string   `json:"footer_icon"`
	ImageUrl   string   `json:"image_url"`
	MrkdwnIn   []string `json:"mrkdwn_in"`
	Pretext    string   `json:"pretext"`
	ThumbUrl   string   `json:"thumb_url"`
	Title      string   `json:"title"`
	TitleLink  string   `json:"title_link"`
	Ts         string   `json:"ts"`
}

type Field struct {
	Title string `json:"title"`
	Value string `json:"value"`
	Short bool   `json:"short"`
}

type Channel struct {
	Id   string `json:"id"`
	Name string `json:"name"`
}
