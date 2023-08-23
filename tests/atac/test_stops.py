from atac import load_stops, StopManager


def test_load_stops():
    stops = load_stops("tests/atac/data/stops.txt")

    assert len(stops) == 3


def test_stop_manager():
    stop_manager = StopManager("tests/atac/data/stops.txt")
    found_stop = stop_manager.find_stop("00213")

    assert found_stop
