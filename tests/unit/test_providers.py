"""Tests generic for parser."""
import json
import os
from pathlib import Path

import pytest

# pylint: disable=duplicate-code
from circuit_maintenance_parser.providers import (
    GenericProvider,
    Cogent,
    EUNetworks,
    Lumen,
    Megaport,
    NTT,
    PacketFabric,
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
def test_complete_parsing(provider_class, raw_file, results_file):
    """Tests various parser."""
    with open(raw_file, "rb") as file_obj:
        provider = provider_class(raw=file_obj.read())

    parsed_notifications = provider.process()[0]

    with open(results_file) as res_file:
        expected_result = json.load(res_file)

    # The parser result don't have the default organizer that comes from the Provider class
    # If the Provider test is using the GENERIC_ICAL_DATA_PATH it comes with a well-defined 'organizer'
    # from the notificaction.
    if provider_class == GenericProvider or raw_file == GENERIC_ICAL_DATA_PATH:
        expected_result["organizer"] = "mailto:noone@example.com"
    else:
        expected_result["organizer"] = provider.get_default_organizer()

    assert json.loads(parsed_notifications.to_json()) == expected_result
