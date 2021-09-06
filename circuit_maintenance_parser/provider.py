"""Definition of Provider class as the entry point to the library."""
import logging
import traceback

from typing import Iterable, List

from pydantic import BaseModel, Extra

from circuit_maintenance_parser.utils import rgetattr

from circuit_maintenance_parser.output import Maintenance
from circuit_maintenance_parser.data import NotificationData
from circuit_maintenance_parser.parser import ICal, EmailDateParser
from circuit_maintenance_parser.errors import ProcessorError, ProviderError
from circuit_maintenance_parser.processor import CombinedProcessor, SimpleProcessor, GenericProcessor

from circuit_maintenance_parser.parsers.cogent import HtmlParserCogent1
from circuit_maintenance_parser.parsers.gtt import HtmlParserGTT1
from circuit_maintenance_parser.parsers.lumen import HtmlParserLumen1
from circuit_maintenance_parser.parsers.megaport import HtmlParserMegaport1
from circuit_maintenance_parser.parsers.seaborn import (
    HtmlParserSeaborn1,
    HtmlParserSeaborn2,
    SubjectParserSeaborn1,
    SubjectParserSeaborn2,
)
from circuit_maintenance_parser.parsers.telstra import HtmlParserTelstra1
from circuit_maintenance_parser.parsers.turkcell import HtmlParserTurkcell1
from circuit_maintenance_parser.parsers.verizon import HtmlParserVerizon1
from circuit_maintenance_parser.parsers.zayo import HtmlParserZayo1


logger = logging.getLogger(__name__)


class GenericProvider(BaseModel, extra=Extra.forbid):
    """Base class for the Providers.

    This is the entry object to the library and it offers the `get_maintenances` method to process notifications.

    Attributes:
        provider_type (optional): string to define the provider type.
        organizer (optional): email address of the provider.
        _processors (optional): Defines a list of `_processors` that will be evaluated in order to get `Maintenances`.
            Each `Processor` implementation has a custom logic to combine the parsed data and a list of the `Parsers`
            that will be used. Default: `[SimpleProcessor(data_parsers=[ICal])]`.
        _default_organizer (optional): Defines a default `organizer`, an email address, to be used to create a
            `Maintenance` in absence of the information in the original notification.

    Examples:
        >>> GenericProvider()
        GenericProvider(provider_type='', organizer='')
    """

    provider_type: str = ""
    organizer: str = ""

    _processors: List[GenericProcessor] = [SimpleProcessor(data_parsers=[ICal])]
    _default_organizer: str = ""

    def __init__(self, **data):
        """Init default internal attributes."""
        super().__init__(**data)

        self.organizer = data.get("organizer", "")
        self.provider_type = data.get("provider_type", "")

    def get_maintenances(self, data: NotificationData) -> Iterable[Maintenance]:
        """Main entry method that will use the defined `_processors` in order to extract the `Maintenances` from data."""
        provider_name = self.__class__.__name__
        error_message = ""
        related_exceptions = []

        for processor in self._processors:
            try:
                return processor.process(data, self.get_extended_data())
            except ProcessorError as exc:
                process_error_message = (
                    f"- Processor {processor.__class__.__name__} from {provider_name} failed due to: %s\n"
                )
                logger.debug(process_error_message, traceback.format_exc())

                related_exc = rgetattr(exc, "__cause__")
                error_message += process_error_message % related_exc
                related_exceptions.append(exc)
                continue

        raise ProviderError(
            (f"Failed creating Maintenance notification for {provider_name}.\nDetails:\n{error_message}"),
            related_exceptions=related_exceptions,
        )

    def get_extended_data(self):
        """Return the default data used to extend processed notification data.

        It's used when the data is not available in the notification itself
        """
        return {"organizer": self.get_default_organizer(), "provider": self.get_provider_type()}

    def get_default_organizer(self) -> str:
        """Expose default_organizer."""
        return self.organizer if self.organizer else self._default_organizer

    def get_provider_type(self) -> str:
        """Return the Provider Type."""
        return self.provider_type if self.provider_type else self.__class__.__name__.lower()


####################
# PROVIDERS        #
####################


class Cogent(GenericProvider):
    """Cogent provider custom class."""

    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserCogent1]),
    ]
    _default_organizer = "support@cogentco.com"


class EUNetworks(GenericProvider):
    """EUNetworks provider custom class."""

    _default_organizer = "noc@eunetworks.com"


class GTT(GenericProvider):
    """GTT provider custom class."""

    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserGTT1]),
    ]
    _default_organizer = "InfraCo.CM@gttcorp.org"


class Lumen(GenericProvider):
    """Lumen provider custom class."""

    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserLumen1]),
    ]
    _default_organizer = "smc@lumen.com"


class Megaport(GenericProvider):
    """Megaport provider custom class."""

    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserMegaport1]),
    ]
    _default_organizer = "support@megaport.com"


class NTT(GenericProvider):
    """NTT provider custom class."""

    _default_organizer = "noc@us.ntt.net"


class PacketFabric(GenericProvider):
    """PacketFabric provider custom class."""

    _default_organizer = "support@packetfabric.com"


class Seaborn(GenericProvider):
    """Seaborn provider custom class."""

    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserSeaborn1, SubjectParserSeaborn1]),
        CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserSeaborn2, SubjectParserSeaborn2]),
    ]
    _default_organizer = "inoc@superonline.net"


class Telia(GenericProvider):
    """Telia provider custom class."""

    _default_organizer = "carrier-csc@teliacompany.com"


class Telstra(GenericProvider):
    """Telstra provider custom class."""

    _processors: List[GenericProcessor] = [
        SimpleProcessor(data_parsers=[ICal]),
        CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserTelstra1]),
    ]
    _default_organizer = "gpen@team.telstra.com"


class Turkcell(GenericProvider):
    """Turkcell provider custom class."""

    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserTurkcell1]),
    ]
    _default_organizer = "inoc@superonline.net"


class Verizon(GenericProvider):
    """Verizon provider custom class."""

    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserVerizon1]),
    ]
    _default_organizer = "NO-REPLY-sched-maint@EMEA.verizonbusiness.com"


class Zayo(GenericProvider):
    """Zayo provider custom class."""

    _processors: List[GenericProcessor] = [
        SimpleProcessor(data_parsers=[HtmlParserZayo1]),
    ]
    _default_organizer = "mr@zayo.com"
