#!/usr/bin/env python

import bcrypt
import json
from kazoo.client import KazooClient
from kazoo.recipe.watchers import DataWatch
import logging
import requests
import sqlite3
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import threading
import os.path
import os
import uuid

from tornado.options import define, options

define("port", default=8000, help="run on the given port", type=int)
define("sqlite_db", default=os.path.join(os.path.dirname(__file__), "auth.db"), help="User DB")

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
            websocket_ping_interval = 59,
            login_url="/login",
        )
        super(Application, self).__init__(handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    @tornado.web.authenticated
    def get(self):
        user_id = self.get_secure_cookie("user")
        try: metrics = json.loads(action('metrics', 'get'))
        except ValueError: metrics = {}
        dct = {'metrics': metrics}
        self.render("index.html", **dct)

    def get_current_user(self):
        return self.get_secure_cookie("user")


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
        hashed_password = bcrypt.hashpw(tornado.escape.utf8(self.get_argument("password")), tornado.escape.utf8(user[2]))
        if hashed_password == user[2]:
            self.set_secure_cookie("user", str(user[0]))
            self.redirect("/")
        else:
            self.render("login.html", error="incorrect password")

########### not used ##########################
#create new user /user?name=user_name&password=user_password
# class User(tornado.web.RequestHandler):
#     def get(self):
#         con = sqlite3.connect(options.sqlite_db)
#         cur = con.cursor()
#         data = self.request.arguments
#         hashed_password = bcrypt.hashpw(tornado.escape.utf8(self.get_argument("password")), bcrypt.gensalt())
#         cur.execute(
#             "INSERT INTO users (name, password) VALUES (?, ?)",
#              (self.get_argument("name"), hashed_password)
#         )
#         con.commit()
#         cur.close()
#         con.close()
#         self.write('done')


class MountHandler(tornado.web.RequestHandler):
    def post(self):
        if self.get_secure_cookie("user"):
            data = {k: v[0] for k, v in self.request.arguments.items()}
            res = action('mount', 'post', json.dumps(data))
            self.write(res)


class UnmountHandler(tornado.web.RequestHandler):
    def get(self):
        data = {k: v[0] for k, v in self.request.arguments.items()}
        res = action('umount', 'post', json.dumps(data))
        self.write(res)


class ResolveHandler(tornado.web.RequestHandler):
    def get(self):
        data = {k: v[0] for k, v in self.request.arguments.items()}
        res = action('resolve', 'post', json.dumps(data))
        self.write(res)


class StatusHandler(tornado.web.RequestHandler):
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
        SocketHandler.waiters.add(self)
        SocketHandler.send_updates(SocketHandler.quorum)

    def on_close(self):
        SocketHandler.waiters.remove(self)

    @classmethod
    def send_updates(cls, data, *stat):
        if data == '{}':
            my_data = json.loads(data)
            my_data["health"] = 'service is not available'
            my_data["quorum"] = [{"node":""}]
            data = json.dumps(my_data)
        if json.loads(data).get("health") == "deadly.":
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
    with open('conf.json') as conf:
        url = json.load(conf)["api"] + '/' + name
        if method == 'get':
            try:
                res = requests.get(url).content
            except:
                res = 'connection can\'t be established'
        elif method == 'post':
            try:
                res = requests.post(url, data, timeout=10).content
            except:
                res = 'connection can\'t be established'
    return res


def zk_handler():
    logging.basicConfig()
    zk = KazooClient(hosts=config("zookeeper"))
    try: zk.start()
    except: return
    t1 = threading.Thread(target=DataWatch, args=(zk, "/rbmd/log/quorum"), kwargs=dict(func=SocketHandler.send_updates))
    t1.setDaemon(True)
    t1.start()


########### not used ##########################
#def zk_fetch(path):
#    zk = KazooClient(hosts=config("zookeeper"))
#    zk.start()
#    data = zk.get(path)
#    zk.stop()


def main():
    tornado.options.parse_command_line()
    zk_handler()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
