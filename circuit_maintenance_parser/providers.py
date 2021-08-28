"""Definition of Provider class as the entry point to the library."""
import logging
import traceback

from typing import Iterable

from pydantic import BaseModel, Extra

from circuit_maintenance_parser.output import Maintenance
from circuit_maintenance_parser.data import NotificationData
from circuit_maintenance_parser.parser import ICal
from circuit_maintenance_parser.errors import ProcessorError, ProviderError
from circuit_maintenance_parser.processor import SimpleProcessor, GenericProcessor

from circuit_maintenance_parser.parsers.cogent import HtmlParserCogent1
from circuit_maintenance_parser.parsers.gtt import HtmlParserGTT1
from circuit_maintenance_parser.parsers.lumen import HtmlParserLumen1
from circuit_maintenance_parser.parsers.megaport import HtmlParserMegaport1
from circuit_maintenance_parser.parsers.telstra import HtmlParserTelstra1
from circuit_maintenance_parser.parsers.verizon import HtmlParserVerizon1
from circuit_maintenance_parser.parsers.zayo import HtmlParserZayo1


logger = logging.getLogger(__name__)


class GenericProvider(BaseModel, extra=Extra.forbid):
    """Base class for the Providers.

    This is the base class that is created for a Circuit Maintenance Parser

    Examples:
        >>> GenericProvider()
        GenericProvider()
    """

    _processors: Iterable[GenericProcessor] = [SimpleProcessor(data_parsers=[ICal])]

    # Default values for parsing notifications
    _default_organizer: str = "unknown"

    def process_notification(self, data: NotificationData) -> Iterable[Maintenance]:
        """Method that will get all the data parts from `data` and using the `_processors` will create Maintenances."""
        provider_name = self.__class__.__name__
        error_message = ""
        related_exceptions = []
        extended_data = {"organizer": self.get_default_organizer(), "provider": self.get_provider_type()}

        for processor in self._processors:
            try:
                return processor.run(data, extended_data)
            except ProcessorError as exc:
                processor_name = processor.__class__.__name__
                logger.debug(
                    "Processor %s for provider %s was not successful:\n%s",
                    processor_name,
                    provider_name,
                    traceback.format_exc(),
                )
                error_message += f"- Processor {processor_name} from {provider_name} failed due to: {exc.__cause__}\n"
                related_exceptions.append(exc)
                continue

        raise ProviderError(
            (
                f"Not enough information available to create Maintenance notification for {provider_name} .\n"
                f"Details:\n{error_message}"
            ),
            related_exceptions=related_exceptions,
        )

    @classmethod
    def get_default_organizer(cls) -> str:
        """Return the default organizer."""
        return cls._default_organizer

    @classmethod
    def get_provider_type(cls) -> str:
        """Return the Provider Type."""
        return cls.__name__.lower()


####################
# PROVIDERS        #
####################


class Cogent(GenericProvider):
    """EUNetworks provider custom class."""

    _processors: Iterable[GenericProcessor] = [
        SimpleProcessor(data_parsers=[HtmlParserCogent1]),
    ]
    _default_organizer = "support@cogentco.com"


class EUNetworks(GenericProvider):
    """EUNetworks provider custom class."""

    _default_organizer = "noc@eunetworks.com"


class GTT(GenericProvider):
    """GTT provider custom class."""

    _processors: Iterable[GenericProcessor] = [
        SimpleProcessor(data_parsers=[HtmlParserGTT1]),
    ]
    _default_organizer = "InfraCo.CM@gttcorp.org"


class Lumen(GenericProvider):
    """Lumen provider custom class."""

    _processors: Iterable[GenericProcessor] = [
        SimpleProcessor(data_parsers=[HtmlParserLumen1]),
    ]
    _default_organizer = "smc@lumen.com"


class Megaport(GenericProvider):
    """Megaport provider custom class."""

    _processors: Iterable[GenericProcessor] = [
        SimpleProcessor(data_parsers=[HtmlParserMegaport1]),
    ]
    _default_organizer = "support@megaport.com"


class NTT(GenericProvider):
    """NTT provider custom class."""

    _default_organizer = "noc@us.ntt.net"


class PacketFabric(GenericProvider):
    """PacketFabric provider custom class."""

    _default_organizer = "support@packetfabric.com"


class Telia(GenericProvider):
    """Telia provider custom class."""

    _default_organizer = "carrier-csc@teliacompany.com"


class Telstra(GenericProvider):
    """Telstra provider custom class."""

    _processors: Iterable[GenericProcessor] = [
        SimpleProcessor(data_parsers=[ICal]),
        SimpleProcessor(data_parsers=[HtmlParserTelstra1]),
    ]
    _default_organizer = "gpen@team.telstra.com"


class Verizon(GenericProvider):
    """Verizon provider custom class."""

    _processors: Iterable[GenericProcessor] = [
        SimpleProcessor(data_parsers=[HtmlParserVerizon1]),
    ]
    _default_organizer = "NO-REPLY-sched-maint@EMEA.verizonbusiness.com"


class Zayo(GenericProvider):
    """Zayo provider custom class."""

    _processors: Iterable[GenericProcessor] = [
        SimpleProcessor(data_parsers=[HtmlParserZayo1]),
    ]
    _default_organizer = "mr@zayo.com"
