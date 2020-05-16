import logging

import pytest
from kazoo.client import KazooClient

ZK_HOST = "172.17.0.2:2181"


@pytest.fixture
def zk():
    """Configure data in zookeeper."""
    zk = KazooClient(hosts=ZK_HOST)
    try:
        zk.start()
    except Exception:
        logging.error("Error connecting zk", exc_info=True)

    yield zk
    zk.stop()


@pytest.fixture
def driver(selenium):
    selenium.get("http://127.0.0.1:8000/")
    yield selenium
