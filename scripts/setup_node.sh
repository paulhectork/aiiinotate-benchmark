#!/bin/env bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"


if ! command -v npm &> /dev/null; then
    echo "INSTALL NVM & NODE"
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh | bash
   export NVM_DIR=~/.nvm
   source ~/.nvm/nvm.sh
   nvm install 24
   node -v
   npm -v
fi

