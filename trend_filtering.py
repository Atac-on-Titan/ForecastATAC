"""Module for trend filtering functions."""
import dataclasses
import json
import logging.config
from dataclasses import dataclass
from typing import Optional, Dict, Union, List

import cvxpy as cp
import networkx as nx
import numpy as np
import pandas as pd
import scipy

logger = logging.getLogger()


@dataclass
class Filter:
    name: str
    value: any
    completed: bool

    def file_name(self):
        return f"{self.name}_{self.value}"


class FilterManager:
    """Loads, saves, and updates Filter objects."""

    def __init__(self, filters: Union[str, List]):
        if isinstance(filters, List):
            self.filters = filters
        elif isinstance(filters, str):
            with open(filters, "r") as json_file:
                filters = json.load(json_file)
                self.filters = [Filter(item['name'], item['value'], item['completed']) for item in filters['filter']]

    def save(self, path: str):
        """Saves the filters to a given path."""
        filters = {"filter": [dataclasses.asdict(filter_) for filter_ in self.filters]}

        with open(path, "w") as json_file:
            json.dump(filters, json_file)

    def get_filters(self):
        """Returns the filters in this manager."""
        return self.filters

    def get_uncompleted_filters(self):
        """Returns filters that are not marked as completed."""
        return list(filter(lambda filter_: not filter_.completed, self.filters))

    def get_completed_filters(self):
        """Returns filters are that are marked as completed."""
        return list(filter(lambda filter_: filter_.completed, self.filters))

    def set_filter_completed(self, name: str, value: any):
        """Sets the filter identified by its name and value as completed."""
        for filter_ in self.filters:
            if filter_.name == name and filter_.value == value:
                filter_.completed = True


def vertex_signal(complete_df: pd.DataFrame, routes_graph: nx.Graph, *, weather: Optional[int] = None,
                  day: Optional[int] = None, time: Optional[tuple[int, int]] = None) -> nx.Graph:
    """
    Function assigning signal over the public transport graph vertexes by averaging across the inbound edges
    elapsed time, according to a specific filtering option, passed as keyword argument.
    :param complete_df: The dataframe containing the preprocessed data.
    :param routes_graph: The graph, already built.
    :param weather: Main weather conditions, either 0 or 1.
    :param day: The day of the week, as integer in the range [0, 6].
    :param time: The daytime, as an interval specified by a tuple of two integers.
    :return: The graph with the signal defined over the vertex set.
    """
    routes_graph = routes_graph.copy()

    if sum([(weather is None), (day is None), (time is None)]) != 2:
        raise TypeError(
            'This functions builds the graph according to only one filtering option, you have to pass one and only one.')
    if weather is not None:
        mask = (complete_df['weather_main_post'] == weather)
    elif day is not None:
        mask = (complete_df['day_of_week'] == day)
    else:
        mask = (complete_df['time_pre_datetime'].between_time(time[0], time[1]))

    complete_df = complete_df[mask]
    if not len(complete_df):
        raise (ValueError('The filtering option you passed is wrong since no observation has matching fields.'))

    pd.options.mode.chained_assignment = None
    complete_df['elapsed'] /= complete_df['stop_distance']
    pd.options.mode.chained_assignment = 'warn'

    complete_df = complete_df[['elapsed', 'stop_id_post']].groupby('stop_id_post').mean()
    nx.set_node_attributes(routes_graph, complete_df.to_dict('index'))

    delete_vx = [x[0] for x in routes_graph.nodes('elapsed') if x[1] is None]
    routes_graph.remove_nodes_from(delete_vx)
    routes_graph.remove_nodes_from(list(nx.isolates(routes_graph)))
    return routes_graph


def difference_op(graph: nx.Graph, order: int) -> scipy.sparse.csr_array:
    """
    Produces a linear difference operator for graph trend filtering according to Tibshirani R. et al. (2015).
    :param graph: The graph from which to build the difference linear operator.
    :param order: The order of the difference operator.
    :return: The difference operator as a SciPy sparse row matrix.
    """
    if order == 1:
        out = nx.incidence_matrix(graph, oriented=True)
    elif order == 2:
        out = nx.laplacian_matrix(graph)
    elif not order % 2:
        out = scipy.sparse.csr_matrix(nx.laplacian_matrix(graph)) ** (order / 2)
    else:
        out = (nx.incidence_matrix(graph, oriented=True) @
               scipy.sparse.csr_matrix(nx.laplacian_matrix(graph)) ** ((order - 1) / 2))

    return out


def trend_filter_validate(train: pd.DataFrame, val: pd.DataFrame, routes_graph: nx.Graph, lambda_seq: tuple[float, ...],
                          cond_filter: Filter) -> Dict[float, np.ndarray]:
    """Runs a validation using trend filtering on a given train-test split.

    :arg
        train (pd.DataFrame): the training data.
        val (pd.DataFrame): the validation data.
        routes_graph (nx.Graph): the networkx graph of bus routes.
        lambda_seq (tuple[float, ...]): the sequence of lambda values to try.
        cond_filter (Filter): the filter used to select validation data. An instance of the Filter dataclass.
    :return
        (dict) a dictionary with validation metrics.
    """
    cond_filter_dict = {cond_filter.name: cond_filter.value}

    logger.info("Building graph with signals.")
    # Building the unfiltered graph on training data
    train_graph = vertex_signal(train, routes_graph, **cond_filter_dict)

    logger.info("Building difference operator.")
    difference_operator = difference_op(train_graph, 2)
    time_vec = np.array([x[1] for x in train_graph.nodes(data='elapsed')])
    metric_dict = {}

    logger.info("Filtering validation set.")
    # Filtering the validation data
    if cond_filter.name == 'weather':
        mask = (val['weather_main_post'] == cond_filter.value)
    elif cond_filter.name == 'day':
        mask = (val['day_of_week'] == cond_filter.value)
    elif cond_filter.name == 'time':
        mask = (val['time_pre_datetime'].between_time(cond_filter.value[0], cond_filter.value[1]))
    else:
        raise ValueError('Illegal filtering option.')
    val = val[mask]

    for value_lambda in lambda_seq:
        logger.info(f"Validating for lambda: {value_lambda}")
        # Filtering on training data
        x = cp.Variable(shape=len(time_vec))
        loss = cp.Minimize((1 / 2) * cp.sum_squares(time_vec - x)
                           + value_lambda * cp.norm(difference_operator @ x, 1))
        problem = cp.Problem(loss)
        problem.solve(solver=cp.CVXOPT, verbose=False)
        congestion_df = pd.DataFrame(zip(train_graph.nodes, x.value), columns=['stop_id_post', 'congestion'])

        # Compute validation metric for specific lambda
        val_congestion = val.merge(congestion_df, on='stop_id_post')
        error = (val_congestion['congestion'] * val_congestion['stop_distance'] - val_congestion['elapsed']).to_numpy() **2
        metric_dict[value_lambda] = error.tolist()

    return metric_dict
