"""Module for ATAC stops."""
import csv
import logging.config
import os
from dataclasses import dataclass
from typing import Union

import pandas as pd
from dotenv import load_dotenv

load_dotenv()
log_conf_path = os.getenv("log_conf")

if log_conf_path:
    # Load the logging configuration from the logging.ini file
    logging.config.fileConfig(log_conf_path)
else:
    logging.config.fileConfig("log_conf.ini")

# Create a logger
logger = logging.getLogger(__name__)  # Replace with the logger name from your config


@dataclass
class Stop:
    id: str
    code: str
    name: str
    desc: str
    lat: float
    lon: float
    url: str
    wheelchair_boarding: str
    timezone: str
    location_type: str
    parent_station: str

    @staticmethod
    def from_pandas_row(row):
        return Stop(row['stop_id'], row['stop_code'], row['stop_name'], row['stop_desc'], row['stop_lat'],
                    row['stop_lon'],
                    row['stop_url'], row['wheelchair_boarding'], row['stop_timezone'], row['location_type'],
                    row['parent_station'])


class StopManager:
    """Holds ATAC stops and has methods for searching for them."""

    def __init__(self, stops):
        if type(stops) == str:
            self.stops = load_stops(stops)
        elif type(stops) == list:
            self.stops = stops
        elif type(stops) == pd.DataFrame:
            self.stops = [Stop.from_pandas_row(row) for row in stops.iterrows()]

    def find(self, id: Union[str, list]):
        """Gets the stop for the specific id.

        :arg
            id (Union[str, list]): the ID or IDs of the stop/s to find.

        :return
            (Union[Stop, None]): a Stop object with a matching ID if found, otherwise returns None.
        """
        if type(id) == str:
            stops = list(filter(lambda stop: stop.id == id, self.stops))
        elif type(id) == list:
            stops = list(filter(lambda stop: stop.id in id, self.stops))
        else:
            raise ValueError(f"id must be of type str of list.")

        if len(stops) == 1:
            return stops[0]
        if len(stops) > 1:
            return stops
        return None


def load_stops(file_path: str):
    """Loads the stops from the provided path.

    :arg
        file_path (str): the path to a csv file with the stops.

    :return
        (list): a list of Stop objects.
    """

    stops = []
    logger.info(f"Loading stops from {file_path}")
    with open(file_path) as file:
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            stop = Stop(row['stop_id'], row['stop_code'], row['stop_name'], row['stop_desc'], row['stop_lat'],
                        row['stop_lon'],
                        row['stop_url'], row['wheelchair_boarding'], row['stop_timezone'], row['location_type'],
                        row['parent_station'])
            stops.append(stop)

    return stops
