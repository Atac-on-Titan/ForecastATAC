"""Unit tests for preprocessing."""

from preprocessing import get_start_end_hours


def test_get_start_end_hours_with_hour_interval():
    start = 1
    interval = 60
    expected_start = "01:00"
    expected_end = "02:00"

    actual_start, actual_end = get_start_end_hours(start, interval)

    assert actual_start == expected_start
    assert actual_end == expected_end


def test_get_start_end_hours_with_minute_interval():
    start = 6
    interval = 45
    expected_start = "06:00"
    expected_end = "06:45"

    actual_start, actual_end = get_start_end_hours(start, interval)

    assert actual_start == expected_start
    assert actual_end == expected_end


def test_get_start_end_hours_midnight():
    start = 23
    interval = 60
    expected_start = "23:00"
    expected_end = "00:00"

    actual_start, actual_end = get_start_end_hours(start, interval)

    assert actual_start == expected_start
    assert actual_end == expected_end
