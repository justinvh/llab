llab
----

A lightweight lab for Git Development.

This project is trying to be a low-dependency Github-like clone. It is
growing out of the efforts that I have seen needed in an industrial company
where management of tasks and requirements is a bit more involved.


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
