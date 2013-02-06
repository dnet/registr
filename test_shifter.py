#!/usr/bin/env python

from shifter import shift
from tempfile import mkdtemp
from operator import attrgetter
from shutil import rmtree
from pygit2 import init_repository, Repository, Signature
from time import time
from os import path, walk
import unittest

SIG = Signature('foo', 'foo@bar.tld', time(), 0)
REF = 'refs/heads/master'

class TestShifter(unittest.TestCase):
    def setUp(self):
        self.repo_path = mkdtemp('registr_test_shifter')
        init_repository(self.repo_path, True)

    def test_unaffected_with_0_amount(self):
        repo = self.get_repo()
        empty_tree = get_empty_tree_oid(repo)
        root = repo.create_commit(REF, SIG, SIG, 'root #1', empty_tree, [])
        repo.create_commit(REF, SIG, SIG, 'leaf #2', empty_tree, [root])
        del repo
        before = self.get_repo_filelist()
        changelog, _ = shift(0, self.repo_path)
        for old, new in changelog.iteritems():
            self.assertEqual(old, new)
        after = self.get_repo_filelist()
        self.assertEqual(before, after)

    def test_unaffected_without_issues(self):
        repo = self.get_repo()
        empty_tree = get_empty_tree_oid(repo)
        root = repo.create_commit(REF, SIG, SIG, 'root', empty_tree, [])
        repo.create_commit(REF, SIG, SIG, 'leaf', empty_tree, [root])
        del repo
        before = self.get_repo_filelist()
        changelog, _ = shift(42, self.repo_path)
        self.assertEqual(changelog, {})
        after = self.get_repo_filelist()
        self.assertEqual(before, after)

    def test_merged_tree(self):
        repo = self.get_repo()
        empty_tree = get_empty_tree_oid(repo)
        root = repo.create_commit(REF, SIG, SIG, 'root #1', empty_tree, [])
        leaf = repo.create_commit(REF, SIG, SIG, 'leaf #2', empty_tree, [root])
        side = repo.create_commit(REF, SIG, SIG, '#3 side', empty_tree, [root])
        repo.create_commit(REF, SIG, SIG, 'merge #4', empty_tree, [leaf, side])
        del repo
        changelog, reference = shift(10, self.repo_path)
        self.assertEqual(len(changelog), 4)
        repo = self.get_repo()
        registr_head = repo.lookup_reference(reference).resolve()
        commit = repo[registr_head.oid]
        self.assertEqual(commit.message, 'merge #14')
        self.assertEqual(len(commit.parents), 2)
        for parent in commit.parents:
            self.assertEqual(len(parent.parents), 1)
            self.assertEqual(parent.parents[0].message, 'root #11')
        c1, c2 = sorted(commit.parents, key=attrgetter('message'))
        self.assertEqual(c1.message, '#13 side')
        self.assertEqual(c2.message, 'leaf #12')
        self.assertEqual(c1.parents[0].oid, c2.parents[0].oid)
    
    def get_repo(self):
        return Repository(self.repo_path)

    def get_repo_filelist(self):
        return list(walk(path.join(self.repo_path, 'objects')))

    def tearDown(self):
        rmtree(self.repo_path)

def get_empty_tree_oid(repo):
    return repo.TreeBuilder().write()

if __name__ == '__main__':
    unittest.main()
