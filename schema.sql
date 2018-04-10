-- sqlite3 auth.db
-- sqlite3 auth.db < schema.sql

DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);
