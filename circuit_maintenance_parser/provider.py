"""Definition of Provider class as the entry point to the library."""
import logging
import re
import traceback

from typing import Iterable, List, Dict

from pydantic import BaseModel

from circuit_maintenance_parser.utils import rgetattr

from circuit_maintenance_parser.output import Maintenance
from circuit_maintenance_parser.data import NotificationData
from circuit_maintenance_parser.parser import ICal, EmailDateParser
from circuit_maintenance_parser.errors import ProcessorError, ProviderError
from circuit_maintenance_parser.processor import CombinedProcessor, SimpleProcessor, GenericProcessor
from circuit_maintenance_parser.constants import EMAIL_HEADER_SUBJECT

from circuit_maintenance_parser.parsers.aquacomms import HtmlParserAquaComms1, SubjectParserAquaComms1
from circuit_maintenance_parser.parsers.aws import SubjectParserAWS1, TextParserAWS1
from circuit_maintenance_parser.parsers.cogent import HtmlParserCogent1
from circuit_maintenance_parser.parsers.colt import ICalParserColt1, CsvParserColt1
from circuit_maintenance_parser.parsers.gtt import HtmlParserGTT1
from circuit_maintenance_parser.parsers.hgc import HtmlParserHGC1, HtmlParserHGC2, SubjectParserHGC1
from circuit_maintenance_parser.parsers.lumen import HtmlParserLumen1
from circuit_maintenance_parser.parsers.megaport import HtmlParserMegaport1
from circuit_maintenance_parser.parsers.momentum import HtmlParserMomentum1, SubjectParserMomentum1
from circuit_maintenance_parser.parsers.seaborn import (
    HtmlParserSeaborn1,
    HtmlParserSeaborn2,
    SubjectParserSeaborn1,
    SubjectParserSeaborn2,
)
from circuit_maintenance_parser.parsers.sparkle import HtmlParserSparkle1
from circuit_maintenance_parser.parsers.telstra import HtmlParserTelstra1
from circuit_maintenance_parser.parsers.turkcell import HtmlParserTurkcell1
from circuit_maintenance_parser.parsers.verizon import HtmlParserVerizon1
from circuit_maintenance_parser.parsers.zayo import HtmlParserZayo1


logger = logging.getLogger(__name__)


class GenericProvider(BaseModel):
    """Base class for the Providers.

    This is the entry object to the library and it offers the `get_maintenances` method to process notifications.

    Attributes:
        _processors (optional): Defines a list of `_processors` that will be evaluated in order to get `Maintenances`.
            Each `Processor` implementation has a custom logic to combine the parsed data and a list of the `Parsers`
            that will be used. Default: `[SimpleProcessor(data_parsers=[ICal])]`.
        _default_organizer (optional): Defines a default `organizer`, an email address, to be used to create a
            `Maintenance` in absence of the information in the original notification.
        _include_filter (optional): Dictionary that defines matching regex per data type to take a notification into
            account.
        _exclude_filter (optional): Dictionary that defines matching regex per data type to NOT take a notification
            into account.

    Notes:
        - If a notification matches both the `_include_filter` and `_exclude_filter`, the exclusion takes precedence and
          the notification will be filtered out.

    Examples:
        >>> GenericProvider()
        GenericProvider()
    """

    _processors: List[GenericProcessor] = [SimpleProcessor(data_parsers=[ICal])]
    _default_organizer: str = "unknown"

    _include_filter: Dict[str, List[str]] = {}
    _exclude_filter: Dict[str, List[str]] = {}

    def include_filter_check(self, data: NotificationData) -> bool:
        """If `_include_filter` is defined, it verifies that the matching criteria is met."""
        if self._include_filter:
            return self.filter_check(self._include_filter, data, "include")
        return True

    def exclude_filter_check(self, data: NotificationData) -> bool:
        """If `_exclude_filter` is defined, it verifies that the matching criteria is met."""
        if self._exclude_filter:
            return self.filter_check(self._exclude_filter, data, "exclude")
        return False

    @staticmethod
    def filter_check(filter_dict: Dict, data: NotificationData, filter_type: str) -> bool:
        """Generic filter check."""
        data_part_content = None
        for data_part in data.data_parts:
            filter_data_type = data_part.type
            if filter_data_type not in filter_dict:
                continue

            data_part_content = data_part.content.decode()
            if any(re.search(filter_re, data_part_content) for filter_re in filter_dict[filter_data_type]):
                logger.debug("Matching %s filter expression for %s.", filter_type, data_part_content)
                return True

        if data_part_content:
            logger.warning("Not matching any %s filter expression for %s.", filter_type, data_part_content)
        else:
            logger.warning(
                "Not matching any %s filter expression because the notification doesn't contain the expected data_types: %s",
                filter_type,
                ", ".join(filter_dict.keys()),
            )
        return False

    def get_maintenances(self, data: NotificationData) -> Iterable[Maintenance]:
        """Main entry method that will use the defined `_processors` in order to extract the `Maintenances` from data."""
        provider_name = self.__class__.__name__
        error_message = ""
        related_exceptions = []

        if self.exclude_filter_check(data) or not self.include_filter_check(data):
            logger.debug("Skipping notification %s due filtering policy for %s.", data, self.__class__.__name__)
            return []

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


class AquaComms(GenericProvider):
    """AquaComms provider custom class."""

    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserAquaComms1, SubjectParserAquaComms1]),
    ]
    _default_organizer = "tickets@aquacomms.com"


class AWS(GenericProvider):
    """AWS provider custom class."""

    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[EmailDateParser, TextParserAWS1, SubjectParserAWS1]),
    ]
    _default_organizer = "aws-account-notifications@amazon.com"


class Cogent(GenericProvider):
    """Cogent provider custom class."""

    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserCogent1]),
    ]
    _default_organizer = "support@cogentco.com"


class Colt(GenericProvider):
    """Cogent provider custom class."""

    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[ICalParserColt1, CsvParserColt1]),
    ]
    _default_organizer = "PlannedWorks@colt.net"


class EUNetworks(GenericProvider):
    """EUNetworks provider custom class."""

    _default_organizer = "noc@eunetworks.com"


class GTT(GenericProvider):
    """GTT provider custom class."""

    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserGTT1]),
    ]
    _default_organizer = "InfraCo.CM@gttcorp.org"


class HGC(GenericProvider):
    """HGC provider custom class."""

    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserHGC1, SubjectParserHGC1]),
        CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserHGC2, SubjectParserHGC1]),
    ]
    _default_organizer = "HGCINOCPW@hgc.com.hk"


class Lumen(GenericProvider):
    """Lumen provider custom class."""

    _include_filter = {EMAIL_HEADER_SUBJECT: ["Scheduled Maintenance"]}

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


class Momentum(GenericProvider):
    """Momentum provider custom class."""

    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserMomentum1, SubjectParserMomentum1]),
    ]
    _default_organizer = "maintenance@momentumtelecom.com"


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


class Sparkle(GenericProvider):
    """Sparkle provider custom class."""

    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[HtmlParserSparkle1, EmailDateParser]),
    ]
    _default_organizer = "TISAmericaNOC@tisparkle.com"


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
