"""Execute tests using httpserver fixture
run: PYTEST_HTTPSERVER_PORT=9076 py.test -s test/selenium_tests.py
httpserver will be run at localhost:9076
"""
import json
import logging

import pytest
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait

from test import test_data
from test.page import LoginPage

logging.basicConfig(level=logging.INFO)


def login(driver):
    return LoginPage(driver).login("user1", "password")


def set_status_alive(zk):
    test_data.ALIVE_DATA["health"] = test_data.STATUS.alive
    zk.set("/rbmd/log/quorum", json.dumps(test_data.ALIVE_DATA).encode("utf-8"))


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


@pytest.fixture(params=[test_data.ALIVE_DATA])
def prepare_zk_data(request, zk):
    data = json.dumps(request.param).encode("utf-8")
    zk.create("/rbmd/log/quorum", data, ephemeral=True, makepath=True)


def test_login(driver, httpserver, prepare_zk_data):
    """Login -> main page"""

    dashboard = login(driver)

    httpserver.expect_request(test_data.Endpoints.METRICS).respond_with_json(
        json.dumps(test_data.METRICS)
    )

    dashboard.open_node(test_data.NODE)

    assert is_text_presented("Mountpoint: {}".format(test_data.MOUNTPOINT), driver)


@pytest.mark.parametrize("response", test_data.RESPONSES)
def test_unmount(response, httpserver, prepare_zk_data, dashboard):
    """Test that ok/fail responses on unmount request are correctly displayed."""
    httpserver.expect_request(test_data.Endpoints.METRICS).respond_with_json(
        test_data.METRICS
    )
    httpserver.expect_request(
        test_data.Endpoints.UMOUNT,
        data=json.dumps(test_data.UMOUNT_DATA),
        method="POST",
    ).respond_with_json(response)

    dashboard.open_node(test_data.NODE)
    dashboard.unmount()

    dashboard.accept_alert()

    assert WebDriverWait(dashboard.driver, 10).until(
        lambda x: x.find_element_by_id("rsp").is_displayed()
    )

    assert dashboard.get_result() == response["state"]
    assert dashboard.get_message() == response["message"]


@pytest.fixture
def prepare_http_server(httpserver):
    """Set http server to get response from v1/status and /v1/resolve endpoints."""
    httpserver.expect_request(test_data.Endpoints.STATUS).respond_with_json(
        test_data.DEADLY_RESPONSE
    )

    httpserver.expect_request(
        test_data.Endpoints.RESOLVE,
        data=json.dumps({"node": test_data.NODE}),
        method="POST",
    ).respond_with_json(test_data.DEADLY_RESPONSE)


@pytest.mark.parametrize(
    "prepare_zk_data",
    [dict(test_data.ALIVE_DATA, health=test_data.STATUS.deadly)],
    indirect=True,
)
def test_resolve_deadly(prepare_http_server, prepare_zk_data, zk, dashboard):
    """Test that status can be changed from deadly to alive by clicking resolve."""

    assert dashboard.get_status() == test_data.STATUS.deadly

    dashboard.show_details()
    dashboard.resolve()

    set_status_alive(zk)

    assert dashboard.get_status() == test_data.STATUS.alive

    dashboard.open_node(test_data.NODE)

    # TODO: add check


@pytest.mark.parametrize(
    "prepare_zk_data",
    [dict(test_data.ALIVE_DATA, health=test_data.STATUS.resizing)],
    indirect=True,
)
def test_resizing_to_alive(zk, prepare_zk_data, dashboard):
    """Test that displayed status is changed from resizing to alive."""
    assert dashboard.get_status() == test_data.STATUS.resizing

    set_status_alive(zk)

    assert dashboard.get_status() == test_data.STATUS.alive
