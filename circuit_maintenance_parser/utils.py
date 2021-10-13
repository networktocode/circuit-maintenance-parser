"""Utility functions for the library."""
from geopy.exc import GeocoderUnavailable, GeocoderTimedOut, GeocoderServiceError  # type: ignore
from geopy.geocoders import Nominatim  # type: ignore
from tzwhere import tzwhere  # type: ignore
from .errors import ParserError


def city_timezone(city: str) -> str:
    """Get the timezone for a given city.

    Args:
        city (str): Geographic location name
    """
    try:
        geolocator = Nominatim(user_agent="circuit_maintenance")
        location = geolocator.geocode(city)  # API call to OpenStreetMap web service
        timezone = (
            tzwhere.tzwhere()
        )  # TODO: Offline loading of timezone location data is quite slow. Look for better alternative
        return timezone.tzNameAt(location.latitude, location.longitude)
    except (GeocoderUnavailable, GeocoderTimedOut, GeocoderServiceError):
        raise ParserError(  # pylint: disable=raise-missing-from
            "Cannot connect to the remote Geolocator API to determine timezone"
        )


def rgetattr(obj, attr):
    """Recursive GetAttr to look for nested attributes."""
    nested_value = getattr(obj, attr)
    if not nested_value:
        return obj
    return rgetattr(nested_value, attr)
