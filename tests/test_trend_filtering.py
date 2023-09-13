"""Unit tests for trend filtering."""
import os
import shutil

import pytest

from trend_filtering import FilterManager, Filter


@pytest.fixture
def cleanup_file_before_test():
    # This fixture will be executed before each test.
    file_path = "tmp/"  # Replace with the actual file path.
    if os.path.exists(file_path):
        shutil.rmtree(file_path)
    yield
    # Optional: You can add additional cleanup steps here if needed.


@pytest.fixture
def cleanup_file_after_test():
    # This fixture will be executed after each test.
    yield
    file_path = "tmp/"  # Replace with the actual file path.
    if os.path.exists(file_path):
        shutil.rmtree(file_path)


def test_filter_manager_save(cleanup_file_before_test, cleanup_file_after_test):
    in_json_path = "resources/test_filter.json"
    out_json_path = "tmp/test_filter_saved.json"
    filter_manager_in = FilterManager(in_json_path)

    filter_manager_in.save(out_json_path)
    assert os.path.exists(out_json_path)

    filter_manager_out = FilterManager(out_json_path)

    assert filter_manager_in.get_filters() == filter_manager_out.get_filters()


def test_filter_manager_mark_completed():
    day_filter = Filter("day", 0, [0.1], [False], False)
    filter_manager = FilterManager([day_filter])

    filter_manager.set_filter_completed(day_filter.name, day_filter.value, [0.1])

    assert filter_manager.get_filters()[0].completed
    assert filter_manager.get_uncompleted_filters() == [day_filter]


def test_mark_lambda_completed():
    day_filter = Filter("day", 0, [0.1], [False], False)

    assert not day_filter.is_completed()
    day_filter.set_lambda_completed(0.1)

    assert day_filter.is_completed()


def test_get_remaining_lambdas():
    day_filter = Filter("day", 0, [0.1, 0.2], [False, False], False)

    assert (day_filter.get_remaining_lambdas() == [0.1, 0.2]).all()
    day_filter.set_lambda_completed(0.1)

    assert (day_filter.get_remaining_lambdas() == [0.2]).all()
