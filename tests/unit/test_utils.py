"""Tests for parser utils."""

import pytest

from circuit_maintenance_parser.utils import city_timezone


@pytest.mark.parametrize(
    "city, timezone",
    [
        ("North Bergen, NJ", "America/New_York"),
        # Removing some tests to speed up testing
        # ("Carlstadt, NJ", "America/New_York"),
        # ("Atlanta, GA", "America/New_York"),
        # ("New York, NY", "America/New_York"),
        # ("Worcester, MA", "America/New_York"),
        # ("Salt Lake City, Utah", "America/Denver"),
        # ("Los Angeles, CA", "America/Los_Angeles"),
        # ("Dublin, Ireland", "Europe/Dublin"),
        # ("Barcelona, Spain", "Europe/Madrid"),
        # ("Sydney, Australia", "Australia/Sydney"),
    ],
)
def test_city_timezones(city, timezone):
    """Tests for utility timezone function."""
    assert city_timezone(city) == timezone
