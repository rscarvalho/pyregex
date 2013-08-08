#!/usr/bin/env bash

run_with_retry() {
    MAX_RETRIES=$1
    shift
    NUM_RETRIES=1

    echo "Max Retries: $MAX_RETRIES"

    CMD=$*

    while [ $NUM_RETRIES -le $(( MAX_RETRIES )) ]; do
        echo "Running $CMD..."
        $CMD
        status=$?

        if [ $status -eq 0 ]; then 
            break
        else 
            NUM_RETRIES=$(( NUM_RETRIES+1 ))
        fi
    done

    if [ $NUM_RETRIES -eq $(( MAX_RETRIES )) ]; then
        echo "npm install failed."
        exit -1
    fi
}

NPM_ARGS="-s"
if [[ "${NODE_ENV}" == "production" ]]; then
    NPM_ARGS="${NPM_ARGS} --production"
fi

run_with_retry 3 npm install -g ${NPM_ARGS} karma bower grunt-cli &&

run_with_retry 3 npm install ${NPM_ARGS} &&

run_with_retry 3 bower install -q

exit $?