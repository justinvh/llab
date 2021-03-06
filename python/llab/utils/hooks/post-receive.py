#!/usr/bin/env python
import sys
import os
import django

django.setup()


from project.models import Project
from account.models import User


# Determine the project being executed
push_user_pk = os.environ['SSH_USER']
location = os.path.dirname(os.path.abspath(__file__)).split(os.sep)
username, repository = location[-3:-1]

project = Project.objects.get(name=repository, owner__username=username)
push_user = User.objects.get(pk=push_user_pk)

for line in sys.stdin.readlines():
    old_rev, new_rev, refname = line.replace('\n', '').split(' ')
    branch = refname.split('/')[-1].strip()
    project.post_receive(old_rev, new_rev, refname, branch, push_user)
