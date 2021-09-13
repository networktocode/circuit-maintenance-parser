"""Tests for Providers."""
from unittest.mock import patch

import pytest

from circuit_maintenance_parser.data import NotificationData
from circuit_maintenance_parser.errors import ProcessorError, ProviderError
from circuit_maintenance_parser.processor import SimpleProcessor
from circuit_maintenance_parser.provider import GenericProvider
from circuit_maintenance_parser.parser import Parser


fake_data = NotificationData.init_from_raw("fake_type", b"fake data")


class ProviderWithOneProcessor(GenericProvider):
    """Fake Provider with only one Processor."""


class ProviderWithTwoProcessors(GenericProvider):
    """Fake Provider with two Processors."""

    _processors = [
        SimpleProcessor(data_parsers=[Parser]),
        SimpleProcessor(data_parsers=[Parser]),
    ]


@pytest.mark.parametrize(
    "provider_class", [ProviderWithOneProcessor, ProviderWithTwoProcessors],
)
def test_provide_get_maintenances(provider_class):
    """Tests GenericProvider."""
    provider = provider_class()

    with patch("circuit_maintenance_parser.provider.GenericProcessor.process") as mock_processor:
        provider.get_maintenances(fake_data)
        assert mock_processor.call_count == 1


@pytest.mark.parametrize(
    "provider_class", [ProviderWithOneProcessor, ProviderWithTwoProcessors],
)
def test_provide_get_maintenances_one_exception(provider_class):
    """Tests GenericProvider."""
    provider = provider_class()

    with patch("circuit_maintenance_parser.provider.GenericProcessor.process") as mock_processor:
        mock_processor.side_effect = [ProcessorError, ""]
        if len(provider._processors) < 2:  # pylint: disable=protected-access
            with pytest.raises(ProviderError) as ex_info:
                provider.get_maintenances(fake_data)
            assert "Failed creating Maintenance notification for" in str(ex_info)

        else:
            provider.get_maintenances(fake_data)
            assert mock_processor.call_count == 2
