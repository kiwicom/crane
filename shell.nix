with import <nixpkgs> {};

stdenv.mkDerivation rec {
  name = "crane-go";
  version = "1.0-alpha";

  buildInputs = [
    go
    go-tools
    go-langserver
    go-motion
    neovim
    watchexec
  ];

  shellHook = ''
            set -v
            export GOPATH="$(pwd)/.go"
            export GOCACHE=""
            export GO111MODULE='on'
            export PATH=$GOPATH/bin:$PATH

            if [ ! -d $(pwd)/.go ]; then
               go mod download
            fi

            # Install some utilities
            go get -u -v github.com/mdempsky/gocode
            go get -u -v github.com/rogpeppe/godef
            go get -u -v github.com/godoctor/godoctor
            go get -u -v golang.org/x/tools/cmd/goimports
            go get -u -v golang.org/x/tools/cmd/gorename
            go get -u -v golang.org/x/tools/cmd/guru
            go get -u -v github.com/zmb3/gogetdoc

            set +v
  '';
}
