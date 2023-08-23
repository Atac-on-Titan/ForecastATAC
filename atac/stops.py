"""Module for ATAC stops."""
import csv
import logging.config
import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load the logging configuration from the logging.ini file
logging.config.fileConfig('resources/test_log_conf.ini')

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


class StopManager:
    """Holds ATAC stops and has methods for searching for them."""

    def __init__(self, stops):
        if type(stops) == str:
            self.stops = load_stops(stops)
        else:
            self.stops = stops

    def find_stop(self, id: str):
        """Gets the stop for the specific id.

        :arg
            id (str): the ID of the stop to find.

        :return
            (Union[Stop, None]): a Stop object with a matching ID if found, otherwise returns None.
        """
        stop = list(filter(lambda stop: stop.id == id, self.stops))
        if stop:
            return stop[0]
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


load_dotenv()
stop_file_path = os.getenv("stops")
stop_manager = StopManager(stop_file_path)
