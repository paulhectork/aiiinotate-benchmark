#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ENV_AIIINOTATE="$SCRIPT_DIR/.env.aiiinotate";
VENV_DIR="$SCRIPT_DIR/venv"

git submodule init && git submodule update;

# setup venv
if [ ! -d "$VENV_DIR" ];
then python3.10 -m venv venv;
fi;
source "$VENV_DIR"/bin/activate;
pip install -r requirements.txt;

# setup aiiinotate
if [ ! -f "$SCRIPT_DIR"/.env.aiiinotate ];
then echo "'.env.aiiinotate' file not found at '$SCRIPT_DIR'. exiting." && exit 1;
fi;
cp "$ENV_AIIINOTATE" "$SCRIPT_DIR/aiiinotate/src/config/.env";
cd "$SCRIPT_DIR/aiiinotate";
bash setup.sh;

cd "$SCRIPT_DIR";

