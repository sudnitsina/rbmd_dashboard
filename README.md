[![Build Status](https://travis-ci.org/sudnitsina/rbmd_dashboard.svg?branch=feature%2Fdummy_zookeeper)](https://travis-ci.org/sudnitsina/rbmd_dashboard)
# rbmd web panel

Web dashboard for [RBMD](https://github.com/Difrex/rbmd)
provides interface to monitor cluster data and allows you to mount/umount/resolve.

## Requirements

* Python2.7
* Zookeeper
* [RBMD](https://github.com/Difrex/rbmd)

## Usage

Install dependencies:
```sh
pip install -r requrements.txt
```

Apply database schema
```sh
sqlite3 auth.db < schema.sql
```

Add users
```sh
./users.py -u username # Add -p 'password' optionaly
```

Change config
```json
{
    "zookeeper" : "127.0.0.1:2181", // Zookeeper
    "api": "http://127.0.0.1:9076/v1" // RBMD HTTP API endpoint
}
```

Run
```sh
./rbmd.py
```

Web server will be started at 0.0.0.0:8000.

To run app in docker container:

```sh
docker build -t rbmd PROJECT_DIRECTORY
docker run -ti --network="host" rbmd
```
