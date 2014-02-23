#!/usr/bin/env sh

if [[ -z $SSH_ORIGINAL_COMMAND ]]; then
    echo "Hi! Your public key was accepted, but there is no shell." 1>&2 
    exit
fi

source $LLAB_VENV_ACTIVATE
cd $LLAB_PROJECT_PATH
source env.bash

llab --sh --user $1 $SSH_ORIGINAL_COMMAND
