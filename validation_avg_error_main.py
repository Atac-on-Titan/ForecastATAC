"""Main script for validation"""
import argparse
import logging.config
import os
from pathlib import Path

import pandas as pd

from validation import MetricParser, to_mean_error

log_dir = "logs"
Path(log_dir).mkdir(parents=True, exist_ok=True)
logging.config.fileConfig("log_conf.ini")
logger = logging.getLogger()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Concatenate all validation metric dataframes into a single dataframe with average errors.')
    parser.add_argument('-d', '--directory', type=str, required=True, help="The directory where the validation metric "
                                                                           "feather dataframes can be found.")

    # Parse the arguments
    args = parser.parse_args()

    dfs = []

    output_dir = "data/validation"

    for file_name in os.listdir(args.directory):
        file_path = f"{args.directory}/{file_name}"
        logger.info(f"Reading dataframe from {file_path}")
        df = pd.read_feather(file_path)

        logger.info(f"Extracting mean error.")
        df = to_mean_error(df)

        dfs.append(df)

    logger.info(f"Concatenating {len(dfs)} into a single dataframe")
    df = pd.concat(dfs, ignore_index=True)

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = f"{output_dir}/avg_error.feather"
    logger.info(f"Saving final dataframe to {output_path}")
    df.to_feather(output_path)
