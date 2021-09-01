"""Tests for Processor."""


import json
import os
from pathlib import Path

import pytest

from circuit_maintenance_parser.processor import SimpleProcessor
from circuit_maintenance_parser.data import NotificationData

from circuit_maintenance_parser.parser import ICal
from circuit_maintenance_parser.parsers.cogent import HtmlParserCogent1
from circuit_maintenance_parser.parsers.gtt import HtmlParserGTT1
from circuit_maintenance_parser.parsers.lumen import HtmlParserLumen1
from circuit_maintenance_parser.parsers.megaport import HtmlParserMegaport1
from circuit_maintenance_parser.parsers.telstra import HtmlParserTelstra1
from circuit_maintenance_parser.parsers.verizon import HtmlParserVerizon1
from circuit_maintenance_parser.parsers.zayo import HtmlParserZayo1


dir_path = os.path.dirname(os.path.realpath(__file__))


@pytest.mark.parametrize(
    "processor_class, data_parsers, data_type, data_file, result_parse_file",
    [
        # iCal
        (
            SimpleProcessor,
            [ICal],
            "ical",
            Path(dir_path, "data", "ical", "ical1"),
            Path(dir_path, "data", "ical", "ical1_result.json"),
        ),
        (
            SimpleProcessor,
            [ICal],
            "ical",
            Path(dir_path, "data", "ical", "ical2"),
            Path(dir_path, "data", "ical", "ical2_result.json"),
        ),
        (
            SimpleProcessor,
            [ICal],
            "ical",
            Path(dir_path, "data", "ical", "ical3"),
            Path(dir_path, "data", "ical", "ical3_result.json"),
        ),
        (
            SimpleProcessor,
            [ICal],
            "ical",
            Path(dir_path, "data", "ical", "ical4"),
            Path(dir_path, "data", "ical", "ical4_result.json"),
        ),
        (
            SimpleProcessor,
            [ICal],
            "ical",
            Path(dir_path, "data", "ical", "ical5"),
            Path(dir_path, "data", "ical", "ical5_result.json"),
        ),
        # Cogent
        (
            SimpleProcessor,
            [HtmlParserCogent1],
            "html",
            Path(dir_path, "data", "cogent", "cogent1.html"),
            Path(dir_path, "data", "cogent", "cogent1_result.json"),
        ),
        (
            SimpleProcessor,
            [HtmlParserCogent1],
            "html",
            Path(dir_path, "data", "cogent", "cogent2.html"),
            Path(dir_path, "data", "cogent", "cogent2_result.json"),
        ),
        # GTT
        (
            SimpleProcessor,
            [HtmlParserGTT1],
            "html",
            Path(dir_path, "data", "gtt", "gtt1.html"),
            Path(dir_path, "data", "gtt", "gtt1_result.json"),
        ),
        (
            SimpleProcessor,
            [HtmlParserGTT1],
            "html",
            Path(dir_path, "data", "gtt", "gtt2.html"),
            Path(dir_path, "data", "gtt", "gtt2_result.json"),
        ),
        (
            SimpleProcessor,
            [HtmlParserGTT1],
            "html",
            Path(dir_path, "data", "gtt", "gtt3.html"),
            Path(dir_path, "data", "gtt", "gtt3_result.json"),
        ),
        # # Lumen
        (
            SimpleProcessor,
            [HtmlParserLumen1],
            "html",
            Path(dir_path, "data", "lumen", "lumen1.html"),
            Path(dir_path, "data", "lumen", "lumen1_result.json"),
        ),
        (
            SimpleProcessor,
            [HtmlParserLumen1],
            "html",
            Path(dir_path, "data", "lumen", "lumen2.html"),
            Path(dir_path, "data", "lumen", "lumen2_result.json"),
        ),
        (
            SimpleProcessor,
            [HtmlParserLumen1],
            "html",
            Path(dir_path, "data", "lumen", "lumen3.html"),
            Path(dir_path, "data", "lumen", "lumen3_result.json"),
        ),
        # Megaport
        (
            SimpleProcessor,
            [HtmlParserMegaport1],
            "html",
            Path(dir_path, "data", "megaport", "megaport1.html"),
            Path(dir_path, "data", "megaport", "megaport1_result.json"),
        ),
        (
            SimpleProcessor,
            [HtmlParserMegaport1],
            "html",
            Path(dir_path, "data", "megaport", "megaport2.html"),
            Path(dir_path, "data", "megaport", "megaport2_result.json"),
        ),
        # NTT
        (
            SimpleProcessor,
            [ICal],
            "ical",
            Path(dir_path, "data", "ntt", "ntt1"),
            Path(dir_path, "data", "ntt", "ntt1_result.json"),
        ),
        # Telstra
        (
            SimpleProcessor,
            [HtmlParserTelstra1],
            "html",
            Path(dir_path, "data", "telstra", "telstra1.html"),
            Path(dir_path, "data", "telstra", "telstra1_result.json"),
        ),
        (
            SimpleProcessor,
            [HtmlParserTelstra1],
            "html",
            Path(dir_path, "data", "telstra", "telstra2.html"),
            Path(dir_path, "data", "telstra", "telstra2_result.json"),
        ),
        # Verizon
        (
            SimpleProcessor,
            [HtmlParserVerizon1],
            "html",
            Path(dir_path, "data", "verizon", "verizon1.html"),
            Path(dir_path, "data", "verizon", "verizon1_result.json"),
        ),
        (
            SimpleProcessor,
            [HtmlParserVerizon1],
            "html",
            Path(dir_path, "data", "verizon", "verizon2.html"),
            Path(dir_path, "data", "verizon", "verizon2_result.json"),
        ),
        (
            SimpleProcessor,
            [HtmlParserVerizon1],
            "html",
            Path(dir_path, "data", "verizon", "verizon3.html"),
            Path(dir_path, "data", "verizon", "verizon3_result.json"),
        ),
        # Zayo
        (
            SimpleProcessor,
            [HtmlParserZayo1],
            "html",
            Path(dir_path, "data", "zayo", "zayo1.html"),
            Path(dir_path, "data", "zayo", "zayo1_result.json"),
        ),
        (
            SimpleProcessor,
            [HtmlParserZayo1],
            "html",
            Path(dir_path, "data", "zayo", "zayo2.html"),
            Path(dir_path, "data", "zayo", "zayo2_result.json"),
        ),
    ],
)
def test_processor(  # pylint: disable=too-many-locals
    processor_class, data_parsers, data_type, data_file, result_parse_file
):
    """Tests various processors."""
    extended_data = {"provider": "some provider", "organizer": "some organizer"}
    # TODO: check how to make data optional from Pydantic do not initialized?
    default_maintenance_data = {"stamp": None, "uid": "0", "sequence": 1, "summary": ""}
    extended_data.update(default_maintenance_data)

    with open(data_file, "rb") as file_obj:
        if data_type in ["ical", "html"]:
            data = NotificationData.init(data_type, file_obj.read())
        # TODO: Add EML testing

    parsed_notifications = processor_class(data_parsers=data_parsers).process(data, extended_data)

    notifications_json = []
    for parsed_notification in parsed_notifications:
        notifications_json.append(json.loads(parsed_notification.to_json()))

    with open(result_parse_file) as res_file:
        expected_result = json.load(res_file)

    for result in expected_result:
        temp_res = result.copy()
        result.update(extended_data)
        result.update(temp_res)

    assert notifications_json == expected_result
