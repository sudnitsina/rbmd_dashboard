#!/usr/bin/env python

import json
import logging
import os
import os.path
import sqlite3
import threading

import bcrypt
import requests
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.websocket
from kazoo.client import KazooClient
from kazoo.recipe.watchers import DataWatch
from tornado.options import define, options


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/socket", SocketHandler),
            (r"/mount", MountHandler),
            (r"/unmount", UnmountHandler),
            (r"/resolve", ResolveHandler),
            (r"/status", StatusHandler),
            (r"/login", Auth),
        ]
        settings = dict(
            cookie_secret="=&r854^9nk7ys49@m7a5eu(g&jn8pytk6f%@quumabt*x5e*)i",
            template_path=os.path.join(os.path.dirname(__file__), "templates/rbmd"),
            static_path=os.path.join(os.path.dirname(__file__), "static/rbmd"),
            xsrf_cookies=True,
            websocket_ping_interval=59,
            login_url="/login?next=/",
        )
        super(Application, self).__init__(handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        try:
            metrics = json.loads(action('metrics', 'get'))
        except ValueError:
            metrics = {}
        dct = {'metrics': metrics}
        self.render("index.html", **dct)


class Auth(tornado.web.RequestHandler):
    def get(self):
        self.render("login.html", error=None)

    def post(self):
        con = sqlite3.connect(options.sqlite_db)
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE name = :name", {"name": self.get_argument("username")})
        user = cur.fetchone()
        cur.close()
        con.close()
        if not user:
            self.render("login.html", error="user not found")
            return

        hashed_password = bcrypt.hashpw(tornado.escape.utf8(self.get_argument("password")),
                                        tornado.escape.utf8(user[2]))
        if hashed_password == user[2]:
            self.set_secure_cookie("user", str(user[0]))
            self.redirect("/")
        else:
            self.render("login.html", error="incorrect password")


class MountHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        data = {k: v[0] for k, v in self.request.arguments.items()}
        res = action('mount', 'post', json.dumps(data))
        self.write(res)


class UnmountHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        data = {k: v[0] for k, v in self.request.arguments.items()}
        res = action('umount', 'post', json.dumps(data))
        self.write(res)


class ResolveHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        data = {k: v[0] for k, v in self.request.arguments.items()}
        res = action('resolve', 'post', json.dumps(data))
        self.write(res)


class StatusHandler(BaseHandler):
    pass


class SocketHandler(tornado.websocket.WebSocketHandler):
    waiters = set()
    quorum = json.dumps(dict())

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def check_origin(self, origin):
        return True

    def open(self):
        user_id = self.get_secure_cookie("user")
        if not user_id:
            return None
        SocketHandler.waiters.add(self)
        SocketHandler.send_updates(SocketHandler.quorum)

    def on_close(self):
        SocketHandler.waiters.remove(self)

    @classmethod
    def send_updates(cls, data, *stat):
        if not data:
            my_data = {"health": 'service is not available', "quorum": {"node": ""}}
            data = json.dumps(my_data)
        elif json.loads(data).get("health") == "deadly.":
            dead_data = action('status', 'get')
            my_data = json.loads(data)
            my_data["deadlyreason"] = json.loads(dead_data)["deadlyreason"]
            data = json.dumps(my_data)
        SocketHandler.quorum = data
        for waiter in cls.waiters:
            try:
                waiter.write_message(SocketHandler.quorum)
            except:
                logging.error("Error sending message", exc_info=True)

    def on_message(self, message): pass


def config(point):
    with open('conf.json') as conf:
        path = json.load(conf)[point]
    return path


def action(name, method, data=None):
    url = config("api") + '/' + name
    try:
        if method == 'get':
            res = requests.get(url).content
        elif method == 'post':
            res = requests.post(url, data, timeout=10).content
        else:
            res = 'method not allowed'
    except Exception as e:
        res = 'connection can\'t be established'
        logging.error(e)
    return res


def zk_handler():
    logging.basicConfig()
    zk = KazooClient(hosts=config("zookeeper"))
    try:
        zk.start()
    except Exception as e:
        logging.error("Error connecting zk", exc_info=True)
        return
    t1 = threading.Thread(target=DataWatch, args=(zk, "/rbmd/log/quorum"), kwargs=dict(func=SocketHandler.send_updates))
    t1.setDaemon(True)
    t1.start()


def main():
    define("port", default=8000, help="run on the given port", type=int)
    define("sqlite_db", default=os.path.join(os.path.dirname(__file__), "auth.db"), help="User DB")

    options.parse_command_line()
    zk_handler()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
