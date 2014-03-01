llab
----

`llab` is a lightweight Github clone. It is currently immature and completly
in the development process, but you're more than welcome to try it out.

Current development features and topics:

    - Git SSH wrapper for managing users and dispatching commands
    - SSH Key management with AES cipher and SHA1 verification
    - Event streams with user and organizations
    - Repository creation on the server side


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
