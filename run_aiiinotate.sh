#/usr/bin/env/ bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
AIIINOTATE_DIR="$SCRIPT_DIR/aiiinotate";
ENV_PATH="$SCRIPT_DIR/.env.aiiinotate";

if [ ! -f $ENV_PATH ];
then echo ".env file not found (at '$ENV_PATH'). exiting." && exit 1;
fi;

sudo systemctl start mongod;

set -a
source $ENV_PATH;
set +a

cd "$AIIINOTATE_DIR";
npm run start_prof -- serve prod;
