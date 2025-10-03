"""Tests for generic parser."""

import os

import pytest
from pydantic import ValidationError

from circuit_maintenance_parser.output import CircuitImpact, Maintenance

dir_path = os.path.dirname(os.path.realpath(__file__))


@pytest.mark.parametrize(
    "attribute, value, exception",
    [
        ("account", None, ValidationError),
        ("account", 1, ValidationError),
        ("account", "good", None),
        ("end", None, ValidationError),
        ("end", "1533712380", ValidationError),
        ("end", 1533704400, ValidationError),
        ("end", 1533712380, None),
        ("start", None, ValidationError),
        ("start", "1533704400", ValidationError),
        ("start", 1533704400, None),
        ("stamp", None, ValidationError),
        ("stamp", "1533712380", ValidationError),
        ("stamp", 1533712380, None),
        ("maintenance_id", None, ValidationError),
        ("maintenance_id", 1, ValidationError),
        ("maintenance_id", "good", None),
        ("organizer", None, ValidationError),
        ("organizer", 1, ValidationError),
        ("organizer", "good", None),
        ("provider", None, ValidationError),
        ("provider", 1, ValidationError),
        ("provider", "good", None),
        ("status", None, ValidationError),
        ("status", 1, ValidationError),
        ("status", "good", ValidationError),
        ("status", "IN-PROCESS", None),
        # Non mandatory attributes
        ("sequence", None, None),
        ("sequence", "1", ValidationError),
        ("sequence", 1, None),
        ("uid", None, None),
        ("uid", 1, ValidationError),
        ("uid", "good", None),
        ("summary", None, None),
        ("summary", 1, ValidationError),
        ("summary", "good", None),
    ],
)
def test_maintenance_attributes(maintenance_data, attribute, value, exception):
    """Tests for Maintenance class attributes."""
    if value is None:
        del maintenance_data[attribute]
    else:
        maintenance_data[attribute] = value

    if exception is None:
        maint = Maintenance(**maintenance_data)
        if value is not None:
            assert getattr(maint, attribute) == value
    else:
        with pytest.raises(exception):
            Maintenance(**maintenance_data)


@pytest.mark.parametrize(
    "attribute, value, exception",
    [
        ("circuit_id", None, ValidationError),
        ("circuit_id", 1, ValidationError),
        ("circuit_id", "1", None),
        # Non mandatory attributes
        ("impact", None, None),
        ("impact", 1, ValidationError),
        ("impact", "wrong impact", ValidationError),
        ("impact", "OUTAGE", None),
    ],
)
def test_circuit_impact_attributes(circuitimpact_data, attribute, value, exception):
    """Tests for Circuit Impact class attributes."""
    if value is None:
        del circuitimpact_data[attribute]
    else:
        circuitimpact_data[attribute] = value

    if exception is None:
        maint = CircuitImpact(**circuitimpact_data)
        if value is not None:
            assert getattr(maint, attribute) == value
    else:
        with pytest.raises(exception):
            CircuitImpact(**circuitimpact_data)
