"""Definition of Provider class as the entry point to the library."""
from typing import Iterable, Type

from pydantic import BaseModel

from circuit_maintenance_parser.output import Maintenance

from circuit_maintenance_parser.parser import Parser, ICal
from circuit_maintenance_parser.errors import ParsingError

from circuit_maintenance_parser.parsers.lumen import ParserLumenHtml1
from circuit_maintenance_parser.parsers.megaport import ParserMegaportHtml1
from circuit_maintenance_parser.parsers.telstra import ParserTelstraHtml1
from circuit_maintenance_parser.parsers.zayo import ParserZayoHtml1


class GenericProvider(BaseModel):
    """Base class for the Providers Parsers.

    This is the base class that is created for a Circuit Maintenance Parser

    Attributes:
        raw: Raw notification message (bytes)
        provider_type: Identifier of the provider of the notification
        sender: Identifier of the source of the notification (default "")
        subject: Subject of the notification (default "")
        source: Identifier of the source where this notification was obtained (default "")

    Examples:
        >>> GenericProvider(
        ...     raw=b"raw_message",
        ... )
        GenericProvider(raw=b'raw_message', sender='', subject='', source='')
    """

    # _parser_classes contain the Parser Classes that will be tried, in a specific order
    _parser_classes: Iterable[Type[Parser]] = [ICal]

    # Default values for parsing notifications
    _default_organizer: str = "unknown"

    raw: bytes
    sender: str = ""
    subject: str = ""
    source: str = ""

    @classmethod
    def get_default_organizer(cls) -> str:
        """Return the default organizer."""
        return cls._default_organizer

    @classmethod
    def get_provider_type(cls) -> str:
        """Return the Provider Type."""
        return cls.__name__.lower()

    @classmethod
    def get_data_types(cls) -> Iterable[str]:
        """Return the Provider Types."""
        return {parser_class.get_data_type() for parser_class in cls._parser_classes}

    def process(self) -> Iterable[Maintenance]:
        """Method that returns a list of Maintenance objects."""
        for parser_class in self._parser_classes:
            try:
                parser = parser_class(
                    raw=self.raw, provider_type=self.get_provider_type(), default_organizer=self._default_organizer,
                )
                return parser.process()
            except ParsingError:  # pylint: disable=broad-except
                continue
        raise ParsingError("None of the parsers was able to parse the notification")


####################
# PROVIDER PARSERS #
####################


class EUNetworks(GenericProvider):
    """EUNetworks provider custom class."""

    _default_organizer = "noc@eunetworks.com"


class Lumen(GenericProvider):
    """Lumen provider custom class."""

    _parser_classes: Iterable[Type[Parser]] = [ICal, ParserLumenHtml1]
    _default_organizer = "smc@lumen.com"


class Megaport(GenericProvider):
    """Megaport provider custom class."""

    _parser_classes: Iterable[Type[Parser]] = [ICal, ParserMegaportHtml1]
    _default_organizer = "support@megaport.com"


class NTT(GenericProvider):
    """NTT provider custom class."""

    _default_organizer = "noc@us.ntt.net"


class PacketFabric(GenericProvider):
    """PacketFabric provider custom class."""

    _default_organizer = "support@packetfabric.com"


class Telstra(GenericProvider):
    """Telstra provider custom class."""

    _parser_classes: Iterable[Type[Parser]] = [ICal, ParserTelstraHtml1]
    _default_organizer = "gpen@team.telstra.com"


class Zayo(GenericProvider):
    """Zayo provider custom class."""

    _parser_classes: Iterable[Type[Parser]] = [ICal, ParserZayoHtml1]
    _default_organizer = "mr@zayo.com"
