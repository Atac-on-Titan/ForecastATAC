"""Unit tests for trend filtering."""
import os

import pytest

from trend_filtering import FilterManager, Filter


@pytest.fixture
def cleanup_file_before_test():
    # This fixture will be executed before each test.
    file_path = "resources/test_filter_saved.json"  # Replace with the actual file path.
    if os.path.exists(file_path):
        os.remove(file_path)
    yield
    # Optional: You can add additional cleanup steps here if needed.


@pytest.fixture
def cleanup_file_after_test():
    # This fixture will be executed after each test.
    yield
    file_path = "resources/test_filter_saved.json"  # Replace with the actual file path.
    if os.path.exists(file_path):
        os.remove(file_path)


def test_filter_manager_save(cleanup_file_before_test, cleanup_file_after_test):
    in_json_path = "resources/test_filter.json"
    out_json_path = "resources/test_filter_saved.json"
    filter_manager_in = FilterManager(in_json_path)

    filter_manager_in.save(out_json_path)
    assert os.path.exists(out_json_path)

    filter_manager_out = FilterManager(out_json_path)

    assert filter_manager_in.get_filters() == filter_manager_out.get_filters()


def test_filter_manager_mark_completed():
    day_filter = Filter("day", 0, False)
    filter_manager = FilterManager([day_filter])

    filter_manager.set_filter_completed(day_filter.name, day_filter.value)

    assert filter_manager.get_filters()[0].completed
