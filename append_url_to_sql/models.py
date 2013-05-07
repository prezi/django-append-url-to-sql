"""
:mod:`django-append-url-to-sql` --- Appends the request URL to SQL statements in Django
=======================================================================================

Whilst the `Django Debug Toolbar
<https://github.com/robhudson/django-debug-toolbar>`_ is invaluable for
development in a local environment, it cannot help you identify misbehaving
queries in production. To assist in this task, ``django-append-url-to-sql``
appends the request URL as a comment to every SQL statement that is executed.
For example::

  SELECT "auth_user"."id", [..] WHERE "auth_user"."id" = 1 -- /login

This makes it possible to go from ``SELECT * FROM pg_stat_activity`` or ``SHOW
PROCESSLIST`` output to the view that is executing it.

If the current request URL cannot be determined, nothing is appended.

Installation
------------

1. Add ``append_url_to_sql`` to your ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        ...
        'append_url_to_sql',
        ...
    )

Configuration
-------------

``APPEND_URL_TO_SQL_ENABLED``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Default: ``True``

Use this setting to disable this functionality without having to remove the
application. This can be used to only append the SQL code only in specific
environments.

Links
-----

View/download code
  https://github.com/playfire/django-append-url-to-sql

File a bug
  https://github.com/playfire/django-append-url-to-sql/issues
"""


import sys

from django.conf import settings
from django.http import HttpRequest
from django.db.backends import util, BaseDatabaseWrapper

class CursorWrapper(util.CursorDebugWrapper):
    def get_sql_query_tag_message(self, f_locals):
        message = f_locals.get('sql_query_tag')
        return repr(message) if message is not None else message

    def get_request(self, f_locals):
        request = f.f_locals.get('request')
        if isinstance(request, HttpRequest):
            return repr(request.path)[2:-1].replace('%', '%%')
        return None

    def execute(self, sql, *args):
        f = sys._getframe()
        while f:
            sql_comment = None
            f_locals = f.f_locals
            log_message = self.get_sql_query_tag(f_locals) or self.get_request(f_locals)
            if log_message is not None:
                sql += ' -- %s' % log_message
                break
            f = f.f_back
        return self.cursor.execute(sql, *args)

if getattr(settings, 'APPEND_URL_TO_SQL_ENABLED', True):
    old_cursor = BaseDatabaseWrapper.cursor
    def cursor(self, *args, **kwargs):
        return CursorWrapper(old_cursor(self, *args, **kwargs), self)
    BaseDatabaseWrapper.cursor = cursor
