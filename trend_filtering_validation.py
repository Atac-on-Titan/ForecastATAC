"""Script for running the validation."""
import argparse
import json
import logging.config
import os
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from preprocessing import build_route_stops, build_stop_graph
from trend_filtering import trend_filter_validate, FilterManager

log_dir = "logs"
Path(log_dir).mkdir(parents=True, exist_ok=True)
logging.config.fileConfig("log_conf.ini")
logger = logging.getLogger()


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
    os.environ["OMP_NUM_THREADS"] = "4"
    # Create an argument parser with arguments
    parser = argparse.ArgumentParser(description='Run the trend filtering validation.')
    parser.add_argument('-f', '--filter', type=str, help="Path to a .json file with the filters for which to run the validation.")

    # Parse the arguments
    args = parser.parse_args()

    filter_manager = FilterManager(args.filter)
    uncompleted_filters = filter_manager.get_uncompleted_filters()

    # create data directory if not exists
    Path("data").mkdir(parents=True, exist_ok=True)
    Path("data/static").mkdir(parents=True, exist_ok=True)

    # download the necessary data
    bucket_name = "statistical-learning"
    files_to_download = ["trip_live_final.feather", 'static/trips.txt', 'static/stop_times.txt', 'static/stops.txt', 'static/routes.txt']
    file_paths = ["data/trip_live_final.feather", 'data/static/trips.txt', 'data/static/stop_times.txt', 'data/static/stops.txt', 'data/static/routes.txt']

    logger.info(f"Downloading static and preprocessed final ATAC data if they don't exist in data/ directory.")
    for object_key, local_file_path in zip(files_to_download, file_paths):
        s3_download(bucket_name, object_key, local_file_path)

    # check that all necessary files are present
    if not all(map(lambda local_file_path: Path(local_file_path).exists(), file_paths)):
        logger.error("Not all files present, analysis not possible.")
        exit(1)

    logger.info("All files present.")

    # load the data
    logger.info("Loading the data.")
    trip_live = pd.read_feather("data/trip_live_final.feather")
    route_stops = build_route_stops('data/static/trips.txt', 'data/static/stop_times.txt', 'data/static/stops.txt',
                                    'data/static/routes.txt')
    init_graph = build_stop_graph('data/static/stops.txt', route_stops)

    # validation
    logger.info("Creating train-val split.")
    trip_live['time_pre_datetime'] = pd.to_datetime(trip_live['time_pre_datetime']).dt.date
    val_mask = trip_live['time_pre_datetime'] >= np.datetime64('2023-06-09')
    train_data = trip_live[~val_mask]
    val_data = trip_live[val_mask]

    lambda_seq = (1, 2, 4, 8, 16, 32, 64, 128, 256, 512)
    logger.info(f"Using lambda values: {lambda_seq}")

    validation_dir = "validation"
    logger.info(f"Creating directory {validation_dir} for validation results.")
    Path(validation_dir).mkdir(parents=True, exist_ok=True)

    for trend_filter in uncompleted_filters:
        logger.info(f"Running trend filter validation with filter: {trend_filter} and lambda values: {lambda_seq}")
        metrics = trend_filter_validate(train_data, val_data, init_graph, lambda_seq, trend_filter)

        metrics_file = f"{validation_dir}/val_{trend_filter.file_name()}.json"
        logger.info(f"Saving validation metrics to {metrics_file}")
        with open(metrics_file, "w") as outfile:
            json.dump(metrics, outfile)

        logger.info(f"Marking {trend_filter} as completed.")
        trend_filter.completed = True
        filter_manager.save(args.filter)
