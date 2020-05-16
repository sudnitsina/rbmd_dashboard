"""Execute tests using httpserver fixture
run: PYTEST_HTTPSERVER_PORT=9076 py.test -s test/selenium_tests.py
httpserver will be run at localhost:9076
"""
import json
import logging
from collections import namedtuple

import pytest
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait

from test import test_data
from test.page import LoginPage

logging.basicConfig(level=logging.INFO)


RESPONSES = [
    {"state": "OK", "message": "OK"},
    {"state": "FAIL", "message": "Not found"},
]

STATUS = namedtuple("Status", "alive resizing deadly")("alive", "resizing", "deadly.")


def login(driver):
    return LoginPage(driver).login("user1", "password")


def set_status_alive(zk):
    test_data.STATUS_JSON["health"] = STATUS.alive
    zk.set("/rbmd/log/quorum", json.dumps(test_data.STATUS_JSON).encode("utf-8"))


@pytest.fixture
def dashboard(driver):
    return login(driver)


def is_text_presented(text, driver):
    """Return True if element with specified test can be found, False otherwise."""
    try:
        driver.find_element_by_xpath("//*[contains(text(), '{}')]".format(text))
        return True
    except NoSuchElementException:
        return False


@pytest.fixture(params=[test_data.STATUS_JSON])
def prepare_zk_data(request, zk):
    data = (
        request.param
        if isinstance(request.param, bytes)
        else json.dumps(request.param).encode("utf-8")
    )
    zk.create("/rbmd/log/quorum", data, ephemeral=True, makepath=True)


def test_login(driver, httpserver, prepare_zk_data):
    """Login -> main page"""

    dashboard = login(driver)

    httpserver.expect_request("/v1/metrics").respond_with_json(
        json.dumps(test_data.METRICS)
    )

    dashboard.open_node("node.example.com")

    assert is_text_presented("Mountpoint: 123", driver)


@pytest.mark.parametrize("res", RESPONSES)
def test_unmount(res, httpserver, prepare_zk_data, dashboard):
    """Test that ok/fail responses on unmount request are correctly displayed."""
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


@pytest.fixture
def prepare_http_server(httpserver):
    """Set http server to get response from v1/status and /v1/resolve endpoints."""
    httpserver.expect_request("/v1/status").respond_with_json(test_data.STATUS_API)

    httpserver.expect_request(
        "/v1/resolve", data='{"node": "node.example.com"}', method="POST"
    ).respond_with_json(test_data.STATUS_API)


@pytest.mark.parametrize("prepare_zk_data", [test_data.STATUS], indirect=True)
def test_resolve_deadly(prepare_http_server, prepare_zk_data, zk, dashboard):
    """Test that status can be changed from deadly to alive by clicking resolve."""

    assert dashboard.get_status() == STATUS.deadly

    dashboard.show_details()
    dashboard.resolve()

    set_status_alive(zk)

    assert dashboard.get_status() == STATUS.alive

    dashboard.open_node("node.example.com")

    # TODO: add check


@pytest.mark.parametrize(
    "prepare_zk_data", [dict(test_data.STATUS_JSON, health="resizing.")], indirect=True
)
def test_resizing_to_alive(zk, prepare_zk_data, dashboard):
    """Test that displayed status is changed from resizing to alive."""
    assert dashboard.get_status() == "resizing."

    set_status_alive(zk)

    assert dashboard.get_status() == STATUS.alive
