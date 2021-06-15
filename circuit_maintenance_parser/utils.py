"""Utility functions for the Circuit Maintenance parsers."""

from geopy.geocoders import Nominatim  # type: ignore
from tzwhere import tzwhere  # type: ignore


def city_timezone(city: str) -> str:
    """Get the timezone for a given city.

    Args:
        city (str): Geographic location name
    """
    geolocator = Nominatim(user_agent="circuit_maintenance")
    location = geolocator.geocode(city)
    timezone = tzwhere.tzwhere()  # TODO: quite slow. Look for better alternative
    return timezone.tzNameAt(location.latitude, location.longitude)
