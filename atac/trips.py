"""Module for making available ATAC trip data."""
import csv
import logging.config
import os
from dataclasses import dataclass

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
class Trip:
    route_id: str
    service_id: str
    trip_id: str
    trip_headsign: str
    trip_short_name: str
    direction_id: str
    block_id: str
    shape_id: str
    wheelchair_accessible: str
    exceptional: str

    @staticmethod
    def from_pandas_row(row):
        return Trip(row['route_id'], row['service_id'], row['trip_id'], row['trip_headsign'], row['trip_short_name'],
                        row['direction_id'],
                        row['block_id'], row['shape_id'], row['wheelchair_accessible'], row['exceptional'])


def load_trips(file_path: str):
    """Loads a trip path file and creates trip objects.

    :arg
        file_path (str): the path to the ATAC trip csv file.

    :return
        (list): a list of Trip objects.
    """
    trips = []
    logger.info(f"Loading stops from {file_path}")
    with open(file_path) as file:
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            stop = Trip(row['route_id'], row['service_id'], row['trip_id'], row['trip_headsign'], row['trip_short_name'],
                        row['direction_id'],
                        row['block_id'], row['shape_id'], row['wheelchair_accessible'], row['exceptional'])
            trips.append(stop)

    return trips


class TripManager:
    """Manages ATAC trip objects."""

    def __init__(self, trips):
        if type(trips) == str:
            self.trips = load_trips(trips)
        elif type(trips) == list:
            self.trips = trips
        elif type(trips) == pd.DataFrame:
            self.trips = [Trip.from_pandas_row(row) for row in trips.iterrows()]

    def find(self, **kwargs):
        if "route_id" in kwargs:
            trips = list(filter(lambda trip: trip.route_id == kwargs.get("route_id"), self.trips))
        elif "service_id" in kwargs:
            trips = list(filter(lambda trip: trip.service_id == kwargs.get("service_id"), self.trips))
        elif "trip_id" in kwargs:
            trips = list(filter(lambda trip: trip.trip_id == kwargs.get("trip_id"), self.trips))
        else:
            raise ValueError(f"Keyword arguments must contain either: route_id, service_id, trip_id.")

        return trips
