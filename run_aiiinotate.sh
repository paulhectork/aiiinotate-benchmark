#/usr/bin/env/ bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd );
ENV_PATH="$SCRIPT_DIR/aiiinotate/src/config/.env"; 

if [ ! -f $ENV_PATH ];
then echo ".env file not found in aiiinotate (at '$ENV_PATH'). exiting." && exit 1;
fi;

cd "$SCRIPT_DIR/aiiinotate";
npm run start
