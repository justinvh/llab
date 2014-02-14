Project Scripts
---------------

This folder contains a number of scripts for running llab. 
Some are convenience, while others are necessities. This file will provide a
breakdown of the scripts as they are added.

SSH Breakdown
-------------

There is currently no automation for the SSH commands.

```
$ cat $GIT_USER/.ssh/authorized_keys

command="source env.bash; llab --ssh --user 1 $SSH_ORIGINAL_COMMAND",no-port-forwarding,no-x11-forwarding,no-agent-forwarding SSH_TYPE SSH_KEY SSH_USER
```

The env.bash is just a hack for:

```
$ cat $HOME/env.bash

source $VENV/llab/bin/activate
cd $PROJECT/llab
source env.bash
```
