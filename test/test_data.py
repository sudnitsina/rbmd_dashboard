# test data to be stored in zookeeper

# /rbmd/log/quorum"
# deadly status
STATUS = b"""
{
  "quorum": [{
      "node": "node.example.com",
      "ip": {
        "v4": [
          "10.0.3.1"
        ],
        "v6": [
          "fe80::f869:d0ff:fea3:3c0a"
        ]
      },
      "updated": 1483428452,
      "mounts": [
          {
            "mountpoint": "123",
            "mountopts": "",
            "fstype": "ext123",
            "pool": "",
            "image": "",
            "block": ""
          }
        ]
    }
  ],
  "health": "deadly.",
  "deadlyreason": {
      "node": "",
      "ip": {
        "v4": null,
        "v6": null
      },
      "updated": 0,
      "mounts": null
    },

  "leader": "node.example.com"
}"""

STATUS_JSON = {
    "quorum": [
        {
            "node": "node.example.com",
            "ip": {"v4": ["10.0.3.1"], "v6": ["fe80::f869:d0ff:fea3:3c0a"]},
            "updated": 1483428452,
            "mounts": [
                {
                    "mountpoint": "123",
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
    "leader": "node.example.com",
}


# test data to be returned from api
# v1/metrics
METRICS = {"goroutines": 9, "nodes": 2, "mountstotal": 0, "cgocall": 1}

STATUS_API = {
    "quorum": {
        "node.example.com": {
            "node": "node.example.com",
            "ip": {"v4": ["10.0.3.1"], "v6": ["fe80::f869:d0ff:fea3:3c0a"]},
            "updated": 1483428452,
            "mounts": None,
        }
    },
    "health": "deadly.",
    "deadlyreason": {
        "node": "node.example.com",
        "ip": {"v4": None, "v6": None},
        "updated": 0,
        "mounts": None,
    },
    "leader": "node.example.com",
}
