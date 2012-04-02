#!/usr/bin/env python

from shifter import shift
from tempfile import mkdtemp
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
        repo = Repository(self.repo_path)
        tree = repo.TreeBuilder()
        empty_tree = tree.write()
        root = repo.create_commit(REF, SIG, SIG, 'root #1', empty_tree, [])
        repo.create_commit(REF, SIG, SIG, 'leaf #2', empty_tree, [root])
        del repo
        before = self.get_repo_filelist()
        shift(1, self.repo_path)
        after = self.get_repo_filelist()
        self.assertEqual(before, after)

    def test_unaffected_without_issues(self):
        repo = Repository(self.repo_path)
        tree = repo.TreeBuilder()
        empty_tree = tree.write()
        root = repo.create_commit(REF, SIG, SIG, 'root', empty_tree, [])
        repo.create_commit(REF, SIG, SIG, 'leaf', empty_tree, [root])
        del repo
        before = self.get_repo_filelist()
        shift(42, self.repo_path)
        after = self.get_repo_filelist()
        self.assertEqual(before, after)
    
    def get_repo_filelist(self):
        return list(walk(path.join(self.repo_path, 'objects')))

    def tearDown(self):
        rmtree(self.repo_path)

if __name__ == '__main__':
    unittest.main()
