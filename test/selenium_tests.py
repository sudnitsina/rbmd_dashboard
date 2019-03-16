"""Execute tests using httpserver fixture
run: PYTEST_HTTPSERVER_PORT=9076 py.test -s test/selenium_tests.py
httpserver will be run at localhost:9076
"""
import json
import logging
import time

import pytest
from kazoo.client import KazooClient
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

from test import test_data

logging.basicConfig(level=logging.INFO)

ZK_HOST = "172.17.0.2:2181"

RESPONSES = [
    {"state": "OK", "message": "OK"},
    {"state": "FAIL", "message": "Not found"},
]


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
    # login form
    driver.find_element_by_name("username").send_keys("user1")
    driver.find_element_by_name("password").send_keys("password")

    driver.find_element_by_xpath("/html/body/form/input[4]").click()


def is_text_presented(text, driver):
    try:
        driver.find_element_by_xpath(f"//*[contains(text(), '{text}')]")
        return True
    except NoSuchElementException:
        return False


# @pytest.mark.skip
def test_login(driver, httpserver, zk):
    """Login -> main page"""
    zk.create(
        "/rbmd/log/quorum",
        json.dumps(test_data.STATUS_JSON).encode("utf-8"),
        ephemeral=True,
        makepath=True,
    )
    login(driver)

    httpserver.expect_request("/v1/metrics").respond_with_json(
        json.dumps(test_data.METRICS)
    )

    driver.find_element_by_link_text("node.example.com").click()

    status_container = driver.find_element_by_xpath('//*[@id="statusContainer"]')

    assert is_text_presented("Mountpoint: 123", driver)

    assert not is_text_presented("Mountsds", driver)


@pytest.mark.parametrize("res", RESPONSES)
def test_unmount(res, driver, httpserver, zk):
    zk.create(
        "/rbmd/log/quorum",
        json.dumps(test_data.STATUS_JSON).encode("utf-8"),
        ephemeral=True,
        makepath=True,
    )

    login(driver)

    mydata = {"node": "node.example.com", "mountpoint": "123", "block": ""}

    httpserver.expect_request("/v1/metrics").respond_with_json(test_data.METRICS)
    httpserver.expect_request(
        "/v1/umount", data=json.dumps(mydata), method="POST"
    ).respond_with_json(res)

    driver.find_element_by_link_text("node.example.com").click()
    driver.find_element_by_link_text("unmount").click()

    driver.switch_to.alert.accept()

    assert WebDriverWait(driver, 10).until(
        lambda x: x.find_element_by_id("rsp").is_displayed()
    )

    assert (
        driver.find_element_by_id("rsp").find_element_by_tag_name("h3").text
        == res["state"]
    )
    assert (
        driver.find_element_by_id("rsp").find_element_by_tag_name("p").text
        == res["message"]
    )


def test_deadly(driver, httpserver, zk):
    httpserver.expect_request("/v1/status").respond_with_json(test_data.STATUS_API)

    httpserver.expect_request(
        "/v1/resolve", data='{"node": "node.example.com"}', method="POST"
    ).respond_with_json(test_data.STATUS_API)

    zk.create("/rbmd/log/quorum", test_data.STATUS, ephemeral=True, makepath=True)
    login(driver)

    assert (
        driver.find_element_by_id("status").find_element_by_tag_name("p").text
        == "deadly."
    )

    driver.find_element_by_link_text(
        "Show details"
    ).click()  # TODO: add details verification

    driver.find_element_by_link_text("Resolve").click()

    test_data.STATUS_JSON["health"] = "alive"

    zk.set("/rbmd/log/quorum", json.dumps(test_data.STATUS_JSON).encode("utf-8"))

    assert (
        driver.find_element_by_id("status").find_element_by_tag_name("p").text
        == "alive"
    )

    driver.find_element_by_link_text(
        "node.example.com"
    ).click()  # BUG: red frame should disappear after resolve
    time.sleep(2)  # and status is alive, but it doesn't


def test_resizing(driver, zk):
    test_data.STATUS_JSON["health"] = "resizing."
    zk.create(
        "/rbmd/log/quorum",
        json.dumps(test_data.STATUS_JSON).encode("utf-8"),
        ephemeral=True,
        makepath=True,
    )
    login(driver)

    assert (
        driver.find_element_by_id("status").find_element_by_tag_name("p").text
        == "resizing."
    )

    test_data.STATUS_JSON["health"] = "alive"
    zk.set("/rbmd/log/quorum", json.dumps(test_data.STATUS_JSON).encode("utf-8"))

    assert (
        driver.find_element_by_id("status").find_element_by_tag_name("p").text
        == "alive"
    )


"""https://stackoverflow.com/questions/53705219/how-to-separate-tests-and-fixtures"""
"""https://flowfx.de/blog/test-django-with-selenium-pytest-and-user-authentication/"""
