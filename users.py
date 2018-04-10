#!/usr/bin/env python

import argparse
import bcrypt
import random
import sqlite3


def parse_command_line():
    """Parse command line arguments.
    Add new user:
      ./users.py -u <USERNAME> [-p <PASSWORD>]
    Delete user:
      ./users.py -u <USERNAME> --delete
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user",
                        help="User name")
    parser.add_argument("-p", "--password",
                        help="User password. If it none password will be generated")
    parser.add_argument("-b", "--database", default="./auth.db", help="Path to users database")
    parser.add_argument("--delete", action='store_true', help="Delete user")
    return parser.parse_args()


class User:

    def __init__(self, args):
        self.args = args
        self.user = args.user
        self.password = args.password
        self.connection = self._init_connection()

    def _init_connection(self):
        con = sqlite3.connect(self.args.database)
        cur = con.cursor()
        return {"cursor": cur, "connect": con}

    def _close_connection(self):
        self.connection["cursor"].close()
        self.connection["connect"].close()

    def _commit(self):
        self.connection["connect"].commit()
        
    def add(self):
        if self.password is None:
            self.password = self._passgen()
            print "Password has been generated: ", self.password 
        hashed_password = bcrypt.hashpw(self.password.encode('utf-8'), bcrypt.gensalt())
        try: 
            self.connection["cursor"].execute(
                "INSERT INTO users (name, password) VALUES (?, ?)",
                (self.user, hashed_password)
            )
            self._commit()
        except sqlite3.IntegrityError: 
            print 'user already exists'
        self._close_connection()

    def delete(self):
        self.connection["cursor"].execute(
            "DELETE FROM users WHERE name=?",
            (self.user,)
        )
        self._commit()
        self._close_connection()

    def _passgen(self):
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        return ''.join(random.choice(chars) for i in range(10))


if __name__ == "__main__":
    args = parse_command_line()
    user = User(args)
    if not args.delete:
        user.add()
    else:
        user.delete()
