#!/bin/sh

sqlite3 auth.db < schema.sql
python users.py -u user1 -p password
python rbmd.py