"""Definition of Provider class as the entry point to the library."""
import logging
from typing import Iterable, Type

from pydantic import BaseModel, Extra

from circuit_maintenance_parser.output import Maintenance

from circuit_maintenance_parser.parser import Parser, ICal
from circuit_maintenance_parser.errors import ParsingError, MissingMandatoryFields

from circuit_maintenance_parser.parsers.cogent import HtmlParserCogent1
from circuit_maintenance_parser.parsers.lumen import HtmlParserLumen1
from circuit_maintenance_parser.parsers.megaport import HtmlParserMegaport1
from circuit_maintenance_parser.parsers.telstra import HtmlParserTelstra1
from circuit_maintenance_parser.parsers.zayo import HtmlParserZayo1


logger = logging.getLogger(__name__)


class GenericProvider(BaseModel, extra=Extra.forbid):
    """Base class for the Providers Parsers.

    This is the base class that is created for a Circuit Maintenance Parser

    Attributes:
        raw: Raw notification message (bytes)

    Examples:
        >>> GenericProvider(
        ...     raw=b"raw_message",
        ... )
        GenericProvider(raw=b'raw_message')
    """

    # _parser_classes contain the Parser Classes that will be tried, in a specific order
    _parser_classes: Iterable[Type[Parser]] = [ICal]

    # Default values for parsing notifications
    _default_organizer: str = "unknown"

    raw: bytes

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

    def process(self, data_type: str = "") -> Iterable[Maintenance]:
        """Method that returns a list of Maintenance objects.

        Attributes:
            data_type: Hint to limit the parsing to specific data types. (default "")

        """
        for parser_class in self._parser_classes:
            try:
                parser = parser_class(
                    raw=self.raw,
                    default_provider=self.get_provider_type(),
                    default_organizer=self.get_default_organizer(),
                )
                if data_type and data_type == parser.get_data_type() or not data_type:
                    return parser.process()
            except (ParsingError, MissingMandatoryFields):
                logger.debug(
                    "Parser %s for provider %s was not successful", parser_class.__name__, self.__class__.__name__
                )
                continue
        raise ParsingError("None of the parsers was able to parse the notification")


####################
# PROVIDER PARSERS #
####################


class Cogent(GenericProvider):
    """EUNetworks provider custom class."""

    _parser_classes: Iterable[Type[Parser]] = [HtmlParserCogent1]
    _default_organizer = "support@cogentco.com"


class EUNetworks(GenericProvider):
    """EUNetworks provider custom class."""

    _default_organizer = "noc@eunetworks.com"


class Lumen(GenericProvider):
    """Lumen provider custom class."""

    _parser_classes: Iterable[Type[Parser]] = [HtmlParserLumen1]
    _default_organizer = "smc@lumen.com"


class Megaport(GenericProvider):
    """Megaport provider custom class."""

    _parser_classes: Iterable[Type[Parser]] = [HtmlParserMegaport1]
    _default_organizer = "support@megaport.com"


class NTT(GenericProvider):
    """NTT provider custom class."""

    _default_organizer = "noc@us.ntt.net"


class PacketFabric(GenericProvider):
    """PacketFabric provider custom class."""

    _default_organizer = "support@packetfabric.com"


class Telstra(GenericProvider):
    """Telstra provider custom class."""

    _parser_classes: Iterable[Type[Parser]] = [ICal, HtmlParserTelstra1]
    _default_organizer = "gpen@team.telstra.com"


class Zayo(GenericProvider):
    """Zayo provider custom class."""

    _parser_classes: Iterable[Type[Parser]] = [HtmlParserZayo1]
    _default_organizer = "mr@zayo.com"
