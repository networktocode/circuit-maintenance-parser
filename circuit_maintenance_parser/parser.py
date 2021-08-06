"""Definition of Mainentance Notification base classes."""
import logging
import base64
import calendar
import datetime
import quopri
from typing import Iterable, Union, Dict, Mapping

import bs4  # type: ignore
from bs4.element import ResultSet  # type: ignore

from pydantic import BaseModel, ValidationError, Extra
from icalendar import Calendar  # type: ignore

from circuit_maintenance_parser.errors import ParsingError, MissingMandatoryFields
from circuit_maintenance_parser.output import Maintenance, Status, Impact, CircuitImpact

# pylint: disable=no-member

logger = logging.getLogger(__name__)


class Parser(BaseModel, extra=Extra.forbid):
    """Parser class.

    Attributes:
        raw: Raw notification message (bytes)
        default_provider: Identifier of the provider of the notification
        default_organizer: Identifier of the organizer of the notification

    Examples:
        >>> Parser(
        ...     raw=b"raw_message",
        ...     default_provider="ntt",
        ...     default_organizer="noc@us.ntt.net"
        ... )
        Parser(raw=b'raw_message', default_provider='ntt', default_organizer='noc@us.ntt.net')

        >>> Parser(raw=b"raw_message")
        Parser(raw=b'raw_message', default_provider='unknown', default_organizer='unknown')

        >>> Parser(b"raw_message")
        Traceback (most recent call last):
        ...
        TypeError: __init__() takes exactly 1 positional argument (2 given)

    """

    raw: bytes
    default_provider: str = "unknown"
    default_organizer: str = "unknown"

    # Data Type used as payload
    _data_type = "text/plain"

    @classmethod
    def get_data_type(cls) -> str:
        """Return the expected data type."""
        return cls._data_type

    def process(self) -> Iterable[Maintenance]:
        """Method that returns a list of Maintenance objects."""
        raise NotImplementedError

    @staticmethod
    def dt2ts(date_time: datetime.datetime) -> int:
        """Converts a datetime object to UTC timestamp. Naive datetime will be considered UTC."""
        return calendar.timegm(date_time.utctimetuple())


class ICal(Parser):
    """Standard Notifications Parser based on ICal notifications.

    Reference: https://tools.ietf.org/html/draft-gunter-calext-maintenance-notifications-00
    """

    _data_type = "text/calendar"

    def process(self) -> Iterable[Maintenance]:
        """Method that returns a list of Maintenance objects."""
        result = []

        # iCalendar data sometimes comes encoded with base64
        # TODO: add a test case
        try:
            gcal = Calendar.from_ical(base64.b64decode(self.raw))
        except ValueError:
            try:
                gcal = Calendar.from_ical(self.raw)
            except ValueError as exc:
                raise ParsingError from exc

        if not gcal:
            raise ParsingError("Not a valid iCalendar data received")

        try:
            gcal = Calendar.from_ical(self.raw)
            for component in gcal.walk():
                if component.name == "VEVENT":
                    organizer = (
                        str(component.get("ORGANIZER")) if component.get("ORGANIZER") else self.default_organizer
                    )
                    provider = (
                        str(component.get("X-MAINTNOTE-PROVIDER"))
                        if component.get("X-MAINTNOTE-PROVIDER")
                        else self.default_provider
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
            raise MissingMandatoryFields(exc)  # pylint: disable=W0707

        except Exception as exc:
            raise ParsingError(exc)  # pylint: disable=W0707

        logger.debug("Successful parsing for %s", self.__class__.__name__)

        return result


class Html(Parser):
    """Html parser."""

    _data_type = "text/html"

    def process(self) -> Iterable[Maintenance]:
        """Execute parsing."""
        result = []

        data_base: Dict[str, Union[int, str, Iterable]] = {
            "provider": self.default_provider,
            "organizer": self.default_organizer,
        }
        try:
            soup = bs4.BeautifulSoup(quopri.decodestring(self.raw), features="lxml")

            # Even we have not noticed any HTML notification with more than one maintenance yet, we define the
            # return of `parse_html` as an Iterable object to accommodate this potential case.
            for data in self.parse_html(soup, data_base):
                result.append(Maintenance(**data))

            logger.debug("Successful parsing for %s", self.__class__.__name__)

            return result

        except ValidationError as exc:
            raise MissingMandatoryFields(exc)  # pylint: disable=W0707

        except Exception as exc:
            raise ParsingError(exc)  # pylint: disable=W0707

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
