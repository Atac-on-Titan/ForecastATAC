"""Module for trend filtering functions."""
from typing import Optional, Dict

import networkx as nx
import numpy as np
import pandas as pd
import scipy
import cvxpy as cp


def vertex_signal(complete_df: pd.DataFrame, routes_graph: nx.Graph, *, wtr: Optional[str] = None,
                  dow: Optional[int] = None, daytime: Optional[tuple[int, int]] = None) -> nx.Graph:
    """
    Function assigning signal over the public transport graph vertexes by averaging across the inbound edges
    elapsed time, according to a specific filtering option, passed as keyword argument.
    :param complete_df: The dataframe containing the preprocessed data.
    :param routes_graph: The graph, already built.
    :param wtr: Main weather conditions.
    :param dow: The day of the week, as integer.
    :param daytime: The daytime, as an interval specified by a tuple of two integers.
    :return: The graph with the signal defined over the vertex set.
    """
    routes_graph = routes_graph.copy()

    if sum([(wtr is None), (dow is None), (daytime is None)]) != 2:
        raise TypeError(
            'This functions builds the graph according to only one filtering option, you have to pass one and only one.')
    if wtr is not None:
        mask = (complete_df['weather_main_post'] == wtr.capitalize())
    elif dow is not None:
        mask = (complete_df['day_of_week'] == dow)
    else:
        mask = (complete_df['time_pre_datetime'].between_time(daytime[0], daytime[1]))

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
                          cond_filter: tuple) -> Dict[float, np.ndarray]:
    """Runs a validation using trend filtering on a given train-test split.

    :arg
        train (pd.DataFrame): the training data.
        val (pd.DataFrame): the validation data.
        routes_graph (nx.Graph): the networkx graph of bus routes.
        lambda_seq (tuple[float, ...]): the sequence of lambda values to try.
    """
    cond_filter = {cond_filter[0]: cond_filter[1]}

    # Building the unfiltered graph on training data
    train_graph = vertex_signal(train, routes_graph, **cond_filter)
    difference_operator = difference_op(train_graph, 2)
    time_vec = np.array([x[1] for x in train_graph.nodes(data='elapsed')])
    metric_dict = {}

    for value_lambda in lambda_seq:
        # Filtering on training data
        x = cp.Variable(shape=len(time_vec))
        loss = cp.Minimize((1 / 2) * cp.sum_squares(time_vec - x)
                           + value_lambda * cp.norm(difference_operator @ x, 1))
        problem = cp.Problem(loss)
        problem.solve(solver=cp.CVXOPT, verbose=False)
        congestion_df = pd.DataFrame(zip(train_graph.nodes, x.value), columns=['stop_id_post', 'congestion'])

        # Filtering the validation data
        if cond_filter[0] == 'weather':
            mask = (val['weather_main_post'] == cond_filter[1].capitalize())
        elif cond_filter[0] == 'day':
            mask = (val['day_of_week'] == cond_filter[1])
        elif cond_filter[0] == 'time':
            mask = (val['time_pre_datetime'].between_time(cond_filter[1][0], cond_filter[1][1]))
        else:
            raise ValueError('Illegal filtering option.')
        val = val[mask]

        # Compute validation metric for specific lambda
        val = val.merge(congestion_df, on='stop_id_post')
        error = np.absolute(val['congestion'] * val['stop_distance'] - val['elapsed'])
        metric_dict[value_lambda] = error

    return metric_dict
