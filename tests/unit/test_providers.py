"""Tests for Provider."""
import json
import os
from pathlib import Path

import pytest

from circuit_maintenance_parser.data import NotificationData

# pylint: disable=duplicate-code
from circuit_maintenance_parser.provider import (
    GenericProvider,
    Cogent,
    EUNetworks,
    Lumen,
    Megaport,
    NTT,
    PacketFabric,
    Telia,
    Telstra,
    Verizon,
    Zayo,
)

dir_path = os.path.dirname(os.path.realpath(__file__))

GENERIC_ICAL_DATA_PATH = Path(dir_path, "data", "ical", "ical1")
GENERIC_ICAL_RESULT_PATH = Path(dir_path, "data", "ical", "ical1_result.json")


@pytest.mark.parametrize(
    "provider_class, data_type, data_file, result_parse_file",
    [
        # GenericProvider
        (GenericProvider, "ical", GENERIC_ICAL_DATA_PATH, GENERIC_ICAL_RESULT_PATH,),
        # Cogent
        (
            Cogent,
            "html",
            Path(dir_path, "data", "cogent", "cogent1.html"),
            Path(dir_path, "data", "cogent", "cogent1_result.json"),
        ),
        (
            Cogent,
            "html",
            Path(dir_path, "data", "cogent", "cogent2.html"),
            Path(dir_path, "data", "cogent", "cogent2_result.json"),
        ),
        # EUNetworks
        (EUNetworks, "ical", GENERIC_ICAL_DATA_PATH, GENERIC_ICAL_RESULT_PATH,),
        # Lumen
        (
            Lumen,
            "html",
            Path(dir_path, "data", "lumen", "lumen1.html"),
            Path(dir_path, "data", "lumen", "lumen1_result.json"),
        ),
        (
            Lumen,
            "html",
            Path(dir_path, "data", "lumen", "lumen2.html"),
            Path(dir_path, "data", "lumen", "lumen2_result.json"),
        ),
        # Megaport
        (
            Megaport,
            "html",
            Path(dir_path, "data", "megaport", "megaport1.html"),
            Path(dir_path, "data", "megaport", "megaport1_result.json"),
        ),
        (
            Megaport,
            "html",
            Path(dir_path, "data", "megaport", "megaport2.html"),
            Path(dir_path, "data", "megaport", "megaport2_result.json"),
        ),
        # NTT
        (NTT, "ical", Path(dir_path, "data", "ntt", "ntt1"), Path(dir_path, "data", "ntt", "ntt1_result.json"),),
        (NTT, "ical", GENERIC_ICAL_DATA_PATH, GENERIC_ICAL_RESULT_PATH,),
        # PacketFabric
        (PacketFabric, "ical", GENERIC_ICAL_DATA_PATH, GENERIC_ICAL_RESULT_PATH,),
        # Telia
        (
            Telia,
            "ical",
            Path(dir_path, "data", "telia", "telia1"),
            Path(dir_path, "data", "telia", "telia1_result.json"),
        ),
        (
            Telia,
            "ical",
            Path(dir_path, "data", "telia", "telia2"),
            Path(dir_path, "data", "telia", "telia2_result.json"),
        ),
        # Telstra
        (
            Telstra,
            "html",
            Path(dir_path, "data", "telstra", "telstra1.html"),
            Path(dir_path, "data", "telstra", "telstra1_result.json"),
        ),
        (
            Telstra,
            "html",
            Path(dir_path, "data", "telstra", "telstra2.html"),
            Path(dir_path, "data", "telstra", "telstra2_result.json"),
        ),
        (Telstra, "ical", GENERIC_ICAL_DATA_PATH, GENERIC_ICAL_RESULT_PATH,),
        # Verizon
        (
            Verizon,
            "html",
            Path(dir_path, "data", "verizon", "verizon1.html"),
            Path(dir_path, "data", "verizon", "verizon1_result.json"),
        ),
        (
            Verizon,
            "html",
            Path(dir_path, "data", "verizon", "verizon2.html"),
            Path(dir_path, "data", "verizon", "verizon2_result.json"),
        ),
        (
            Verizon,
            "html",
            Path(dir_path, "data", "verizon", "verizon3.html"),
            Path(dir_path, "data", "verizon", "verizon3_result.json"),
        ),
        # Zayo
        (
            Zayo,
            "html",
            Path(dir_path, "data", "zayo", "zayo1.html"),
            Path(dir_path, "data", "zayo", "zayo1_result.json"),
        ),
        (
            Zayo,
            "html",
            Path(dir_path, "data", "zayo", "zayo2.html"),
            Path(dir_path, "data", "zayo", "zayo2_result.json"),
        ),
    ],
)
def test_provider_get_maintenances(provider_class, data_type, data_file, result_parse_file):
    """Tests various providers."""
    extended_data = provider_class.get_extended_data()
    # TODO: check how to make data optional from Pydantic do not initialized?
    default_maintenance_data = {"stamp": None, "uid": "0", "sequence": 1, "summary": ""}
    extended_data.update(default_maintenance_data)

    with open(data_file, "rb") as file_obj:
        if data_type in ["ical", "html"]:
            data = NotificationData.init(data_type, file_obj.read())
        # TODO: Add EML testing

    # pdb.set_trace()
    parsed_notifications = provider_class().get_maintenances(data)
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


# @pytest.mark.parametrize(
#     "provider_class, raw_file, exception, error_message",
#     [
#         (
#             GenericProvider,
#             Path(dir_path, "data", "ical", "ical_no_account"),
#             ParsingError,
#             """\
# None of the GenericProvider parsers was able to parse the notification.
# Details:
# - Parser class ICal from GenericProvider failed due to: 1 validation error for Maintenance\naccount\n  String is empty or 'None' (type=value_error)
# """,
#         ),
#         (
#             Telstra,
#             Path(dir_path, "data", "ical", "ical_no_account"),
#             ParsingError,
#             """\
# None of the Telstra parsers was able to parse the notification.
# Details:
# - Parser class ICal from Telstra failed due to: 1 validation error for Maintenance\naccount\n  String is empty or 'None' (type=value_error)
# - Parser class HtmlParserTelstra1 from Telstra failed due to: 6 validation errors for Maintenance
# account
#   field required (type=value_error.missing)
# maintenance_id
#   field required (type=value_error.missing)
# circuits
#   field required (type=value_error.missing)
# status
#   field required (type=value_error.missing)
# start
#   field required (type=value_error.missing)
# end
#   field required (type=value_error.missing)
# """,
#         ),
#     ],
# )
# def test_errored_provider_process(provider_class, raw_file, exception, error_message):
#     """Negative tests for various parsers."""
#     with open(raw_file, "rb") as file_obj:
#         provider = provider_class(raw=file_obj.read())

#     with pytest.raises(exception) as exc:
#         provider.process()

#     assert len(exc.value.related_exceptions) == len(provider_class._parser_classes)  # pylint: disable=protected-access
#     assert str(exc.value) == error_message
