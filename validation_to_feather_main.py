"""Main script for validation"""
import argparse
import logging.config
import os
from pathlib import Path

import pandas as pd

from validation import MetricParser

log_dir = "logs"
Path(log_dir).mkdir(parents=True, exist_ok=True)
logging.config.fileConfig("log_conf.ini")
logger = logging.getLogger()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Concatenate all validation metric files into a single dataframe.')
    parser.add_argument('-d', '--directory', type=str, required=True, help="The directory where the validation metric files can be found.")

    # Parse the arguments
    args = parser.parse_args()

    metrics = []

    for file_name in os.listdir(args.directory):
        file_path = f"{args.directory}/{file_name}"

        metric_parser = MetricParser(file_path)
        metric_parser.parse()
        metric_parser.save("data/validation/df")
