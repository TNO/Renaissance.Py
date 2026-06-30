import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-slow-hypothesis",
        action="store_true",
        default=False,
        help="Run slow tests",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "hypothesisslow: mark test as a slow hypothesis test")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-slow-hypothesis"):
        skip = pytest.mark.skip(reason="Pass --run-slow-hypothesis to run slow hypothesis test")
        for item in items:
            if "hypothesisslow" in item.keywords:
                item.add_marker(skip)
