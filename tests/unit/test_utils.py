"""Tests for parser utils."""

import pytest

from circuit_maintenance_parser.utils import Geolocator

geolocator = Geolocator()


@pytest.mark.parametrize(
    "city, timezone",
    [
        ("North Bergen, NJ", "America/New_York"),
        ("Carlstadt, NJ", "America/New_York"),
        ("Atlanta, GA", "America/New_York"),
        ("New York, NY", "America/New_York"),
        ("Worcester, MA", "America/New_York"),
        ("Salt Lake City, Utah", "America/Denver"),
        ("Los Angeles, CA", "America/Los_Angeles"),
        ("Dublin, Ireland", "Europe/Dublin"),
        ("Barcelona, Spain", "Europe/Madrid"),
        ("Sydney, Australia", "Australia/Sydney"),
        ("Guadalajara, Spain", "Europe/Madrid"),
        ("Guadalajara, Mexico", "America/Mexico_City"),
    ],
)
def test_city_timezones(city, timezone):
    """Tests for utility timezone function."""
    assert geolocator.city_timezone(city) == timezone
