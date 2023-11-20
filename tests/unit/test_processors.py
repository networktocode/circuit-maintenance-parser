"""Tests for Processor."""
import copy
from unittest.mock import patch

import pytest
from pydantic.error_wrappers import ValidationError

from circuit_maintenance_parser.output import Maintenance, Metadata
from circuit_maintenance_parser.processor import CombinedProcessor, SimpleProcessor
from circuit_maintenance_parser.data import DataPart, NotificationData
from circuit_maintenance_parser.errors import ProcessorError


from circuit_maintenance_parser.parser import Parser

# pylint: disable=global-variable-undefined

PARSED_DATA = [{"a": "b"}, {"c": "d"}]
EXTENDED_DATA = {"y": "z", "provider": "required"}


class FakeParser(Parser):
    "Fake class to simulate a Parser."
    _parsed_data = PARSED_DATA
    _data_types = ["fake_type"]

    def parse(self, *args, **kwargs):  # pylint: disable=unused-argument
        return copy.deepcopy(self._parsed_data)

    def parser_hook(self, raw: bytes, content_type: str):
        pass


class FakeParser0(FakeParser):
    "Fake class to simulate another Parser."
    _data_types = ["fake_type_0"]
    _parsed_data = copy.deepcopy([PARSED_DATA[0]])


class FakeParser1(FakeParser):
    "Fake class to simulate yet another Parser."
    _data_types = ["fake_type_1"]
    _parsed_data = copy.deepcopy([PARSED_DATA[1]])


class FakeParserMultiDataType(FakeParser):
    "Fake class to simulate yet another Parser."
    _data_types = ["fake_type_0", "fake_type_1"]
    _parsed_data = copy.deepcopy([PARSED_DATA[1]])

    def parse(self, *args, **kwargs):  # pylint: disable=unused-argument
        global parser_runs
        parser_runs += 1  # pylint: disable=undefined-variable
        return copy.deepcopy(self._parsed_data)


# Fake data used for SimpleProcessor
fake_data = NotificationData.init_from_raw("fake_type", b"fake data")
# Fake data used for CombinedProcessor
fake_data_type_0 = NotificationData.init_from_raw("fake_type_0", b"fake data")
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
            parsed_data_element.update(
                {
                    "_metadata": Metadata(
                        provider=EXTENDED_DATA["provider"],
                        processor=SimpleProcessor.get_name(),
                        parsers=[FakeParser.get_name()],
                    )
                }
            )
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
            parsed_data_element.update(
                {
                    "_metadata": Metadata(
                        provider=EXTENDED_DATA["provider"],
                        processor=CombinedProcessor.get_name(),
                        parsers=[FakeParser.get_name()],
                    )
                }
            )
            mock_maintenance.assert_any_call(**parsed_data_element)


def test_combinedprocessor():
    """Tests CombinedProcessor."""
    processor = CombinedProcessor(data_parsers=[FakeParser0, FakeParser1])

    with patch("circuit_maintenance_parser.processor.Maintenance") as mock_maintenance:
        processor.process(fake_data_for_combined, EXTENDED_DATA)
        assert mock_maintenance.call_count == 1
        mock_maintenance.assert_any_call(
            **{
                **PARSED_DATA[0],
                **PARSED_DATA[1],
                **EXTENDED_DATA,
                **{
                    "_metadata": Metadata(
                        provider=EXTENDED_DATA["provider"],
                        processor=CombinedProcessor.get_name(),
                        parsers=[FakeParser0.get_name(), FakeParser1.get_name()],
                    )
                },
            }
        )


def test_combinedprocessor_missing_data():
    """Tests CombinedProcessor when there is not enough info to create a Maintenance."""
    processor = CombinedProcessor(data_parsers=[FakeParser0, FakeParser1])

    with patch("circuit_maintenance_parser.processor.Maintenance") as mock_maintenance:
        mock_maintenance.side_effect = ValidationError(errors=["whatever"], model=Maintenance)
        with pytest.raises(ProcessorError) as e_info:
            # Using the fake_data that returns mutliple maintenances that are not expected in this processor type
            processor.process(fake_data_for_combined, EXTENDED_DATA)

        assert "Not enough information available to create a Maintenance notification" in str(e_info)


def test_combinedprocessor_bleed():
    """Test CombinedProcessor to make sure that information from one processing doesn't bleed over to another."""
    processor = CombinedProcessor(data_parsers=[FakeParser0, FakeParser1])

    with patch("circuit_maintenance_parser.processor.Maintenance") as mock_maintenance:
        processor.process(fake_data_for_combined, EXTENDED_DATA)
        assert mock_maintenance.call_count == 1
        mock_maintenance.assert_any_call(
            **{
                **PARSED_DATA[0],
                **PARSED_DATA[1],
                **EXTENDED_DATA,
                **{
                    "_metadata": Metadata(
                        provider=EXTENDED_DATA["provider"],
                        processor=CombinedProcessor.get_name(),
                        parsers=[FakeParser0.get_name(), FakeParser1.get_name()],
                    )
                },
            }
        )

    with patch("circuit_maintenance_parser.processor.Maintenance") as mock_maintenance:
        processor.process(fake_data_type_0, EXTENDED_DATA)
        assert mock_maintenance.call_count == 1
        mock_maintenance.assert_called_with(
            **{
                **PARSED_DATA[0],
                **EXTENDED_DATA,
                **{
                    "_metadata": Metadata(
                        provider=EXTENDED_DATA["provider"],
                        processor=CombinedProcessor.get_name(),
                        parsers=[FakeParser0.get_name(), FakeParser1.get_name()],
                    )
                },
            }
        )


def test_combinedprocessor_multidatatype():
    """Tests CombinedProcessor."""
    processor = CombinedProcessor(data_parsers=[FakeParserMultiDataType])
    global parser_runs
    parser_runs = 0
    with patch("circuit_maintenance_parser.processor.Maintenance") as mock_maintenance:
        processor.process(fake_data_for_combined, EXTENDED_DATA)
        assert mock_maintenance.call_count == 1
        mock_maintenance.assert_any_call(
            **{
                **PARSED_DATA[1],
                **EXTENDED_DATA,
                **{
                    "_metadata": Metadata(
                        provider=EXTENDED_DATA["provider"],
                        processor=CombinedProcessor.get_name(),
                        parsers=[FakeParserMultiDataType.get_name()],
                    )
                },
            }
        )
        assert parser_runs == 1
