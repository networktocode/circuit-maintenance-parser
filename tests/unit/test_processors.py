"""Tests for Processor."""
import copy
from unittest.mock import patch

import pytest
from pydantic.error_wrappers import ValidationError

from circuit_maintenance_parser.output import Maintenance
from circuit_maintenance_parser.processor import CombinedProcessor, SimpleProcessor
from circuit_maintenance_parser.data import DataPart, NotificationData
from circuit_maintenance_parser.errors import ProcessorError


from circuit_maintenance_parser.parser import Parser


PARSED_DATA = [
    {
        "account": "Not Available",
        "circuits": [{"circuit_id": "CIR0000000000001", "impact": "OUTAGE"}],
        "end": 1628679600,
        "organizer": "TISAmericaNOC@tisparkle.com",
        "provider": "sparkle",
        "sequence": 1,
        "stamp": 1630077882,
        "start": 1628650800,
        "status": "COMPLETED",
        "summary": "A scheduled work will be carried out to perform hardware upgrade in order in order to ensure the continued integrity of the network.",
        "uid": "0",
    },
    {
        "account": "Not Available",
        "circuits": [{"circuit_id": "CIR0000000000001", "impact": "OUTAGE"}],
        "end": 1628679600,
        "organizer": "TISAmericaNOC@tisparkle.com",
        "provider": "sparkle",
        "sequence": 1,
        "stamp": 1630077882,
        "start": 1628650800,
        "status": "COMPLETED",
        "summary": "A scheduled work will be carried out to perform hardware upgrade in order in order to ensure the continued integrity of the network.",
        "uid": "0",
    },
]
EXTENDED_DATA = {"maintenance_id": "11111"}


class FakeParser(Parser):
    "Fake class to simulate a Parser."
    _parsed_data = PARSED_DATA
    _data_type = "fake_type"

    @classmethod
    def get_data_types(cls):
        return [cls._data_type]

    def parse(self, *args, **kwargs):  # pylint: disable=unused-argument
        return copy.deepcopy(self._parsed_data)

    def parser_hook(self, raw: bytes):
        pass


class FakeParser0(FakeParser):
    "Fake class to simulate another Parser."
    _data_type = "fake_type_0"
    _parsed_data = copy.deepcopy([PARSED_DATA[0]])


class FakeParser1(FakeParser):
    "Fake class to simulate yet another Parser."
    _data_type = "fake_type_1"
    _parsed_data = copy.deepcopy([PARSED_DATA[1]])


# Fake data used for SimpleProcessor
fake_data = NotificationData.init_from_raw("fake_type", b"fake data")
# Fake data used for CombinedProcessor
fake_data_for_combined = NotificationData.init_from_raw("fake_type_0", b"fake data")
if fake_data_for_combined:
    fake_data_for_combined.data_parts.append(DataPart("fake_type_1", b"fake data"))


def test_simpleprocessor():
    """Tests SimpleProcessor."""
    processor = SimpleProcessor(data_parsers=[FakeParser])

    with patch("circuit_maintenance_parser.processor.Maintenance") as mock_maintenance:
        processor.process(fake_data, EXTENDED_DATA)
        assert mock_maintenance.call_count == len(PARSED_DATA)
        for parsed_data_element in PARSED_DATA:
            parsed_data_element.update(EXTENDED_DATA)
            mock_maintenance.assert_any_call(**parsed_data_element)


def test_simpleprocessor_without_matching_type():
    """Tests SimpleProcessor without matching data types."""
    processor = SimpleProcessor(data_parsers=[FakeParser])
    with pytest.raises(ProcessorError) as e_info:
        processor.process(fake_data_for_combined, EXTENDED_DATA)
    assert "None of the supported parsers for processor SimpleProcessor (FakeParser)" in str(e_info)


def test_combinedprocessor_multiple_data():
    """Tests CombinedProcessor wrong parsed data, with multiple entities."""
    processor = CombinedProcessor(data_parsers=[FakeParser])

    with patch("circuit_maintenance_parser.processor.Maintenance") as mock_maintenance:
        processor.process(fake_data, EXTENDED_DATA)
        assert mock_maintenance.call_count == len(PARSED_DATA)
        for parsed_data_element in PARSED_DATA:
            parsed_data_element.update(EXTENDED_DATA)
            mock_maintenance.assert_any_call(**parsed_data_element)


def test_combinedprocessor():
    """Tests CombinedProcessor."""
    processor = CombinedProcessor(data_parsers=[FakeParser0, FakeParser1])

    with patch("circuit_maintenance_parser.processor.Maintenance") as mock_maintenance:
        processor.process(fake_data_for_combined, EXTENDED_DATA)
        assert mock_maintenance.call_count == 1
        mock_maintenance.assert_any_call(**{**PARSED_DATA[0], **PARSED_DATA[1], **EXTENDED_DATA})


def test_combinedprocessor_missing_data():
    """Tests CombinedProcessor when there is not enough info to create a Maintenance."""
    processor = CombinedProcessor(data_parsers=[FakeParser0, FakeParser1])

    with patch("circuit_maintenance_parser.processor.Maintenance") as mock_maintenance:
        mock_maintenance.side_effect = ValidationError(errors=["whatever"], model=Maintenance)
        with pytest.raises(ProcessorError) as e_info:
            # Using the fake_data that returns mutliple maintenances that are not expected in this processor type
            processor.process(fake_data_for_combined, EXTENDED_DATA)

        assert "Not enough information available to create a Maintenance notification" in str(e_info)
