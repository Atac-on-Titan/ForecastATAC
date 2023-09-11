"""Module for parsing the validation metric files."""
import json
import logging
import re

import pandas as pd

logger = logging.getLogger()


class MetricParser:
    """Class for parsing a metric dictionary."""

    columns = ["name", "value", "lambda", "error"]

    def __init__(self, path: str):
        self.metrics = None
        self.path = path
        file_name = self.path.split("/")[-1]

        _, name, *value = file_name.split("_")
        self.name = name

        if name == "day" or name == "weather":
            self.value = value[0].split(".")[0]
        elif name == "time":
            matches = re.findall(r'\d+', file_name)
            numbers = [int(match) for match in matches]
            start, end = numbers[0], numbers[2]
            self.value = f"{start}-{end}"

    def parse(self):
        """Parses the metric file."""
        logger.info(f"Parsing metrics from: {self.path}")
        name_column = []
        value_column = []
        lambda_column = []
        error_column = []

        with open(self.path, "r") as file:
            data = json.load(file)

        for lambda_value, errors in data.items():
            n_rows = len(errors)
            name_column += [self.name] * n_rows
            value_column += [self.value] * n_rows
            lambda_column += [lambda_value] * n_rows
            error_column += errors

        df = pd.DataFrame([name_column, value_column, lambda_column, error_column]).T
        df.columns = self.columns
        self.metrics = df

    def to_pandas_df(self):
        return self.metrics

    def to_numpy(self):
        return self.metrics.to_numpy()

    def save(self, directory: str):
        logger.info(f"Saving metrics at {directory}")
        file_name = f"{self.name}_{self.value}.feather"
        file_path = f"{directory}/{file_name}"
        self.metrics.to_feather(file_path)
