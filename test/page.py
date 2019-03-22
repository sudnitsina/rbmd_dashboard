"""Page class."""


class BasePage:
    def __init__(self, driver):
        self.driver = driver

    def go(self, url=None):
        self.driver.get(url) if url else self.driver.get(self.url)

    def accept_alert(self):
        self.driver.switch_to.alert.accept()


class LoginPage(BasePage):
    def login(self, name, password):
        self.driver.find_element_by_name("username").send_keys(name)
        self.driver.find_element_by_name("password").send_keys(password)
        self.driver.find_element_by_xpath("/html/body/form/input[4]").click()
        return Dashboard(self.driver)


class Dashboard(BasePage):
    """Page class contains elements and methods."""

    def is_metric_exist(self, metric):
        """Is specified metric available at the page.

        :param metric:
        :return: True if metric exists, False otherwise
        """

    def get_metrics(self, metric):
        """Get value of specified metric."""

    def get_nodes_list(self):
        """Get all nodes names."""

    def open_node(self, node_name):
        """Click node link to open node details."""
        self.driver.find_element_by_link_text(node_name).click()

    def unmount(self):
        self.driver.find_element_by_link_text("unmount").click()

    def get_status(self):
        return (
            self.driver.find_element_by_id("status").find_element_by_tag_name("p").text
        )

    # RESPONSE CONTAINER

    def get_result(self):
        return self.driver.find_element_by_id("rsp").find_element_by_tag_name("h3").text

    def get_message(self):
        return self.driver.find_element_by_id("rsp").find_element_by_tag_name("p").text

    # Deadly message

    def show_details(self):
        return self.driver.find_element_by_link_text("Show details").click()

    def resolve(self):
        return self.driver.find_element_by_link_text("Resolve").click()
