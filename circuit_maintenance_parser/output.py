"""Parser uses MAINTNOTE defined.

See: https://tools.ietf.org/html/draft-gunter-calext-maintenance-notifications-00
"""

import json
from enum import Enum

from typing import List

from pydantic import BaseModel, validator, StrictStr, StrictInt, Extra


class Impact(str, Enum):
    """Types of maintenance impact.

    - "NO-IMPACT" indicates that there is no expected impact to services in scope for the maintenance.
    - "REDUCED-REDUNDANCY" indicates that during the maintenance the services in scope are expected to continue
    operating without any consumer visible impact, however the services are without their normal level of redundancy.
    While operating at a reduced level of redundancy, failure of supporting infrastructure outside the scope of the
    maintenance occurring concurrent to the maintenance may cause consumer visible service impact.
    - "DEGRADED" indicates that negative impact to services in scope for the maintenance is expected, however the
    maintenance will not result in a total service outage.
    - "OUTAGE" indicates that the services in scope of the maintenance are expected to be completely out of service.
    """

    NO_IMPACT = "NO-IMPACT"
    REDUCED_REDUNDANCY = "REDUCED-REDUNDANCY"
    DEGRADED = "DEGRADED"
    OUTAGE = "OUTAGE"


class Status(str, Enum):
    """Types of maintenance status.

    - "TENTATIVE": Indicates maintenance event is possible.
    - "CONFIRMED": Indicates maintenance event is definite.
    - "CANCELLED": Indicates maintenance event was cancelled.
    - "IN-PROCESS": Indicates maintenance event is in process (e.g. open).
    - "COMPLETED":Indicates maintenance event completed (e.g. closed).
    - "RE-SCHEDULED": Indicates maintenance event was re-scheduled.
    """

    TENTATIVE = "TENTATIVE"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    IN_PROCESS = "IN-PROCESS"
    COMPLETED = "COMPLETED"
    RE_SCHEDULED = "RE-SCHEDULED"


class CircuitImpact(BaseModel, extra=Extra.forbid):
    """CircuitImpact class.

    Each Circuit Maintenance can contain multiple affected circuits, and each one can have a different level of impact.

    Attributes:
        circuit_id: Circuit unique identifier.
        impact:     Impact level (default: OUTAGE).

    Examples:
        >>> CircuitImpact(
        ...     circuit_id="1234"
        ... )
        CircuitImpact(circuit_id='1234', impact=<Impact.OUTAGE: 'OUTAGE'>)

        >>> CircuitImpact(
        ...     circuit_id="1234",
        ...     impact="wrong impact"
        ... )
        Traceback (most recent call last):
        ...
        pydantic.error_wrappers.ValidationError: 1 validation error for CircuitImpact
        impact
          value is not a valid enumeration member; permitted: 'NO-IMPACT', 'REDUCED-REDUNDANCY', 'DEGRADED', 'OUTAGE' (type=type_error.enum; enum_values=[<Impact.NO_IMPACT: 'NO-IMPACT'>, <Impact.REDUCED_REDUNDANCY: 'REDUCED-REDUNDANCY'>, <Impact.DEGRADED: 'DEGRADED'>, <Impact.OUTAGE: 'OUTAGE'>])
    """

    circuit_id: StrictStr
    # Optional Attributes
    impact: Impact = Impact.OUTAGE

    # pylint: disable=no-self-argument,no-self-use
    @validator("impact")
    def validate_impact_type(cls, value):
        """Validate Impact type."""
        if value not in Impact:
            raise ValueError("Not a valid impact type")
        return value


class Maintenance(BaseModel, extra=Extra.forbid):
    """Maintenance class.

    Mandatory attributes:
        provider: identifies the provider of the service that is the subject of the maintenance notification
        account:  identifies an account associated with the service that is the subject of the maintenance notification
        maintenance_id:  contains text that uniquely identifies the maintenance that is the subject of the notification
        circuits: list of circuits affected by the maintenance notification and their specific impact
        status: defines the overall status or confirmation for the maintenance
        start: timestamp that defines the start date of the maintenance in GMT
        end: timestamp that defines the end date of the maintenance in GMT
        stamp: timestamp that defines the update date of the maintenance in GMT
        organizer: defines the contact information included in the original notification

    Optional attributes:
        summary: description of the maintenace notification
        uid: specific unique identifier for each notification
        sequence: sequence number - initially zero - to serialize updates in case they are received or processed out of
            order

    Example:
        >>> Maintenance(
        ...     account="12345000",
        ...     end=1533712380,
        ...     maintenance_id="VNOC-1-99999999999",
        ...     circuits=[{"circuit_id": "123",  "impact": "NO-IMPACT"}, {"circuit_id": "456"}],
        ...     organizer="myemail@example.com",
        ...     provider="A random NSP",
        ...     sequence=1,
        ...     stamp=1533595768,
        ...     start=1533704400,
        ...     status="COMPLETED",
        ...     summary="This is a maintenance notification",
        ...     uid="1111",
        ... )
        Maintenance(provider='A random NSP', account='12345000', maintenance_id='VNOC-1-99999999999', circuits=[CircuitImpact(circuit_id='123', impact=<Impact.NO_IMPACT: 'NO-IMPACT'>), CircuitImpact(circuit_id='456', impact=<Impact.OUTAGE: 'OUTAGE'>)], status=<Status.COMPLETED: 'COMPLETED'>, start=1533704400, end=1533712380, stamp=1533595768, organizer='myemail@example.com', uid='1111', sequence=1, summary='This is a maintenance notification')
    """

    provider: StrictStr
    account: StrictStr
    maintenance_id: StrictStr
    circuits: List[CircuitImpact]
    status: Status
    start: StrictInt
    end: StrictInt
    stamp: StrictInt
    organizer: StrictStr

    # Non mandatory attributes
    uid: StrictStr = "0"
    sequence: StrictInt = 1
    summary: StrictStr = ""

    # pylint: disable=no-self-argument,no-self-use
    @validator("status")
    def validate_status_type(cls, value):
        """Validate Status type."""
        if value not in Status:
            raise ValueError("Not a valid status type")
        return value

    @validator("provider", "account", "maintenance_id", "organizer")
    def validate_empty_strings(cls, value):
        """Validate emptry strings."""
        if value in ["", "None"]:
            raise ValueError("String is empty or 'None'")
        return value

    @validator("circuits")
    def validate_empty_circuits(cls, value):
        """Validate emptry strings."""
        if len(value) < 1:
            raise ValueError("At least one circuit has to be included in the maintenance")
        return value

    @validator("end")
    def validate_end_time(cls, end, values):
        """Validate that End time happens after Start time."""
        if "start" not in values:
            raise ValueError("Start time is a mandatory attribute.")
        start = values["start"]

        if end <= start:
            raise ValueError(f"End time ({end}) should happen later than start time({start}).")
        return end

    def slug(self) -> str:
        """Get slug for provider name."""
        return self.provider.split()[0].lower()

    def to_json(self) -> str:
        """Get JSON representation of the class object."""
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=2)
