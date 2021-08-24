"""Tests generic for parser."""
import json
import os
from pathlib import Path

import pytest

from circuit_maintenance_parser.errors import MissingMandatoryFields, ParsingError

from circuit_maintenance_parser.parser import ICal
from circuit_maintenance_parser.parsers.cogent import HtmlParserCogent1
from circuit_maintenance_parser.parsers.lumen import HtmlParserLumen1
from circuit_maintenance_parser.parsers.megaport import HtmlParserMegaport1
from circuit_maintenance_parser.parsers.telstra import HtmlParserTelstra1
from circuit_maintenance_parser.parsers.verizon import HtmlParserVerizon1
from circuit_maintenance_parser.parsers.zayo import HtmlParserZayo1


dir_path = os.path.dirname(os.path.realpath(__file__))


@pytest.mark.parametrize(
    "parser_class, raw_file, results_file",
    [
        # iCal
        (ICal, Path(dir_path, "data", "ical", "ical1"), Path(dir_path, "data", "ical", "ical1_result.json"),),
        (ICal, Path(dir_path, "data", "ical", "ical2"), Path(dir_path, "data", "ical", "ical2_result.json"),),
        (ICal, Path(dir_path, "data", "ical", "ical3"), Path(dir_path, "data", "ical", "ical3_result.json"),),
        (ICal, Path(dir_path, "data", "ical", "ical4"), Path(dir_path, "data", "ical", "ical4_result.json"),),
        (ICal, Path(dir_path, "data", "ical", "ical5"), Path(dir_path, "data", "ical", "ical5_result.json"),),
        # Cogent
        (
            HtmlParserCogent1,
            Path(dir_path, "data", "cogent", "cogent1.html"),
            Path(dir_path, "data", "cogent", "cogent1_result.json"),
        ),
        (
            HtmlParserCogent1,
            Path(dir_path, "data", "cogent", "cogent2.html"),
            Path(dir_path, "data", "cogent", "cogent2_result.json"),
        ),
        # Lumen
        (
            HtmlParserLumen1,
            Path(dir_path, "data", "lumen", "lumen1.html"),
            Path(dir_path, "data", "lumen", "lumen1_result.json"),
        ),
        (
            HtmlParserLumen1,
            Path(dir_path, "data", "lumen", "lumen2.html"),
            Path(dir_path, "data", "lumen", "lumen2_result.json"),
        ),
        (
            HtmlParserLumen1,
            Path(dir_path, "data", "lumen", "lumen3.html"),
            Path(dir_path, "data", "lumen", "lumen3_result.json"),
        ),
        # Megaport
        (
            HtmlParserMegaport1,
            Path(dir_path, "data", "megaport", "megaport1.html"),
            Path(dir_path, "data", "megaport", "megaport1_result.json"),
        ),
        (
            HtmlParserMegaport1,
            Path(dir_path, "data", "megaport", "megaport2.html"),
            Path(dir_path, "data", "megaport", "megaport2_result.json"),
        ),
        # NTT
        (ICal, Path(dir_path, "data", "ntt", "ntt1"), Path(dir_path, "data", "ntt", "ntt1_result.json"),),
        # Telstra
        (
            HtmlParserTelstra1,
            Path(dir_path, "data", "telstra", "telstra1.html"),
            Path(dir_path, "data", "telstra", "telstra1_result.json"),
        ),
        (
            HtmlParserTelstra1,
            Path(dir_path, "data", "telstra", "telstra2.html"),
            Path(dir_path, "data", "telstra", "telstra2_result.json"),
        ),
        # Verizon
        (
            HtmlParserVerizon1,
            Path(dir_path, "data", "verizon", "verizon1.html"),
            Path(dir_path, "data", "verizon", "verizon1_result.json"),
        ),
        (
            HtmlParserVerizon1,
            Path(dir_path, "data", "verizon", "verizon2.html"),
            Path(dir_path, "data", "verizon", "verizon2_result.json"),
        ),
        (
            HtmlParserVerizon1,
            Path(dir_path, "data", "verizon", "verizon3.html"),
            Path(dir_path, "data", "verizon", "verizon3_result.json"),
        ),
        # Zayo
        (
            HtmlParserZayo1,
            Path(dir_path, "data", "zayo", "zayo1.html"),
            Path(dir_path, "data", "zayo", "zayo1_result.json"),
        ),
        (
            HtmlParserZayo1,
            Path(dir_path, "data", "zayo", "zayo2.html"),
            Path(dir_path, "data", "zayo", "zayo2_result.json"),
        ),
    ],
)
def test_complete_parsing(parser_class, raw_file, results_file):
    """Tests various parser."""
    with open(raw_file, "rb") as file_obj:
        parser = parser_class(raw=file_obj.read())

    parsed_notifications = parser.process()
    notifications_json = []
    for parsed_notification in parsed_notifications:
        notifications_json.append(json.loads(parsed_notification.to_json()))

    with open(results_file) as res_file:
        expected_result = json.load(res_file)

    assert notifications_json == expected_result


@pytest.mark.parametrize(
    "parser_class, raw_file, exception, error_message",
    [
        # ICal
        (
            ICal,
            Path(dir_path, "data", "ical", "ical_no_account"),
            MissingMandatoryFields,
            """\
1 validation error for Maintenance
account
  String is empty or 'None' (type=value_error)""",
        ),
        (
            ICal,
            Path(dir_path, "data", "ical", "ical_no_maintenance_id"),
            MissingMandatoryFields,
            """\
1 validation error for Maintenance
maintenance_id
  String is empty or 'None' (type=value_error)""",
        ),
        (
            ICal,
            Path(dir_path, "data", "ical", "ical_no_stamp"),
            ParsingError,
            "'NoneType' object has no attribute 'dt'",
        ),
        (
            ICal,
            Path(dir_path, "data", "ical", "ical_no_start"),
            ParsingError,
            "'NoneType' object has no attribute 'dt'",
        ),
        (ICal, Path(dir_path, "data", "ical", "ical_no_end"), ParsingError, "'NoneType' object has no attribute 'dt'"),
        # Zayo
        (
            HtmlParserZayo1,
            Path(dir_path, "data", "zayo", "zayo_missing_maintenance_id.html"),
            MissingMandatoryFields,
            """\
1 validation error for Maintenance
maintenance_id
  field required (type=value_error.missing)""",
        ),
        (
            HtmlParserZayo1,
            Path(dir_path, "data", "zayo", "zayo_bad_html.html"),
            MissingMandatoryFields,
            """\
6 validation errors for Maintenance
account
  field required (type=value_error.missing)
maintenance_id
  field required (type=value_error.missing)
circuits
  At least one circuit has to be included in the maintenance (type=value_error)
status
  field required (type=value_error.missing)
start
  field required (type=value_error.missing)
end
  field required (type=value_error.missing)""",
        ),
    ],
)
def test_errored_parsing(parser_class, raw_file, exception, error_message):
    """Negative tests for various parsers."""
    with open(raw_file, "rb") as file_obj:
        parser = parser_class(raw=file_obj.read())

    with pytest.raises(exception) as exc:
        parser.process()

    assert str(exc.value.__cause__) == error_message
