"""Tests generic for parser."""
import json
import os
from pathlib import Path

import pytest

from circuit_maintenance_parser.errors import ParsingError

# pylint: disable=duplicate-code
from circuit_maintenance_parser.providers import (
    GenericProvider,
    Cogent,
    EUNetworks,
    Lumen,
    Megaport,
    NTT,
    PacketFabric,
    Telia,
    Telstra,
    Zayo,
)

dir_path = os.path.dirname(os.path.realpath(__file__))

GENERIC_ICAL_DATA_PATH = Path(dir_path, "data", "ical", "ical1")
GENERIC_ICAL_RESULT_PATH = Path(dir_path, "data", "ical", "ical1_result.json")


@pytest.mark.parametrize(
    "provider_class, raw_file, results_file",
    [
        # GenericProvider
        (GenericProvider, GENERIC_ICAL_DATA_PATH, GENERIC_ICAL_RESULT_PATH,),
        # Cogent
        (
            Cogent,
            Path(dir_path, "data", "cogent", "cogent1.html"),
            Path(dir_path, "data", "cogent", "cogent1_result.json"),
        ),
        (
            Cogent,
            Path(dir_path, "data", "cogent", "cogent2.html"),
            Path(dir_path, "data", "cogent", "cogent2_result.json"),
        ),
        # EUNetworks
        (EUNetworks, GENERIC_ICAL_DATA_PATH, GENERIC_ICAL_RESULT_PATH,),
        # Lumen
        (Lumen, Path(dir_path, "data", "lumen", "lumen1.html"), Path(dir_path, "data", "lumen", "lumen1_result.json"),),
        (Lumen, Path(dir_path, "data", "lumen", "lumen2.html"), Path(dir_path, "data", "lumen", "lumen2_result.json"),),
        # Megaport
        (
            Megaport,
            Path(dir_path, "data", "megaport", "megaport1.html"),
            Path(dir_path, "data", "megaport", "megaport1_result.json"),
        ),
        (
            Megaport,
            Path(dir_path, "data", "megaport", "megaport2.html"),
            Path(dir_path, "data", "megaport", "megaport2_result.json"),
        ),
        # NTT
        (NTT, Path(dir_path, "data", "ntt", "ntt1"), Path(dir_path, "data", "ntt", "ntt1_result.json"),),
        (NTT, GENERIC_ICAL_DATA_PATH, GENERIC_ICAL_RESULT_PATH,),
        # PacketFabric
        (PacketFabric, GENERIC_ICAL_DATA_PATH, GENERIC_ICAL_RESULT_PATH,),
        # Telia
        (
            Telia,
            Path(dir_path,  "data", "telia", "telia1"),
            Path(dir_path,  "data", "telia", "telia1_result.json"),
        ),
        (
            Telia,
            Path(dir_path,  "data", "telia", "telia2"),
            Path(dir_path,  "data", "telia", "telia2_result.json"),
        ),
        # Telstra
        (
            Telstra,
            Path(dir_path, "data", "telstra", "telstra1.html"),
            Path(dir_path, "data", "telstra", "telstra1_result.json"),
        ),
        (
            Telstra,
            Path(dir_path, "data", "telstra", "telstra2.html"),
            Path(dir_path, "data", "telstra", "telstra2_result.json"),
        ),
        (Telstra, GENERIC_ICAL_DATA_PATH, GENERIC_ICAL_RESULT_PATH,),
        # Zayo
        (Zayo, Path(dir_path, "data", "zayo", "zayo1.html"), Path(dir_path, "data", "zayo", "zayo1_result.json"),),
        (Zayo, Path(dir_path, "data", "zayo", "zayo2.html"), Path(dir_path, "data", "zayo", "zayo2_result.json"),),
    ],
)
def test_complete_provider_process(provider_class, raw_file, results_file):
    """Tests various providers."""
    with open(raw_file, "rb") as file_obj:
        provider = provider_class(raw=file_obj.read())

    parsed_notifications = provider.process()
    notifications_json = []
    for parsed_notification in parsed_notifications:
        notifications_json.append(json.loads(parsed_notification.to_json()))

    with open(results_file) as res_file:
        expected_result = json.load(res_file)

    # The parser result don't have the default organizer that comes from the Provider class
    # If the Provider test is using the GENERIC_ICAL_DATA_PATH it comes with a well-defined 'organizer'
    # from the notificaction.
    if provider_class == GenericProvider or raw_file == GENERIC_ICAL_DATA_PATH:
        expected_result[0]["organizer"] = "mailto:noone@example.com"
    else:
        if expected_result[0]["organizer"] == "unknown":
            expected_result[0]["organizer"] = provider.get_default_organizer()
        if expected_result[0]["provider"] == "unknown":
            expected_result[0]["provider"] = provider.get_provider_type()

    assert notifications_json == expected_result


@pytest.mark.parametrize(
    "provider_class, raw_file, exception, error_message",
    [
        (
            GenericProvider,
            Path(dir_path, "data", "ical", "ical_no_account"),
            ParsingError,
            """\
None of the GenericProvider parsers was able to parse the notification.
Details:
- Parser class ICal from GenericProvider failed due to: 1 validation error for Maintenance\naccount\n  String is empty or 'None' (type=value_error)
""",
        ),
        (
            Telstra,
            Path(dir_path, "data", "ical", "ical_no_account"),
            ParsingError,
            """\
None of the Telstra parsers was able to parse the notification.
Details:
- Parser class ICal from Telstra failed due to: 1 validation error for Maintenance\naccount\n  String is empty or 'None' (type=value_error)
- Parser class HtmlParserTelstra1 from Telstra failed due to: 6 validation errors for Maintenance
account
  field required (type=value_error.missing)
maintenance_id
  field required (type=value_error.missing)
circuits
  field required (type=value_error.missing)
status
  field required (type=value_error.missing)
start
  field required (type=value_error.missing)
end
  field required (type=value_error.missing)
""",
        ),
    ],
)
def test_errored_provider_process(provider_class, raw_file, exception, error_message):
    """Negative tests for various parsers."""
    with open(raw_file, "rb") as file_obj:
        provider = provider_class(raw=file_obj.read())

    with pytest.raises(exception) as exc:
        provider.process()

    assert len(exc.value.related_exceptions) == len(provider_class._parser_classes)  # pylint: disable=protected-access
    assert str(exc.value) == error_message
