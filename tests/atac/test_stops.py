from atac import load_stops


def test_load_stops():
    stops = load_stops("resources/stops.txt")

    assert len(stops) == 3
