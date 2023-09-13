"""Module for preprocessing functions."""
from typing import Union

import networkx as nx
import pandas as pd


def build_route_stops(trips: Union[str, pd.DataFrame], stop_times: Union[str, pd.DataFrame],
                      stops: Union[str, pd.DataFrame],
                      routes: Union[str, pd.DataFrame]):
    """Builds a single pandas DataFrame from trip, stop_times, and routes.

    Each row in the final dataframe will be a stop along a route.

    :arg
        trips (Union[str, pd.DataFrame]): a string pointing to a csv file with trips or a pandas dataframe with trips.
        stop_times (Union[str, pd.DataFrame]): a string pointing to a csv file with stop_times or a pandas dataframe with
        stop_times.
        stops (Union[str, pd.DataFrame]): either a string pointing to a csv file with stops or a pandas dataframe with
        stops.
        routes (Union[str, pd.DataFrame]): a string pointing to a csv file with routes or a pandas dataframe with routes.

    :return
        (pd.DataFrame) a single pandas dataframe.
    """
    if isinstance(trips, str):
        trips = pd.read_csv(trips, low_memory=False)

    if isinstance(stop_times, str):
        stop_times = pd.read_csv(stop_times, low_memory=False)

    if isinstance(stops, str):
        stops = pd.read_csv(stops, low_memory=False)

    if isinstance(routes, str):
        routes = pd.read_csv(routes, low_memory=False)

    complete = trips.merge(stop_times, how='inner', on='trip_id')
    # We drop everything that it is not needed for this stage. We keep `shape_id` since we want to use shapes later on.
    complete = complete[['route_id', 'trip_id', 'stop_id', 'stop_sequence', 'direction_id', 'shape_id']]

    # The next inner join is to add route specific information (not trip specific). A route is what we call a bus
    # line. This way we can filter out everything which is not handled by ATAC and subway/tram lines.
    complete = complete.merge(routes, on='route_id', how='inner')
    complete = complete[(complete['agency_id'] == 'OP1') & (complete['route_type'] == 3)]

    # With the next inner join we are recovering stop related information, like name, latitude and longitude.
    complete = complete.merge(stops, how='inner', on='stop_id')

    # Here we do not need `trip id`, we remove the column and drop the duplicates w.r.t. route, stop sequence and
    # direction. At this stage, we only want to build (and plot) an undirected graph of ATAC public transport relying
    # on buses.
    complete = (
        complete.drop('trip_id', axis=1).drop_duplicates(['route_id', 'stop_sequence', 'direction_id']).reset_index())

    return complete


def build_stop_graph(stops: Union[str, pd.DataFrame], route_stops: pd.DataFrame):
    """Builds a networkx graph of the ATAC stops.

    Vertices in the graph are the stops, edges are the routes traveled by a bus between two stops.

    :arg
        stops (Union[str, pd.DataFrame]): either a string pointing to a csv file with stops or a pandas dataframe with
        stops.

    :return
        (nx.Graph) a networkx graph.
    """
    if isinstance(stops, str):
        stops = pd.read_csv(stops, low_memory=False)

    init_graph = nx.Graph()
    for _, row in stops.iterrows():
        init_graph.add_node(row['stop_id'], name=row['stop_name'], latitude=row['stop_lat'], longitude=row['stop_lon'])

    routes_grouped = route_stops.sort_values(by='stop_sequence').groupby(['route_id', 'direction_id'])
    for _, group in routes_grouped:
        stops = group['stop_id'].tolist()
        edges = [(stops[i], stops[i + 1]) for i in range(len(stops) - 1) if
                 not init_graph.has_edge(stops[i], stops[i + 1])]
        init_graph.add_edges_from(edges)

    init_graph.remove_nodes_from(list(nx.isolates(init_graph)))  # if present, we remove isolated nodes

    return init_graph


def get_start_end_hours(start_hour: int, interval: int = 60):
    """Creates a time interval from a start hour.

    :arg
        start_hour (int): the hour to be converted to a string, must be in interval [0, 23].
        interval (int): the minute interval to be added to the start_hour, must be in interval [0, inf).

    :return
        (str, str) a tuple of strings in the format HH:MM.
    """
    if start_hour < 0 or start_hour > 23:
        raise ValueError(f"Incorrect hour. Hour must be in interval [0, 23], but received hour: {start_hour}.")

    start_minutes = start_hour * 60
    end_minutes = start_minutes + interval

    end_hour = end_minutes // 60
    end_hour = end_hour if end_hour < 24 else 0
    end_minutes = end_minutes % 60

    return f"{start_hour:02}:00", f"{end_hour:02}:{end_minutes:02}"
