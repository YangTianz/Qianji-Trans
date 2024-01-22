import pytest

from billing.main import load_rules_file


@pytest.fixture(scope="session")
def account_rules_list():
    account_rules = r"test/test_config/account_rules.json"
    return load_rules_file(account_rules)


@pytest.fixture(scope="session")
def classify_rules_list():
    cls_rules = r"test/test_config/category_rules.json"
    return load_rules_file(cls_rules)
