from atac import load_stops, stop_manager


def test_load_stops():
    stops = load_stops("data/stops.txt")

    assert len(stops) == 3


def test_stop_manager():
    found_stop = stop_manager.find_stop("00123")

    assert found_stop
