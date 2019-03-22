import json
import os
from subprocess import call
from unittest import TestCase

from mock import patch
from tornado.options import define
from tornado.testing import AsyncHTTPTestCase

import rbmd
from rbmd import action


def prepare_db():
    name = "test_auth.db"
    with open("schema.sql", "r") as sql:
        call(["sqlite3", "test_auth.db"], stdin=sql)
    call(["python", "users.py", "-u", "tester", "-p", "tester", "-d", name])
    define("sqlite_db", default=os.path.join(os.path.dirname(__file__), name), help="User DB")


def destroy_db():
    name = "test_auth.db"
    call(["rm", name])


class AuthTest(AsyncHTTPTestCase):
    @classmethod
    def setUpClass(cls):
        prepare_db()

    @classmethod
    def tearDownClass(cls):
        destroy_db()

    def get_app(self):
        self.app = rbmd.Application()
        return self.app

    def test_login_redirect(self):
        response = self.fetch('/', method='GET')
        self.assertEqual(response.effective_url, self.get_url('/login?next=/'))
        self.assertEqual(response.code, 200)

    def test_index_page(self):
        response = self.fetch('/', method='GET')
        secure = response.headers["Set-Cookie"]
        print(response)
        headers = {"Cookie": secure}
        response = self.fetch('/login', raise_error=True, method='POST',
                              body="username=tester&password=tester&%s" % secure,
                              headers=headers, follow_redirects=False)
        self.assertEqual(response.code, 302)
        user_cookie = response.headers['Set-Cookie']

        response = self.fetch('/', method='GET', headers={"Cookie": user_cookie})
        self.assertEqual(response.code, 200)
        self.assertIn("Metrics", response.body)


class ActionTest(TestCase):
    @patch('requests.get')
    @patch('requests.post')
    def test_get(self, postMock, getMock):
        res = action('resolve', 'get', json.dumps({'a': 1}))
        assert postMock.called_with('http://127.0.0.1:9076/v1/resalve')
        assert getMock.called
        assert not postMock.called

    @patch('requests.get')
    @patch('requests.post')
    def test_post(self, postMock, getMock):
        res = action('resolve', 'post', json.dumps({'a': 1}))
        assert not getMock.called
        assert postMock.called

    def test_error(self):
        res = action('resolve', 'post', json.dumps({'a': 1}))
        assert res == "connection can't be established"

    def test_put(self):
        res = action('resolve', 'put', json.dumps({'a': 1}))
        assert res == "method not allowed"
