"""Utility functions for the library."""
import os
import logging
from typing import Tuple, Dict, Union
import csv

from geopy.exc import GeocoderUnavailable, GeocoderTimedOut, GeocoderServiceError  # type: ignore
from geopy.geocoders import Nominatim  # type: ignore
from tzwhere import tzwhere  # type: ignore
import backoff  # type: ignore

from .errors import ParserError

logger = logging.getLogger(__name__)

dirname = os.path.dirname(__file__)


class classproperty:  # pylint: disable=invalid-name,too-few-public-methods
    """Simple class-level equivalent of an @property."""

    def __init__(self, method):
        """Wrap a method."""
        self.getter = method

    def __get__(self, _, cls):
        """Call the wrapped method."""
        return self.getter(cls)


class Geolocator:
    """Class to obtain Geo Location coordinates."""

    # Keeping caching of local DB and timezone in the class
    _db_location: Dict[Union[Tuple[str, str], str], Tuple[float, float]] = {}
    _timezone = None

    @classproperty
    def timezone(cls):  # pylint: disable=no-self-argument
        """Load the timezone resolver."""
        if cls._timezone is None:
            cls._timezone = tzwhere.tzwhere()
            logger.info("Loaded local timezone resolver.")
        return cls._timezone

    @classproperty
    def db_location(cls):  # pylint: disable=no-self-argument
        """Load the locations DB from CSV into a Dict."""
        if not cls._db_location:
            with open(os.path.join(dirname, "data", "worldcities.csv")) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Index by city and country
                    cls._db_location[(row["city_ascii"], row["country"])] = (float(row["lat"]), float(row["lng"]))
                    # Index by city (first entry wins if duplicated names)
                    if row["city_ascii"] not in cls._db_location:
                        cls._db_location[row["city_ascii"]] = (float(row["lat"]), float(row["lng"]))
        return cls._db_location

    def get_location(self, city: str) -> Tuple[float, float]:
        """Get location."""
        try:
            location_coordinates = self.get_location_from_local_file(city)
        except ValueError:
            location_coordinates = self.get_location_from_api(city)

        logger.debug(
            "Resolved city %s to coordinates: lat %s - lon %s", city, location_coordinates[0], location_coordinates[1],
        )
        return location_coordinates

    def get_location_from_local_file(self, city: str) -> Tuple[float, float]:
        """Get location from Local DB."""
        city_name = city.split(", ")[0]
        country = city.split(", ")[-1]

        lat, lng = self.db_location.get(  # pylint: disable=no-member
            (city_name, country), self.db_location.get(city_name, (None, None))  # pylint: disable=no-member
        )
        if lat and lng:
            logger.debug("Resolved %s to lat %s, lon %sfrom local locations DB.", city, lat, lng)
            return (lat, lng)

        logger.debug("City %s was not resolvable in the local locations DB.", city)
        raise ValueError

    @staticmethod
    @backoff.on_exception(
        backoff.expo, (GeocoderUnavailable, GeocoderTimedOut, GeocoderServiceError), max_time=10, logger=logger,
    )
    def get_location_from_api(city: str) -> Tuple[float, float]:
        """Get location from API."""
        geolocator = Nominatim(user_agent="circuit_maintenance")
        location = geolocator.geocode(city)  # API call to OpenStreetMap web service
        logger.debug("Resolved %s to %s from OpenStreetMap webservice.", city, location)
        return (location.latitude, location.longitude)

    def city_timezone(self, city: str) -> str:
        """Get the timezone for a given city.

        Args:
            city (str): Geographic location name
        """
        if self.timezone is not None:
            try:
                latitude, longitude = self.get_location(city)
                timezone = self.timezone.tzNameAt(latitude, longitude)  # pylint: disable=no-member
                if not timezone:
                    # In some cases, given a latitued and longitued, the tzwhere library returns
                    # an empty timezone, so we try with the coordinates from the API as an alternative
                    latitude, longitude = self.get_location_from_api(city)
                    timezone = self.timezone.tzNameAt(latitude, longitude)  # pylint: disable=no-member

                if timezone:
                    logger.debug("Matched city %s to timezone %s", city, timezone)
                    return timezone
            except Exception as exc:
                logger.error("Cannot obtain the timezone for city %s: %s", city, exc)
                raise ParserError(  # pylint: disable=raise-missing-from
                    f"Cannot obtain the timezone for city {city}: {exc}"
                )
        raise ParserError("Timezone resolution not properly initalized.")


def rgetattr(obj, attr):
    """Recursive GetAttr to look for nested attributes."""
    nested_value = getattr(obj, attr)
    if not nested_value:
        return obj
    return rgetattr(nested_value, attr)
