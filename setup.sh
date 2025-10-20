#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ENV_AIIINOTATE="$SCRIPT_DIR/.env.aiiinotate";

git submodule init && git submodule update;

# setup aiiinotate
if [ ! -f "$SCRIPT_DIR"/.env.aiiinotate ];
then echo "'.env.aiiinotate' file not found at '$SCRIPT_DIR'. exiting." && exit 1;
fi;

cp "$ENV_AIIINOTATE" "$SCRIPT_DIR/aiiinotate/src/config/.env";

cd "$SCRIPT_DIR/aiiinotate";
bash setup.sh;

cd "$SCRIPT_DIR";

# setup sas (useless, no setup needed)
# cd "$SCRIPT_DIR/SimpleAnnotationServer";
# mvn jetty:run;

