llab
----

A lightweight lab for Git Development.


Building
--------

  ```shell
  $ git clone http://github.com/justinvh/llab.git
  $ virtualenv $PATH_TO_YOUR_VENVS/llab
  $ source $PATH_TO_YOUR_VENVS/lab/bin/activate
  $ cd llab
  $ pip install -r requirements
  $ source env.bash
  ```


Server Side
-----------

You can run llab in two authentication modes.

    - Customized OpenSSH Backend
    - Flat authorized_users

Each backend has their own benefit.
