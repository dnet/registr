Redmine Git Issue Shifter
=========================

Purpose
-------

Importing projects into Redmine from software project management tools that track issues numbers by projects (in contrast with Redmine which uses a global counter for this) results in all issue numbers shifted with the amount of issues present in the Redmine system before the import. In case of the first import, this causes no problem, but all the other imports will require the importer to adjust the issue references in commit messages. This tool does two things: shifts all issue references and since commit hashes change because of how Git works, also adjusts commit references in Redmine objects.

Redmine tables and fields used
------------------------------

Note: on MySQL the storage engine needs to be set to MyISAM for shifting to work because of the need for FULLTEXT support.

 - `journals`.`notes`
 - `time_entries`.`comments`
 - `wiki_content_versions`.`data`

License
-------

The whole project is licensed under MIT license.

Dependencies
------------

 - Python 2.x (tested on 2.7)
 - pygit2 (https://github.com/libgit2/pygit2)
 - SQLAlchemy (Debian/Ubuntu package: `python-sqlalchemy`)
