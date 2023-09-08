"""Script for running the validation."""
import logging.config
from datetime import datetime
from pathlib import Path

import boto3
import cvxpy as cp
import numpy as np
import pandas as pd
import requests

from preprocessing import build_route_stops, build_stop_graph
from trend_filtering import vertex_signal, difference_op, trend_filter_validate


def s3_download(bucket_name, object_key, local_file_path):
    # we only want to download the data once.
    if not Path(local_file_path).exists():
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{object_key}"

        logger.info(f"Data does not exist locally, downloading from {s3_url}")
        # Make an HTTP GET request to the pre-signed URL to download the object
        response = requests.get(s3_url)

        if response.status_code == 200:
            # Save the content of the response to a local file
            logger.info(f"Download successful, saving data at {local_file_path}")
            with open(local_file_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Object '{object_key}' downloaded to '{local_file_path}' successfully.")

        else:
            logger.error(f"Failed to download object '{object_key}'. Status code: {response.status_code}")
            exit(1)

    else:
        logger.info(f"Data exists locally at {local_file_path}")


if __name__ == "__main__":
    log_dir = "logs"
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logging.config.fileConfig("log_conf.ini")
    logger = logging.getLogger("trend-filtering-validation")
    logger.setLevel(logging.INFO)

    # create data directory if not exists

    Path("data").mkdir(parents=True, exist_ok=True)
    Path("data/static").mkdir(parents=True, exist_ok=True)

    bucket_name = "statistical-learning"
    files_to_download = ["trip_live_final.feather", 'static/trips.txt', 'static/stop_times.txt', 'static/stops.txt', 'static/routes.txt']
    file_paths = ["data/live_data_final.feather", 'data/static/trips.txt', 'data/static/stop_times.txt', 'data/static/stops.txt', 'data/static/routes.txt']

    for object_key, local_file_path in zip(files_to_download, file_paths):
        s3_download(bucket_name, object_key, local_file_path)

    if not all(map(lambda: Path(local_file_path).exists(), file_paths)):
        logger.error("Not all files present, analysis not possible.")
        exit(1)

    logger.info("All files downloaded.")

    trip_live = pd.read_feather("data/trip_live_final.feather")

    route_stops = build_route_stops('data/static/trips.txt', 'data/static/stop_times.txt', 'data/static/stops.txt',
                                    'data/static/routes.txt')
    init_graph = build_stop_graph('data/static/stops.txt', route_stops)

    test_graph = vertex_signal(trip_live, init_graph, wtr='clear')

    difference = difference_op(test_graph, 2)
    vector_time = np.array([x[1] for x in test_graph.nodes(data='elapsed')])

    vlambda = 0.1  # Choosing the regularization hyperparameter
    x = cp.Variable(shape=len(vector_time))  # Variable
    obj = cp.Minimize((1 / 2) * cp.sum_squares(vector_time - x)
                      + vlambda * cp.norm(difference @ x, 1))  # defining the optimization problem
    prob = cp.Problem(obj)

    prob.solve(solver=cp.CVXOPT, verbose=True)
    print('Solver status: {}'.format(prob.status))

    congestion_dict = dict(zip(test_graph.nodes, x.value))

    trip_live['time_pre_datetime'] = pd.to_datetime(trip_live['time_pre_datetime']).dt.date
    val_mask = trip_live['time_pre_datetime'] >= np.datetime64('2023-06-09')
    train_data = trip_live[~val_mask]
    val_data = trip_live[val_mask]
