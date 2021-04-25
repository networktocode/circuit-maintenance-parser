"""Tests for packetfabric parser."""
import json
import os
from pathlib import Path

import pytest

from circuit_maintenance_parser.parsers.packetfabric import ParserPacketFabric

dir_path = os.path.dirname(os.path.realpath(__file__))


@pytest.mark.parametrize(
    "raw_file, results_file",
    [
        (
            Path(dir_path, "data", "packetfabric", "packetfabric1"),
            Path(dir_path, "data", "packetfabric", "packetfabric1_result.json"),
        ),
    ],
)
def test_complete_parsing(raw_file, results_file):
    """Tests for packetfabric parser."""
    with open(raw_file) as file_obj:
        parser = ParserPacketFabric(raw=file_obj.read())

    parsed_notifications = parser.process()[0]

    with open(results_file) as res_file:
        expected_result = json.load(res_file)

    assert json.loads(parsed_notifications.to_json()) == expected_result
