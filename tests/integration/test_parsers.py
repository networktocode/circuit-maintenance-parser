"""Tests generic for parser."""
import json
import os
from pathlib import Path

import pytest

from circuit_maintenance_parser.errors import MissingMandatoryFields, ParsingError

from circuit_maintenance_parser.parsers.eunetworks import ParserEUNetworks
from circuit_maintenance_parser.parser import ICal
from circuit_maintenance_parser.parsers.lumen import ParserLumen
from circuit_maintenance_parser.parsers.megaport import ParserMegaport
from circuit_maintenance_parser.parsers.ntt import ParserNTT
from circuit_maintenance_parser.parsers.packetfabric import ParserPacketFabric
from circuit_maintenance_parser.parsers.telstra import ParserTelstra
from circuit_maintenance_parser.parsers.zayo import ParserZayo


dir_path = os.path.dirname(os.path.realpath(__file__))


@pytest.mark.parametrize(
    "parser_class, raw_file, results_file",
    [
        # EUNetworks
        (
            ParserEUNetworks,
            Path(dir_path, "data", "eunetworks", "eunetworks1"),
            Path(dir_path, "data", "eunetworks", "eunetworks1_result.json"),
        ),
        # iCal
        (ICal, Path(dir_path, "data", "ical", "ical1"), Path(dir_path, "data", "ical", "ical1_result.json"),),
        (ICal, Path(dir_path, "data", "ical", "ical2"), Path(dir_path, "data", "ical", "ical2_result.json"),),
        (ICal, Path(dir_path, "data", "ical", "ical3"), Path(dir_path, "data", "ical", "ical3_result.json"),),
        (ICal, Path(dir_path, "data", "ical", "ical4"), Path(dir_path, "data", "ical", "ical4_result.json"),),
        (ICal, Path(dir_path, "data", "ical", "ical5"), Path(dir_path, "data", "ical", "ical5_result.json"),),
        # Lumen
        (
            ParserLumen,
            Path(dir_path, "data", "lumen", "lumen1.html"),
            Path(dir_path, "data", "lumen", "lumen1_result.json"),
        ),
        (
            ParserLumen,
            Path(dir_path, "data", "lumen", "lumen2.html"),
            Path(dir_path, "data", "lumen", "lumen2_result.json"),
        ),
        # Megaport
        (
            ParserMegaport,
            Path(dir_path, "data", "megaport", "megaport1.html"),
            Path(dir_path, "data", "megaport", "megaport1_result.json"),
        ),
        (
            ParserMegaport,
            Path(dir_path, "data", "megaport", "megaport2.html"),
            Path(dir_path, "data", "megaport", "megaport2_result.json"),
        ),
        # NTT
        (ParserNTT, Path(dir_path, "data", "ntt", "ntt1"), Path(dir_path, "data", "ntt", "ntt1_result.json"),),
        # PacketFabric
        (
            ParserPacketFabric,
            Path(dir_path, "data", "packetfabric", "packetfabric1"),
            Path(dir_path, "data", "packetfabric", "packetfabric1_result.json"),
        ),
        # Telstra
        (
            ParserTelstra,
            Path(dir_path, "data", "telstra", "telstra1.html"),
            Path(dir_path, "data", "telstra", "telstra1_result.json"),
        ),
        (
            ParserTelstra,
            Path(dir_path, "data", "telstra", "telstra2.html"),
            Path(dir_path, "data", "telstra", "telstra2_result.json"),
        ),
        # Zayo
        (
            ParserZayo,
            Path(dir_path, "data", "zayo", "zayo1.html"),
            Path(dir_path, "data", "zayo", "zayo1_result.json"),
        ),
        (
            ParserZayo,
            Path(dir_path, "data", "zayo", "zayo2.html"),
            Path(dir_path, "data", "zayo", "zayo2_result.json"),
        ),
    ],
)
def test_complete_parsing(parser_class, raw_file, results_file):
    """Tests various parser."""
    with open(raw_file, "rb") as file_obj:
        parser = parser_class(raw=file_obj.read())

    parsed_notifications = parser.process()[0]

    with open(results_file) as res_file:
        expected_result = json.load(res_file)

    assert json.loads(parsed_notifications.to_json()) == expected_result


@pytest.mark.parametrize(
    "parser_class, raw_file, exception",
    [
        # ICal
        (ICal, Path(dir_path, "data", "ical", "ical_no_account"), MissingMandatoryFields,),
        (ICal, Path(dir_path, "data", "ical", "ical_no_maintenance_id"), MissingMandatoryFields,),
        (ICal, Path(dir_path, "data", "ical", "ical_no_stamp"), ParsingError,),
        (ICal, Path(dir_path, "data", "ical", "ical_no_start"), ParsingError,),
        (ICal, Path(dir_path, "data", "ical", "ical_no_end"), ParsingError,),
        # Zayo
        (ParserZayo, Path(dir_path, "data", "zayo", "zayo_missing_maintenance_id.html"), MissingMandatoryFields,),
        (ParserZayo, Path(dir_path, "data", "zayo", "zayo_bad_html.html"), MissingMandatoryFields,),
    ],
)
def test_errored_parsing(parser_class, raw_file, exception):
    """Negative tests for various parsers."""
    with open(raw_file, "rb") as file_obj:
        parser = parser_class(raw=file_obj.read())

    with pytest.raises(exception):
        parser.process()
