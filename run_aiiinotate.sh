#/usr/bin/env/ bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
AIIINOTATE_DIR="$SCRIPT_DIR/aiiinotate";
ENV_PATH="$SCRIPT_DIR/.env.aiiinotate";

USAGE="bash run_aiinotate.sh [prof|clinic]?"

PROFILING="$1"
if [ "$PROFILING" != "" ] && [ "$PROFILING" != "prof" ] && [ "$PROFILING" != "clinic" ];
then
    echo ""
    echo "run_aiiinotate error: invalid value for \$1";
    echo "USAGE: $USAGE";
    echo "exiting...";
    exit 1;
fi;
if [ "$PROFILING" = "prof" ];
then aiiinotate_cmd="aiiinotate_prof"
elif [ "$PROFILING" = "clinic" ];
then aiiinotate_cmd="aiiinotate_clinic";
else aiiinotate_cmd="aiiinotate";
fi

if [ ! -f "$ENV_PATH" ];
then echo ".env file not found (at '$ENV_PATH'). exiting." && exit 1;
fi;

set -a
source "$ENV_PATH";
set +a

sudo systemctl start mongod;

cd "$AIIINOTATE_DIR";
# apply migrations and indexes, v. important to have realistic performance.
npm run aiiinotate -- migrate apply;
# run the app (with clinic profiling)
npm run $aiiinotate_cmd -- serve prod;
