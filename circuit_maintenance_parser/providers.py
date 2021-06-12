"""Definition of Provider class as the entry point to the library."""
from typing import Iterable, Type

from pydantic import BaseModel

from circuit_maintenance_parser.output import Maintenance

from circuit_maintenance_parser.parser import MaintenanceNotification, ICal
from circuit_maintenance_parser.errors import ParsingError, MissingMandatoryFields

from circuit_maintenance_parser.parsers.lumen import ParserLumenHtml1
from circuit_maintenance_parser.parsers.megaport import ParserMegaportHtml1
from circuit_maintenance_parser.parsers.telstra import ParserTelstraHtml1
from circuit_maintenance_parser.parsers.zayo import ParserZayoHtml1


class GenericProvider(BaseModel):
    """Base class for the custom Providers."""

    # _parser_classes contain the Parser Classes that will be tried, in a specific order
    _parser_classes: Iterable[Type[MaintenanceNotification]] = [ICal]
    # Default values for parsing notifications
    _default_organizer: str = "unknown"
    _provider_type: str = "unknown"

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
        data_types = set()
        for parser_class in cls._parser_classes:
            data_types.add(parser_class.get_data_type())
        return data_types

    def process(self) -> Iterable[Maintenance]:
        """Method that returns a list of Maintenance objects."""
        for parser_class in self._parser_classes:
            try:
                parser = parser_class(
                    raw=self.raw, provider_type=self._provider_type, default_organizer=self._default_organizer,
                )
                return parser.process()
            except (ParsingError, MissingMandatoryFields):
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

    _parser_classes: Iterable[Type[MaintenanceNotification]] = [ICal, ParserLumenHtml1]
    _default_organizer = "smc@lumen.com"


class Megaport(GenericProvider):
    """Megaport provider custom class."""

    _parser_classes: Iterable[Type[MaintenanceNotification]] = [ICal, ParserMegaportHtml1]
    _default_organizer = "support@megaport.com"


class NTT(GenericProvider):
    """NTT provider custom class."""

    _default_organizer = "noc@us.ntt.net"


class PacketFabric(GenericProvider):
    """PacketFabric provider custom class."""

    _default_organizer = "support@packetfabric.com"


class Telstra(GenericProvider):
    """Telstra provider custom class."""

    _parser_classes: Iterable[Type[MaintenanceNotification]] = [ICal, ParserTelstraHtml1]
    _default_organizer = "gpen@team.telstra.com"


class Zayo(GenericProvider):
    """Zayo provider custom class."""

    _parser_classes: Iterable[Type[MaintenanceNotification]] = [ICal, ParserZayoHtml1]
    _default_organizer = "mr@zayo.com"
