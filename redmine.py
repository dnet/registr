#!/usr/bin/env python

from sqlalchemy import create_engine, Table, Column, String, Integer, MetaData
from sqlalchemy.sql import column
from binascii import unhexlify, hexlify
import re

TABLES = [
        ('journals', 'notes'),
        ('time_entries', 'comments'),
        ('wiki_content_versions', 'data'),
        ]

COMMIT_ID_RE = r'(commit:)?[0-9a-f]{7,40}'
ID_COLUMN = 'id'
ENCODING = 'utf-8'

def test_db_connection(db_url):
    db_connect(db_url).close()

def map_changelog(db_url, changelog):
    with db_connect(db_url) as connection:
        metadata = MetaData()
        replacer = Replacer(changelog)
        for table_name, column_name in TABLES:
            table = Table(table_name, metadata,
                    Column(ID_COLUMN, Integer, primary_key=True),
                    Column(column_name, String(255)))
            commit_id_clause = column(column_name).match(COMMIT_ID_RE)
            result = connection.execute(table.select().where(commit_id_clause))
            to_replace = []
            for row_id, content in result:
                unicode_db = isinstance(content, unicode)
                content_str = (content.encode(ENCODING) if unicode_db
                        else content)
                replaced_str = re.sub(COMMIT_ID_RE, replacer.repl, content_str)
                if replaced_str != content_str:
                    replaced_db = (replaced_str.decode(ENCODING) if unicode_db
                            else replaced_str)
                    to_replace.append((row_id, replaced_db))
            result.close()
            id_col = column(ID_COLUMN)
            for row_id, content in to_replace:
                update_where = table.update().where(id_col == row_id)
                connection.execute(update_where.values({column_name: content}))

def db_connect(db_url):
    return create_engine(db_url).connect()

class Replacer(object):
    def __init__(self, changelog):
        self.changelog = changelog

    def repl(self, match):
        commit_id = match.group(0)
        sha = commit_id[7:] if commit_id.startswith('commit:') else commit_id
        oid = unhexlify(sha if len(sha) % 2 == 0 else sha[:-1])
        if oid in self.changelog:
            return 'commit:' + hexlify(self.changelog[oid])
        else:
            for old, new in self.changelog.iteritems():
                if old.startswith(oid):
                    return 'commit:' + hexlify(new)[:7]
        return commit_id
