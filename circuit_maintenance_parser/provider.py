"""Definition of Provider class as the entry point to the library."""
import logging
import traceback

from typing import Iterable, List

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

    This is the entry object to the library and it offers the `get_maintenances` method to process notifications.

    Attributes:
        processors (optional): Defines a list of `Processors` that will be evaluated in order to get `Maintenances`.
            Each `Processor` implementation has a custom logic to combine the parsed data and a list of the `Parsers`
            that will be used. Default: `[SimpleProcessor(data_parsers=[ICal])]`.
        default_organizer (optional): Defines a default `organizer`, an email address, to be used to create a
            `Maintenance` in absence of the information in the original notification.

    Examples:
        >>> GenericProvider()
        GenericProvider(processors=[SimpleProcessor(data_parsers=[<class 'circuit_maintenance_parser.parser.ICal'>], extended_data={})])
    """

    processors: List[GenericProcessor] = [SimpleProcessor(data_parsers=[ICal])]
    _default_organizer: str = "unknown"

    def get_maintenances(self, data: NotificationData) -> Iterable[Maintenance]:
        """Main entry method that will use the defined `Processors` in order to extract the `Maintenances` from data."""
        provider_name = self.__class__.__name__
        error_message = ""
        related_exceptions = []

        for processor in self.processors:
            try:
                return processor.process(data, self.get_extended_data())
            except ProcessorError as exc:
                process_error_message = (
                    f"- Processor {processor.__class__.__name__} from {provider_name} failed due to: %s\n"
                )
                logger.debug(process_error_message, traceback.format_exc())
                error_message += process_error_message % exc.__cause__
                related_exceptions.append(exc)
                continue

        raise ProviderError(
            (f"Failed creating Maintenance notification for {provider_name} .\nDetails:\n{error_message}"),
            related_exceptions=related_exceptions,
        )

    @classmethod
    def get_default_organizer(cls):
        """Expose default_organizer as class attribute."""
        return cls._default_organizer

    @classmethod
    def get_extended_data(cls):
        """Return the default data used to extend processed notification data.

        It's used when the data is not available in the notification itself
        """
        return {"organizer": cls._default_organizer, "provider": cls.get_provider_type()}

    @classmethod
    def get_provider_type(cls) -> str:
        """Return the Provider Type."""
        return cls.__name__.lower()


####################
# PROVIDERS        #
####################


class Cogent(GenericProvider):
    """Cogent provider custom class."""

    processors: List[GenericProcessor] = [
        SimpleProcessor(data_parsers=[HtmlParserCogent1]),
    ]
    _default_organizer = "support@cogentco.com"


class EUNetworks(GenericProvider):
    """EUNetworks provider custom class."""

    _default_organizer = "noc@eunetworks.com"


class GTT(GenericProvider):
    """GTT provider custom class."""

    processors: List[GenericProcessor] = [
        SimpleProcessor(data_parsers=[HtmlParserGTT1]),
    ]
    _default_organizer = "InfraCo.CM@gttcorp.org"


class Lumen(GenericProvider):
    """Lumen provider custom class."""

    processors: List[GenericProcessor] = [
        SimpleProcessor(data_parsers=[HtmlParserLumen1]),
    ]
    _default_organizer = "smc@lumen.com"


class Megaport(GenericProvider):
    """Megaport provider custom class."""

    processors: List[GenericProcessor] = [
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

    processors: List[GenericProcessor] = [
        SimpleProcessor(data_parsers=[ICal]),
        SimpleProcessor(data_parsers=[HtmlParserTelstra1]),
    ]
    _default_organizer = "gpen@team.telstra.com"


class Verizon(GenericProvider):
    """Verizon provider custom class."""

    processors: List[GenericProcessor] = [
        SimpleProcessor(data_parsers=[HtmlParserVerizon1]),
    ]
    _default_organizer = "NO-REPLY-sched-maint@EMEA.verizonbusiness.com"


class Zayo(GenericProvider):
    """Zayo provider custom class."""

    processors: List[GenericProcessor] = [
        SimpleProcessor(data_parsers=[HtmlParserZayo1]),
    ]
    _default_organizer = "mr@zayo.com"
