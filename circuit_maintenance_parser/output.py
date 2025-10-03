"""Parser uses MAINTNOTE defined.

See: https://tools.ietf.org/html/draft-gunter-calext-maintenance-notifications-00
"""

import json
from enum import Enum
from typing import List

try:
    from pydantic import field_validator
except ImportError:
    # TODO: This exception handling is required for Pydantic 1.x compatibility. To be removed when the dependency is deprecated.
    from pydantic import validator as field_validator  # type: ignore


from pydantic import BaseModel, PrivateAttr, StrictInt, StrictStr


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
    - "COMPLETED": Indicates maintenance event completed (e.g. closed).
    - "RE-SCHEDULED": Indicates maintenance event was re-scheduled.
    - "NO-CHANGE": Indicates status is unchanged from a previous notification (dummy value)
    """

    TENTATIVE = "TENTATIVE"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    IN_PROCESS = "IN-PROCESS"
    COMPLETED = "COMPLETED"
    RE_SCHEDULED = "RE-SCHEDULED"

    NO_CHANGE = "NO-CHANGE"


class CircuitImpact(BaseModel, extra="forbid"):
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
        ... ) # doctest:+ELLIPSIS
        Traceback (most recent call last):
        ...
        pydantic_core._pydantic_core.ValidationError: 1 validation error for CircuitImpact
        impact
          Input should be 'NO-IMPACT', 'REDUCED-REDUNDANCY', 'DEGRADED' or 'OUTAGE' [type=enum, input_value='wrong impact', input_type=str]
        ...
    """

    circuit_id: StrictStr
    # Optional Attributes
    impact: Impact = Impact.OUTAGE

    # pylint: disable=no-self-argument
    @field_validator("impact")
    @classmethod
    def validate_impact_type(cls, value):
        """Validate Impact type."""
        if value not in Impact:
            raise ValueError("Not a valid impact type")
        return value

    def to_json(self):
        """Return a JSON serializable dict."""
        return {
            "circuit_id": self.circuit_id,
            "impact": self.impact.value,
        }


class Metadata(BaseModel):
    """Metadata class to provide context about the Maintenance object."""

    provider: StrictStr
    processor: StrictStr
    parsers: List[StrictStr]
    generated_by_llm: bool = False
    tokens_used: int = 0


class Maintenance(BaseModel, extra="forbid"):
    """Maintenance class.

    Mandatory attributes:
        provider: identifies the provider of the service that is the subject of the maintenance notification
        account:  identifies an account associated with the service that is the subject of the maintenance notification
        maintenance_id:  contains text that uniquely identifies the maintenance that is the subject of the notification
        circuits: list of circuits affected by the maintenance notification and their specific impact. Note this can be
            an empty list for notifications with a CANCELLED or COMPLETED status if the provider does not populate the
            circuit list.
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
        >>> metadata = Metadata(
        ...     processor="SimpleProcessor",
        ...     provider="genericprovider",
        ...     parsers=["EmailDateParser"]
        ... )
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
        ...     _metadata=metadata,
        ... )
        Maintenance(provider='A random NSP', account='12345000', maintenance_id='VNOC-1-99999999999', status=<Status.COMPLETED: 'COMPLETED'>, circuits=[CircuitImpact(circuit_id='123', impact=<Impact.NO_IMPACT: 'NO-IMPACT'>), CircuitImpact(circuit_id='456', impact=<Impact.OUTAGE: 'OUTAGE'>)], start=1533704400, end=1533712380, stamp=1533595768, organizer='myemail@example.com', uid='1111', sequence=1, summary='This is a maintenance notification')
    """

    provider: StrictStr
    account: StrictStr
    maintenance_id: StrictStr
    status: Status
    circuits: List[CircuitImpact]
    start: StrictInt
    end: StrictInt
    stamp: StrictInt
    organizer: StrictStr
    _metadata: Metadata = PrivateAttr()

    # Non mandatory attributes
    uid: StrictStr = "0"
    sequence: StrictInt = 1
    summary: StrictStr = ""

    def __init__(self, **data):
        """Initialize the Maintenance object."""
        metadata = data.pop("_metadata")
        super().__init__(**data)
        self._metadata = metadata

    @field_validator("status")
    @classmethod
    def validate_status_type(cls, value):
        """Validate Status type."""
        if value not in Status:
            raise ValueError("Not a valid status type")
        return value

    @field_validator("provider", "account", "maintenance_id", "organizer")
    @classmethod
    def validate_empty_strings(cls, value):
        """Validate emptry strings."""
        if value in ["", "None"]:
            raise ValueError("String is empty or 'None'")
        return value

    @field_validator("circuits")
    @classmethod
    def validate_empty_circuits(cls, value, values):
        """Validate non-cancel notifications have a populated circuit list."""
        try:
            values = values.data  # pydantic 2.x
        except AttributeError:  # pydantic 1.x
            pass
        if len(value) < 1 and values["status"] not in (Status.CANCELLED, Status.COMPLETED):
            raise ValueError("At least one circuit has to be included in the maintenance")
        return value

    @field_validator("end")
    @classmethod
    def validate_end_time(cls, end, values):
        """Validate that End time happens after Start time."""
        try:
            values = values.data  # pydantic 2.x
        except AttributeError:  # pydantic 1.x
            pass
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

    @property
    def metadata(self) -> Metadata:
        """Get Maintenance Metadata."""
        return self._metadata
