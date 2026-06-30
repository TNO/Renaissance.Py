import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="Run slow tests",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run (usually a hypothesis test)")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--runslow"):
        skip = pytest.mark.skip(reason="Pass --runslow to run slow test")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip)
