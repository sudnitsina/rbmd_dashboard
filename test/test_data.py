from collections import namedtuple


class Endpoints:
    METRICS = "/v1/metrics"
    RESOLVE = "/v1/resolve"
    STATUS = "/v1/status"
    UMOUNT = "/v1/umount"


RESPONSES = [
    {"state": "OK", "message": "OK"},
    {"state": "FAIL", "message": "Not found"},
]

STATUS = namedtuple("Status", "alive resizing deadly")("alive", "resizing.", "deadly.")

NODE = "node.example.com"
MOUNTPOINT = "dfdfgffgd"

ALIVE_DATA = {
    "quorum": [
        {
            "node": NODE,
            "ip": {"v4": ["10.0.3.1"], "v6": ["fe80::f869:d0ff:fea3:3c0a"]},
            "updated": 1483428452,
            "mounts": [
                {
                    "mountpoint": MOUNTPOINT,
                    "mountopts": "",
                    "fstype": "ext123",
                    "pool": "",
                    "image": "",
                    "block": "",
                }
            ],
        }
    ],
    "health": "alive.",
    "deadlyreason": {
        "node": "",
        "ip": {"v4": None, "v6": None},
        "updated": 0,
        "mounts": None,
    },
    "leader": NODE,
}


# test data to be returned from api
# v1/metrics
METRICS = {"goroutines": 9, "nodes": 2, "mountstotal": 0, "cgocall": 1}

DEADLY_RESPONSE = {
    "quorum": {
        "node.example.com": {
            "node": NODE,
            "ip": {"v4": ["10.0.3.1"], "v6": ["fe80::f869:d0ff:fea3:3c0a"]},
            "updated": 1483428452,
            "mounts": None,
        }
    },
    "health": "deadly.",
    "deadlyreason": {
        "node": NODE,
        "ip": {"v4": None, "v6": None},
        "updated": 0,
        "mounts": None,
    },
    "leader": NODE,
}

UMOUNT_DATA = {"node": NODE, "mountpoint": MOUNTPOINT, "block": ""}
