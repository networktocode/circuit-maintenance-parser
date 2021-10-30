"""Utility functions for the library."""
import os
import logging
from typing import Tuple

import pandas as pd  # type: ignore
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut, GeocoderServiceError  # type: ignore
from geopy.geocoders import Nominatim  # type: ignore
from tzwhere import tzwhere  # type: ignore
import backoff  # type: ignore

from .errors import ParserError

logger = logging.getLogger(__name__)

dirname = os.path.dirname(__file__)


class Geolocator:
    """Class to obtain Geo Location coordinates."""

    # Keeping caching of local DB and timezone in the class
    db_location = None
    timezone = None

    def __init__(self):
        """Initialize instance."""
        self.load_db_location()
        self.load_timezone()

    @classmethod
    def load_timezone(cls):
        """Load the localtions DB."""
        if cls.timezone is None:
            cls.timezone = tzwhere.tzwhere()

    @classmethod
    def load_db_location(cls):
        """Load the localtions DB."""
        if cls.db_location is None:
            logger.info("Loading local locations DB.")
            cls.db_location = pd.read_csv(os.path.join(dirname, "data", "worldcities.csv"))

    def get_location(self, city: str) -> Tuple[float, float]:
        """Get location."""
        try:
            return self.get_location_from_local_file(city)
        except ValueError:
            return self.get_location_from_api(city)

    def get_location_from_local_file(self, city: str) -> Tuple[float, float]:
        """Get location from Local DB."""
        city_name = city.split(", ")[0]
        country = city.split(", ")[-1]

        if self.db_location is not None:
            # 1. We try to match city name and country
            location = self.db_location.query(f"city_ascii == '{city_name}' & country == '{country}'")
            if not location.empty:
                return (location.lat.values[0], location.lng.values[0])

            # 2. We try to match only city name
            location = self.db_location.query(f"city_ascii == '{city_name}'")
            if not location.empty:
                return (location.lat.values[0], location.lng.values[0])

        raise ValueError

    @staticmethod
    @backoff.on_exception(
        backoff.expo, (GeocoderUnavailable, GeocoderTimedOut, GeocoderServiceError), max_time=10, logger=logger,
    )
    def get_location_from_api(city: str) -> Tuple[float, float]:
        """Get location from API."""
        geolocator = Nominatim(user_agent="circuit_maintenance")
        location = geolocator.geocode(city)  # API call to OpenStreetMap web service
        return (location.latitude, location.longitude)

    def city_timezone(self, city: str) -> str:
        """Get the timezone for a given city.

        Args:
            city (str): Geographic location name
        """
        if self.timezone is not None:
            try:
                latitude, longitude = self.get_location(city)
                timezone = self.timezone.tzNameAt(latitude, longitude)
                if not timezone:
                    # If even with the location we can't find the timezone, we try getting the location
                    # from API.
                    latitude, longitude = self.get_location_from_api(city)
                    timezone = self.timezone.tzNameAt(latitude, longitude)

                if timezone:
                    return timezone
            except Exception:
                raise ParserError(f"Cannot obtain the timezone for city {city}")  # pylint: disable=raise-missing-from
        raise ParserError("Timezone resolution not properly initalized.")


def rgetattr(obj, attr):
    """Recursive GetAttr to look for nested attributes."""
    nested_value = getattr(obj, attr)
    if not nested_value:
        return obj
    return rgetattr(nested_value, attr)
