"""Definition of Provider class as the entry point to the library."""

import logging
import os
import re
import traceback
from typing import Dict, Iterable, List

import chardet
from pydantic import BaseModel, PrivateAttr

from circuit_maintenance_parser.constants import EMAIL_HEADER_SUBJECT
from circuit_maintenance_parser.data import NotificationData
from circuit_maintenance_parser.errors import ProcessorError, ProviderError
from circuit_maintenance_parser.output import Maintenance
from circuit_maintenance_parser.parser import EmailDateParser, ICal

from circuit_maintenance_parser.parsers.apple import SubjectParserApple, TextParserApple
from circuit_maintenance_parser.parsers.aquacomms import HtmlParserAquaComms1, SubjectParserAquaComms1
from circuit_maintenance_parser.parsers.att import HtmlParserATT1, XlsxParserATT1
from circuit_maintenance_parser.parsers.aws import SubjectParserAWS1, TextParserAWS1
from circuit_maintenance_parser.parsers.bso import HtmlParserBSO1
from circuit_maintenance_parser.parsers.cogent import HtmlParserCogent1, SubjectParserCogent1, TextParserCogent1
from circuit_maintenance_parser.parsers.colt import CsvParserColt1, SubjectParserColt1, SubjectParserColt2
from circuit_maintenance_parser.parsers.crowncastle import HtmlParserCrownCastle1
from circuit_maintenance_parser.parsers.equinix import HtmlParserEquinix, SubjectParserEquinix
from circuit_maintenance_parser.parsers.globalcloudxchange import HtmlParserGcx1, SubjectParserGcx1
from circuit_maintenance_parser.parsers.google import HtmlParserGoogle1
from circuit_maintenance_parser.parsers.gtt import HtmlParserGTT1
from circuit_maintenance_parser.parsers.hgc import HtmlParserHGC1, HtmlParserHGC2, SubjectParserHGC1
from circuit_maintenance_parser.parsers.lumen import HtmlParserLumen1
from circuit_maintenance_parser.parsers.megaport import HtmlParserMegaport1
from circuit_maintenance_parser.parsers.momentum import HtmlParserMomentum1, SubjectParserMomentum1
from circuit_maintenance_parser.parsers.netflix import TextParserNetflix1
from circuit_maintenance_parser.parsers.openai import OpenAIParser
from circuit_maintenance_parser.parsers.pccw import HtmlParserPCCW, SubjectParserPCCW
from circuit_maintenance_parser.parsers.seaborn import (
    HtmlParserSeaborn1,
    HtmlParserSeaborn2,
    SubjectParserSeaborn1,
    SubjectParserSeaborn2,
)
from circuit_maintenance_parser.parsers.sparkle import HtmlParserSparkle1
from circuit_maintenance_parser.parsers.tata import HtmlParserTata, SubjectParserTata
from circuit_maintenance_parser.parsers.telstra import HtmlParserTelstra1, HtmlParserTelstra2
from circuit_maintenance_parser.parsers.turkcell import HtmlParserTurkcell1
from circuit_maintenance_parser.parsers.verizon import HtmlParserVerizon1
from circuit_maintenance_parser.parsers.windstream import HtmlParserWindstream1
from circuit_maintenance_parser.parsers.zayo import HtmlParserZayo1, SubjectParserZayo1
from circuit_maintenance_parser.processor import CombinedProcessor, GenericProcessor, SimpleProcessor
from circuit_maintenance_parser.utils import rgetattr

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

    _processors: List[GenericProcessor] = PrivateAttr([SimpleProcessor(data_parsers=[ICal])])
    _default_organizer: str = PrivateAttr("unknown")

    _include_filter: Dict[str, List[str]] = PrivateAttr({})
    _exclude_filter: Dict[str, List[str]] = PrivateAttr({})

    def include_filter_check(self, data: NotificationData) -> bool:
        """If `_include_filter` is defined, it verifies that the matching criteria is met."""
        if self.get_default_include_filters():
            return self.filter_check(self.get_default_include_filters(), data, "include")
        return True

    def exclude_filter_check(self, data: NotificationData) -> bool:
        """If `_exclude_filter` is defined, it verifies that the matching criteria is met."""
        if self.get_default_exclude_filters():
            return self.filter_check(self.get_default_exclude_filters(), data, "exclude")
        return False

    @staticmethod
    def filter_check(filter_dict: Dict, data: NotificationData, filter_type: str) -> bool:
        """Generic filter check."""
        data_part_content = None
        for data_part in data.data_parts:
            filter_data_type = data_part.type
            if filter_data_type not in filter_dict:
                continue

            data_part_encoding = chardet.detect(data_part.content).get("encoding", "utf-8")
            data_part_content = data_part.content.decode(data_part_encoding).replace("\r", "").replace("\n", "")
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

        if os.getenv("PARSER_OPENAI_API_KEY"):
            self._processors.append(CombinedProcessor(data_parsers=[EmailDateParser, OpenAIParser]))

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
    def get_default_organizer(cls) -> str:
        """Expose default_organizer as class attribute."""
        try:
            return cls._default_organizer.get_default()  # type: ignore
        except AttributeError:
            # TODO: This exception handling is required for Pydantic 1.x compatibility. To be removed when the dependency is deprecated.
            return cls()._default_organizer

    @classmethod
    def get_default_processors(cls) -> List[GenericProcessor]:
        """Expose default_processors as class attribute."""
        try:
            return cls._processors.get_default()  # type: ignore
        except AttributeError:
            # TODO: This exception handling is required for Pydantic 1.x compatibility. To be removed when the dependency is deprecated.
            return cls()._processors

    @classmethod
    def get_default_include_filters(cls) -> Dict[str, List[str]]:
        """Expose include_filter as class attribute."""
        try:
            return cls._include_filter.get_default()  # type: ignore
        except AttributeError:
            # TODO: This exception handling is required for Pydantic 1.x compatibility. To be removed when the dependency is deprecated.
            return cls()._include_filter

    @classmethod
    def get_default_exclude_filters(cls) -> Dict[str, List[str]]:
        """Expose exclude_filter as class attribute."""
        try:
            return cls._exclude_filter.get_default()  # type: ignore
        except AttributeError:
            # TODO: This exception handling is required for Pydantic 1.x compatibility. To be removed when the dependency is deprecated.
            return cls()._exclude_filter

    @classmethod
    def get_extended_data(cls):
        """Return the default data used to extend processed notification data.

        It's used when the data is not available in the notification itself
        """
        return {"organizer": cls.get_default_organizer(), "provider": cls.get_provider_type()}

    @classmethod
    def get_provider_type(cls) -> str:
        """Return the Provider Type."""
        return cls.__name__.lower()


####################
# PROVIDERS        #
####################


class Apple(GenericProvider):
    """Apple provider custom class."""

    _processors: List[GenericProcessor] = [
        CombinedProcessor(data_parsers=[TextParserApple, SubjectParserApple]),
    ]
    _default_organizer = "peering-noc@group.apple.com"


class AquaComms(GenericProvider):
    """AquaComms provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserAquaComms1, SubjectParserAquaComms1]),
        ]
    )
    _default_organizer = PrivateAttr("tickets@aquacomms.com")


class Arelion(GenericProvider):
    """Arelion (formerly Telia Carrier) provider custom class."""

    _exclude_filter = PrivateAttr({EMAIL_HEADER_SUBJECT: ["Disturbance Information"]})

    _default_organizer = PrivateAttr("support@arelion.com")


class ATT(GenericProvider):
    """ATT provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserATT1, XlsxParserATT1]),
        ]
    )
    _default_organizer = PrivateAttr("g31654@att.com")


class AWS(GenericProvider):
    """AWS provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[EmailDateParser, TextParserAWS1, SubjectParserAWS1]),
        ]
    )
    _default_organizer = PrivateAttr("aws-account-notifications@amazon.com")


class BSO(GenericProvider):
    """BSO provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserBSO1]),
        ]
    )
    _default_organizer = PrivateAttr("network-servicedesk@bso.co")


class Cogent(GenericProvider):
    """Cogent provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserCogent1]),
            CombinedProcessor(data_parsers=[EmailDateParser, TextParserCogent1, SubjectParserCogent1]),
        ]
    )
    _default_organizer = PrivateAttr("support@cogentco.com")


class Colt(GenericProvider):
    """Cogent provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[EmailDateParser, CsvParserColt1, SubjectParserColt1]),
            CombinedProcessor(data_parsers=[EmailDateParser, CsvParserColt1, SubjectParserColt2]),
        ]
    )
    _default_organizer = PrivateAttr("PlannedWorks@colt.net")


class CrownCastle(GenericProvider):
    """Crown Castle Fiber provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserCrownCastle1]),
        ]
    )
    _default_organizer = PrivateAttr("fiberchangemgmt@crowncastle.com")


class Equinix(GenericProvider):
    """Equinix provider custom class."""

    _include_filter = PrivateAttr({EMAIL_HEADER_SUBJECT: ["Network Maintenance"]})

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[HtmlParserEquinix, SubjectParserEquinix, EmailDateParser]),
        ]
    )
    _default_organizer = PrivateAttr("servicedesk@equinix.com")


class EUNetworks(GenericProvider):
    """EUNetworks provider custom class."""

    _default_organizer = "noc@eunetworks.com"


class GlobalCloudXchange(GenericProvider):
    """Global Cloud Xchange provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[EmailDateParser, SubjectParserGcx1, HtmlParserGcx1]),
        ]
    )
    _default_organizer = PrivateAttr("Gnoc@globalcloudxchange.com")


class Google(GenericProvider):
    """Google provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserGoogle1]),
        ]
    )
    _default_organizer = PrivateAttr("noc-noreply@google.com")


class GTT(GenericProvider):
    """EXA (formerly GTT) provider custom class."""

    # "Planned Work Notification", "Emergency Work Notification"
    _include_filter = PrivateAttr(
        {"Icalendar": ["BEGIN"], "ical": ["BEGIN"], EMAIL_HEADER_SUBJECT: ["Work Notification"]}
    )

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            SimpleProcessor(data_parsers=[ICal]),
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserGTT1]),
        ]
    )
    _default_organizer = PrivateAttr("InfraCo.CM@exainfra.net")


class HGC(GenericProvider):
    """HGC provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserHGC1, SubjectParserHGC1]),
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserHGC2, SubjectParserHGC1]),
        ]
    )
    _default_organizer = PrivateAttr("HGCINOCPW@hgc.com.hk")


class Lumen(GenericProvider):
    """Lumen provider custom class."""

    _include_filter = PrivateAttr({EMAIL_HEADER_SUBJECT: ["Scheduled Maintenance"]})

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserLumen1]),
        ]
    )
    _default_organizer = PrivateAttr("smc@lumen.com")


class Megaport(GenericProvider):
    """Megaport provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserMegaport1]),
        ]
    )
    _default_organizer = PrivateAttr("support@megaport.com")


class Momentum(GenericProvider):
    """Momentum provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserMomentum1, SubjectParserMomentum1]),
        ]
    )
    _default_organizer = PrivateAttr("maintenance@momentumtelecom.com")


class Netflix(GenericProvider):
    """Netflix provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [CombinedProcessor(data_parsers=[EmailDateParser, TextParserNetflix1])]
    )
    _default_organizer = PrivateAttr("cdnetops@netflix.com")


class NTT(GenericProvider):
    """NTT provider custom class."""

    _default_organizer = PrivateAttr("noc@us.ntt.net")


class PacketFabric(GenericProvider):
    """PacketFabric provider custom class."""

    _default_organizer = PrivateAttr("support@packetfabric.com")


class PCCW(GenericProvider):
    """PCCW provider custom class."""

    _include_filter = PrivateAttr(
        {
            "Icalendar": ["BEGIN"],
            "ical": ["BEGIN"],
            EMAIL_HEADER_SUBJECT: [
                "Completion - Planned Outage Notification",
                "Completion - Urgent Maintenance Notification",
            ],
        }
    )

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            SimpleProcessor(data_parsers=[ICal]),
            CombinedProcessor(data_parsers=[HtmlParserPCCW, SubjectParserPCCW, EmailDateParser]),
        ]
    )
    _default_organizer = "mailto:gsoc-planned-event@pccwglobal.com"


class Seaborn(GenericProvider):
    """Seaborn provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserSeaborn1, SubjectParserSeaborn1]),
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserSeaborn2, SubjectParserSeaborn2]),
        ]
    )
    _default_organizer = PrivateAttr("inoc@superonline.net")


class Sparkle(GenericProvider):
    """Sparkle provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[HtmlParserSparkle1, EmailDateParser]),
        ]
    )
    _default_organizer = PrivateAttr("TISAmericaNOC@tisparkle.com")


class Tata(GenericProvider):
    """Tata provider custom class."""

    _include_filter = PrivateAttr({EMAIL_HEADER_SUBJECT: ["Planned Work Notification"]})

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[HtmlParserTata, SubjectParserTata, EmailDateParser]),
        ]
    )
    _default_organizer = PrivateAttr("planned.activity@tatacommunications.com")


class Telia(Arelion):
    """Telia provider custom class."""

    # Kept for compatibility purposes, but Telia is renamed Arelion


class Telstra(GenericProvider):
    """Telstra provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            SimpleProcessor(data_parsers=[ICal]),
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserTelstra2]),
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserTelstra1]),
        ]
    )
    _default_organizer = PrivateAttr("gpen@team.telstra.com")


class Turkcell(GenericProvider):
    """Turkcell provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserTurkcell1]),
        ]
    )
    _default_organizer = PrivateAttr("inoc@superonline.net")


class Verizon(GenericProvider):
    """Verizon provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserVerizon1]),
        ]
    )
    _default_organizer = PrivateAttr("NO-REPLY-sched-maint@EMEA.verizonbusiness.com")


class Windstream(GenericProvider):
    """Windstream provider custom class."""

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[EmailDateParser, HtmlParserWindstream1]),
        ]
    )
    _default_organizer = PrivateAttr("wci.maintenance.notifications@windstream.com")


class Zayo(GenericProvider):
    """Zayo provider custom class."""

    _include_filter = {
        "text/html": ["Maintenance Ticket #"],
        "html": ["Maintenance Ticket #"],
    }

    _processors: List[GenericProcessor] = PrivateAttr(
        [
            CombinedProcessor(data_parsers=[EmailDateParser, SubjectParserZayo1, HtmlParserZayo1]),
        ]
    )
    _default_organizer = PrivateAttr("mr@zayo.com")
