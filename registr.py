#!/usr/bin/env python

from __future__ import print_function
from shifter import shift
from redmine import test_db_connection, map_changelog

def main(args):
    try:
        amount, repo_path = args[1:3]
        amount = int(amount)
    except ValueError:
        raise InvalidUsageError(args[0])
    try:
        db_url = args[3]
        test_db_connection(db_url)
    except IndexError:
        db_url = None
    changelog, reference = shift(int(amount), repo_path)
    print('HEAD is shifted as', reference)
    if db_url is not None:
        map_changelog(db_url, changelog)

class InvalidUsageError(ValueError):
    def __init__(self, exename):
        ValueError.__init__(self)
        self.exename = exename

    USAGE_ERROR_FMT = 'Usage: {exe} <amount> <path to repo> [database URL]'
    def __str__(self):
        return self.USAGE_ERROR_FMT.format(exe=self.exename)

if __name__ == '__main__':
    import sys
    try:
        main(sys.argv)
    except InvalidUsageError as iue:
        print(str(iue), file=sys.stderr)
        sys.exit(1)
