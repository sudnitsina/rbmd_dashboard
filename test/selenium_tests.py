"""Execute tests using httpserver fixture
run: PYTEST_HTTPSERVER_PORT=9076 py.test -s test/selenium_tests.py
httpserver will be run at localhost:9076
"""
import json
import logging
from collections import namedtuple

import pytest
from kazoo.client import KazooClient
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from test import test_data
from test.page import LoginPage

logging.basicConfig(level=logging.INFO)

ZK_HOST = "172.17.0.2:2181"

RESPONSES = [
    {"state": "OK", "message": "OK"},
    {"state": "FAIL", "message": "Not found"},
]

STATUS = namedtuple("Status", "alive resizing deadly")("alive", "resizing", "deadly.")


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
def driver():
    driver = WebDriver()
    driver.get("http://127.0.0.1:8000/")
    yield driver
    driver.quit()


def login(driver):
    return LoginPage(driver).login("user1", "password")


def is_text_presented(text, driver):
    try:
        driver.find_element_by_xpath("//*[contains(text(), '{}')]".format(text))
        return True
    except NoSuchElementException:
        return False


def prepare_data(zk, data=None):
    data = data or json.dumps(test_data.STATUS_JSON).encode("utf-8")
    zk.create("/rbmd/log/quorum", data, ephemeral=True, makepath=True)


def test_login(driver, httpserver, zk):
    """Login -> main page"""
    prepare_data(zk)
    dashboard = login(driver)

    httpserver.expect_request("/v1/metrics").respond_with_json(
        json.dumps(test_data.METRICS)
    )

    dashboard.open_node("node.example.com")

    assert is_text_presented("Mountpoint: 123", driver)


@pytest.mark.parametrize("res", RESPONSES)
def test_unmount(res, driver, httpserver, zk):
    prepare_data(zk)

    dashboard = login(driver)

    mydata = {"node": "node.example.com", "mountpoint": "123", "block": ""}

    httpserver.expect_request("/v1/metrics").respond_with_json(test_data.METRICS)
    httpserver.expect_request(
        "/v1/umount", data=json.dumps(mydata), method="POST"
    ).respond_with_json(res)

    dashboard.open_node("node.example.com")
    dashboard.unmount()

    dashboard.accept_alert()

    assert WebDriverWait(dashboard.driver, 10).until(
        lambda x: x.find_element_by_id("rsp").is_displayed()
    )

    assert dashboard.get_result() == res["state"]
    assert dashboard.get_message() == res["message"]


def test_deadly(driver, httpserver, zk):
    httpserver.expect_request("/v1/status").respond_with_json(test_data.STATUS_API)

    httpserver.expect_request(
        "/v1/resolve", data='{"node": "node.example.com"}', method="POST"
    ).respond_with_json(test_data.STATUS_API)

    prepare_data(zk, data=test_data.STATUS)
    dashboard = login(driver)

    assert dashboard.get_status() == STATUS.deadly

    dashboard.show_details()
    dashboard.resolve()

    test_data.STATUS_JSON["health"] = STATUS.alive

    zk.set("/rbmd/log/quorum", json.dumps(test_data.STATUS_JSON).encode("utf-8"))

    assert dashboard.get_status() == STATUS.alive

    dashboard.open_node("node.example.com")


def test_resizing(driver, zk):
    test_data.STATUS_JSON["health"] = "resizing."
    prepare_data(zk)
    d = login(driver)

    assert d.get_status() == "resizing."

    test_data.STATUS_JSON["health"] = STATUS.alive
    zk.set("/rbmd/log/quorum", json.dumps(test_data.STATUS_JSON).encode("utf-8"))

    assert d.get_status() == STATUS.alive
