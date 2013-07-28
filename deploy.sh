#!/usr/bin/env bash

deploy_branch='stable'
current_branch=$(git branch | grep '*' | sed -e 's/^\* *//')

# Only deploy from the stable branch
if [[ "$current_branch" != "$deploy_branch" ]]; then
    echo "You cannot deploy from branch \"$current_branch\"." >&2
    exit 0
fi

# Set default path for the Google AppEngine SDK
if [[ -z "$APPENGINE_SDK_PATH" ]]; then
    APPENGINE_SDK_PATH='/usr/local/bin'
fi

echo "Using AppEgine SDK at \"${APPENGINE_SDK_PATH}\""

if [[ -z "$APPENGINE_PASSWORD" || -z "$APPENGINE_EMAIL" ]]; then
    echo "ERROR: Please set APPENGINE_EMAIL and APPENGINE_PASSWORD" >&2
    exit -1
fi

sudo ntpdate ntp.ubuntu.com
echo $APPENGINE_PASSWORD | $APPENGINE_SDK_PATH/appcfg.py update . -e $APPENGINE_EMAIL --passin

exit $?