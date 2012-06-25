#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement
from contextlib import closing
from binascii import unhexlify
from tempfile import mkdtemp
from shutil import rmtree
from subprocess import Popen
from time import sleep
from signal import SIGTERM
import oursql
import unittest
import os
import redmine

OLD_COMMIT_ID = '446007dffb0fdc09c0ba9824c65e9fafb61d721b'
NEW_COMMIT_ID = 'e878650876323d9a564416f11194452c7f8085f9'
DB_NAME = 'registr_test_redmine'
CHANGELOG = {unhexlify(OLD_COMMIT_ID): unhexlify(NEW_COMMIT_ID)}
TEST_TABLES = [ # table, field, unicode
        ('journals', 'notes', True),
        ('time_entries', 'comments', True),
        ('wiki_content_versions', 'data', False),
        ]
ACCENTED_TEST = u'Árvíztűrő tükörfúrógép / Добро пожаловать в Википедию'
ENCODING = 'utf-8'

class TestRedmineMySQL(unittest.TestCase):
    CREATE_TABLE = ('CREATE TABLE ' + DB_NAME + '.{table} (id INT '
        'AUTO_INCREMENT PRIMARY KEY, {field} {datatype})')
    SQLA_URL_FMT = 'mysql+oursql://root:@localhost/{db}?unix_socket={socket}'
    def setUp(self):
        self.mysql_path = mkdtemp('registr_test_redmine')
        self.mysql_datadir = os.path.join(self.mysql_path, 'data')
        os.mkdir(self.mysql_datadir)
        self.mysql_socket = os.path.join(self.mysql_path, 'socket')
        self.mysql_pidfile = os.path.join(self.mysql_path, 'pid')
        fnull = open(os.devnull, 'w')
        self.mysqld = Popen(['mysqld_safe', '--socket=' + self.mysql_socket,
            '--datadir=' + self.mysql_datadir, '--skip-networking',
            '--skip_grant_tables', '--pid-file=' + self.mysql_pidfile],
            stdout=fnull, stderr=fnull)
        self.sqlalchemy_url = self.SQLA_URL_FMT.format(
                db=DB_NAME, socket=self.mysql_socket)
        for _ in xrange(12):
            try:
                with closing(self.get_mysql_connection()) as conn:
                    with conn as cursor:
                        cursor.execute('CREATE DATABASE ' + DB_NAME)
                        for table, field, textual in TEST_TABLES:
                            cursor.execute(self.CREATE_TABLE.format(table=table,
                                field=field, datatype=('TEXT COLLATE utf8_general_ci'
                                    if textual else 'LONGBLOB')))
                break
            except oursql.InterfaceError:
                sleep(1)

    def get_mysql_connection(self):
        try:
            return oursql.connect(unix_socket=self.mysql_socket, db=DB_NAME)
        except oursql.ProgrammingError:
            return oursql.connect(unix_socket=self.mysql_socket)

    def test_db_connection(self):
        redmine.test_db_connection(self.sqlalchemy_url)

    def test_empty_run(self):
        self.do_mapping()

    def test_without_hashes(self):
        row = (1337, ACCENTED_TEST)
        self.do_insert_map_expect(row, row)

    def test_with_irrelevant_hashes(self):
        row = (1337, ACCENTED_TEST + u' commit:1234567 1234567890abcdef')
        self.do_insert_map_expect(row, row)

    PREFIXED_MSG_FMT = u'{fill} commit:{commit} {fill}'
    def test_short_hashes(self):
        to_insert = (42, self.PREFIXED_MSG_FMT.format(fill=ACCENTED_TEST,
            commit=OLD_COMMIT_ID[:7]))
        to_expect = (42, self.PREFIXED_MSG_FMT.format(fill=ACCENTED_TEST,
            commit=NEW_COMMIT_ID[:7]))
        self.do_insert_map_expect(to_insert, to_expect)

    def test_long_hashes(self):
        to_insert = (69, self.PREFIXED_MSG_FMT.format(fill=ACCENTED_TEST,
            commit=OLD_COMMIT_ID))
        to_expect = (69, self.PREFIXED_MSG_FMT.format(fill=ACCENTED_TEST,
            commit=NEW_COMMIT_ID))
        self.do_insert_map_expect(to_insert, to_expect)

    UNPREFIXED_MSG_FMT = u'{fill} {commit} {fill}'
    def test_unprefixed_long_hashes(self):
        to_insert = (42, self.UNPREFIXED_MSG_FMT.format(fill=ACCENTED_TEST,
            commit=OLD_COMMIT_ID))
        to_expect = (42, self.PREFIXED_MSG_FMT.format(fill=ACCENTED_TEST,
            commit=NEW_COMMIT_ID))
        self.do_insert_map_expect(to_insert, to_expect)

    def do_insert_map_expect(self, to_insert, to_expect):
        self.insert_row(to_insert)
        self.do_mapping()
        self.expect_row(to_expect)

    def insert_row(self, row):
        with closing(self.get_mysql_connection()) as conn:
            with conn as cursor:
                for table, _field, textual in TEST_TABLES:
                    if not textual:
                        row = [buffer(col.encode(ENCODING))
                                if isinstance(col, unicode)
                                else col for col in row]
                    sql = 'INSERT INTO {table} VALUES (?, ?)'.format(table=table)
                    cursor.execute(sql, row)

    def do_mapping(self):
        redmine.map_changelog(self.sqlalchemy_url, CHANGELOG)

    def expect_row(self, row):
        with closing(self.get_mysql_connection()) as conn:
            with conn as cursor:
                for table, _field, textual in TEST_TABLES:
                    cursor.execute('SELECT * FROM ' + table)
                    (db_row,) = cursor.fetchall()
                    if not textual:
                        db_row = [col.decode(ENCODING)
                                if isinstance(col, str)
                                else col for col in db_row]
                    self.assertEquals(list(row), list(db_row))

    def tearDown(self):
        with file(self.mysql_pidfile) as pidfile:
            pid = int(pidfile.read().strip())
        os.kill(pid, SIGTERM)
        self.mysqld.wait()
        rmtree(self.mysql_path)

if __name__ == '__main__':
    unittest.main()
