"""Used to setup fixtures to be used through tests"""
import pytest


@pytest.fixture()
def maintenance_data():
    """Returns a valid data set to create a Maintenance."""

    return {
        "account": "12345000",
        "maintenance_id": "VNOC-1-99999999999",
        "circuits": [{"circuit_id": "123", "impact": "NO-IMPACT"}, {"circuit_id": "456"}],
        "organizer": "myemail@example.com",
        "provider": "A random NSP",
        "sequence": 1,
        "stamp": 1533595768,
        "start": 1533704400,
        "end": 1533712380,
        "status": "COMPLETED",
        "summary": "This is a maintenance notification",
        "uid": "VNOC-1-99999999999",
    }


@pytest.fixture()
def circuitimpact_data():
    """Returns a valid data set to create a CircuitImpact."""

    return {
        "circuit_id": "1234",
        "impact": "DEGRADED",
    }
