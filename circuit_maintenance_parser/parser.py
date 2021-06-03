"""Definition of Mainentance Notification base classes."""

import base64
import calendar
import datetime
import quopri
from typing import Iterable, Union, Dict, Mapping

import bs4  # type: ignore
from bs4.element import ResultSet  # type: ignore

from pydantic import BaseModel, ValidationError
from icalendar import Calendar  # type: ignore

from circuit_maintenance_parser.errors import ParsingError, MissingMandatoryFields
from circuit_maintenance_parser.output import Maintenance, Status, Impact, CircuitImpact

# pylint: disable=no-member


class MaintenanceNotification(BaseModel):
    """MaintenanceNotification class.

    This is the base class that is created from a Circuit Maintenance notification containing

    Attributes:
        raw: Raw notification message (bytes)
        provider_type: Identifier of the provider of the notification
        sender: Identifier of the source of the notification (default "")
        subject: Subject of the notification (default "")
        source: Identifier of the source where this notification was obtained (default "")

    Examples:
        >>> MaintenanceNotification(
        ...     raw=b"raw_message",
        ...     sender="my_email@example.com",
        ...     subject="Urgent notification for circuits X and Y",
        ...     source="gmail",
        ...     provider_type="ntt",
        ... )
        MaintenanceNotification(raw=b'raw_message', provider_type='ntt', sender='my_email@example.com', subject='Urgent notification for circuits X and Y', source='gmail')

        >>> MaintenanceNotification(raw=b"raw_message")
        Traceback (most recent call last):
        ...
        pydantic.error_wrappers.ValidationError: 1 validation error for MaintenanceNotification
        provider_type
          field required (type=value_error.missing)

        >>> MaintenanceNotification(b"raw_message")
        Traceback (most recent call last):
        ...
        TypeError: __init__() takes exactly 1 positional argument (2 given)

    """

    raw: bytes
    provider_type: str
    sender: str = ""
    subject: str = ""
    source: str = ""

    # Internal placeholder for parser customization
    _default_organizer = "unknown"
    _default_provider = "unknown"

    # Data Type used as payload
    _data_type = "text/plain"

    @classmethod
    def get_data_type(cls) -> str:
        """Return the expected data type."""
        return cls._data_type

    @classmethod
    def get_default_provider(cls) -> str:
        """Return the default provider."""
        return cls._default_provider

    @classmethod
    def get_default_organizer(cls) -> str:
        """Return the default organizer."""
        return cls._default_organizer

    def process(self) -> Iterable[Maintenance]:
        """Method that returns a list of Maintenance objects."""
        raise NotImplementedError

    @staticmethod
    def dt2ts(date_time: datetime.datetime) -> int:
        """Converts a datetime object to UTC timestamp. Naive datetime will be considered UTC."""
        return calendar.timegm(date_time.utctimetuple())


class ICal(MaintenanceNotification):
    """Standard Notifications Parser based on ICal notifications.

    Reference: https://tools.ietf.org/html/draft-gunter-calext-maintenance-notifications-00
    """

    provider_type: str = "ical"

    # Internal placeholder for parser customization
    _default_provider = "ical"

    _data_type = "text/calendar"

    def process(self) -> Iterable[Maintenance]:
        """Method that returns a list of Maintenance objects."""
        result = []

        # iCalendar data sometimes comes encoded with base64
        # TODO: add a test case
        try:
            gcal = Calendar.from_ical(base64.b64decode(self.raw))
        except ValueError:
            gcal = Calendar.from_ical(self.raw)

        if not gcal:
            raise ParsingError("Not a valid iCalendar data received")

        try:
            gcal = Calendar.from_ical(self.raw)
            for component in gcal.walk():
                if component.name == "VEVENT":
                    organizer = (
                        str(component.get("ORGANIZER")) if component.get("ORGANIZER") else self._default_organizer
                    )
                    provider = (
                        str(component.get("X-MAINTNOTE-PROVIDER"))
                        if component.get("X-MAINTNOTE-PROVIDER")
                        else self._default_provider
                    )

                    data = {
                        "circuits": [],
                        "provider": provider,
                        "account": str(component.get("X-MAINTNOTE-ACCOUNT")),
                        "maintenance_id": str(component.get("X-MAINTNOTE-MAINTENANCE-ID")),
                        "status": Status(component.get("X-MAINTNOTE-STATUS")),
                        "start": round(component.get("DTSTART").dt.timestamp()),
                        "end": round(component.get("DTEND").dt.timestamp()),
                        "stamp": round(component.get("DTSTAMP").dt.timestamp()),
                        "summary": str(component.get("SUMMARY")),
                        "organizer": organizer,
                        "uid": str(component.get("UID")),
                        "sequence": int(component.get("SEQUENCE")),
                    }
                    # In a VEVENT sometimes there are mutliple object ID with custom impacts
                    circuits = component.get("X-MAINTNOTE-OBJECT-ID")
                    if isinstance(circuits, list):
                        data["circuits"] = [
                            CircuitImpact(
                                circuit_id=str(object),
                                impact=Impact(
                                    object.params.get("X-MAINTNOTE-OBJECT-IMPACT", component.get("X-MAINTNOTE-IMPACT"))
                                ),
                            )
                            for object in component.get("X-MAINTNOTE-OBJECT-ID")
                        ]
                    else:
                        data["circuits"] = [
                            CircuitImpact(circuit_id=circuits, impact=Impact(component.get("X-MAINTNOTE-IMPACT")),)
                        ]
                    result.append(Maintenance(**data))

        except ValidationError as exc:
            raise MissingMandatoryFields from exc

        except Exception as exc:
            raise ParsingError from exc

        return result


class Html(MaintenanceNotification):
    """Html parser."""

    _data_type = "text/html"

    def process(self) -> Iterable[Maintenance]:
        """Execute parsing."""
        result = []

        data_base: Dict[str, Union[int, str, Iterable]] = {
            "provider": self._default_provider,
            "organizer": self._default_organizer,
        }
        try:
            soup = bs4.BeautifulSoup(quopri.decodestring(self.raw), features="lxml")

            # Even we have not noticed any HTML notification with more than one maintenance yet, we define the
            # return of `parse_html` as an Iterable object to accommodate this potential case.
            for data in self.parse_html(soup, data_base):
                result.append(Maintenance(**data))

            return result

        except ValidationError as exc:
            raise MissingMandatoryFields from exc

    def parse_html(self, soup: ResultSet, data_base: Dict) -> Iterable[Union[Mapping[str, Union[str, int, Dict]]]]:
        """Custom HTML parsing."""
        raise NotImplementedError

    @staticmethod
    def clean_line(line):
        """Clean up of undesired characters from Html."""
        try:
            line = line.text.strip()
        except AttributeError:
            line = line.strip()
        # TODO: below may not be needed if we use `quopri.decodestring()` on the initial email file?
        return line.replace("=C2", "").replace("=A0", "").replace("\r", "").replace("=", "").replace("\n", "")
