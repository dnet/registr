#!/usr/bin/env python

from pygit2 import Repository, GIT_SORT_REVERSE, GIT_SORT_TOPOLOGICAL
from time import time
from os import getpid
from functools import partial
import re

ISSUE_RE = re.compile(r'#([0-9]+)')
REF_FMT = 'refs/heads/registr-{time}-{pid}'

def shift(amount, repo_path):
    repo = Repository(repo_path)
    head = repo.lookup_reference('HEAD').resolve()
    adder = partial(add, amount=amount)
    changelog = dict()
    reference = REF_FMT.format(time=time(), pid=getpid())
    for commit in repo.walk(head.oid, GIT_SORT_REVERSE | GIT_SORT_TOPOLOGICAL):
        newmsg, nsubs = ISSUE_RE.subn(adder, commit.message)
        if nsubs != 0 or any(pnt.oid in changelog for pnt in commit.parents):
            parents = [changelog.get(c.oid, c.oid) for c in commit.parents]
            new_oid = repo.create_commit(reference, commit.author,
                    commit.committer, newmsg, commit.tree.oid, parents)
            changelog[commit.oid] = new_oid
    return changelog, reference

def add(match, amount):
    return '#{0}'.format(int(match.group(1)) + amount)
