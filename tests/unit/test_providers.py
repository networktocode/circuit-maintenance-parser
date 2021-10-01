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


def test_provider_with_include_filter():
    """Tests usage of _include_filter."""

    class ProviderWithIncludeFilter(GenericProvider):
        """Fake Provider."""

        _include_filter = {fake_data.data_parts[0].type: [fake_data.data_parts[0].content.decode()]}

    # Because the include filter is matching with the data, we expect that we hit the `process`
    with pytest.raises(ProviderError):
        ProviderWithIncludeFilter().get_maintenances(fake_data)

    # With a non matching data to include, the notification will be skipped and just return empty
    other_fake_data = NotificationData.init_from_raw("other type", b"other data")
    assert ProviderWithIncludeFilter().get_maintenances(other_fake_data) == []


def test_provider_with_exclude_filter():
    """Tests usage of _exclude_filter."""

    class ProviderWithIncludeFilter(GenericProvider):
        """Fake Provider."""

        _exclude_filter = {fake_data.data_parts[0].type: [fake_data.data_parts[0].content.decode()]}

    # Because the exclude filter is matching with the data, we expect that we skip the processing
    assert ProviderWithIncludeFilter().get_maintenances(fake_data) == []

    # With a non matching data to exclude, the notification will be not skipped and processed
    other_fake_data = NotificationData.init_from_raw("other type", b"other data")
    with pytest.raises(ProviderError):
        ProviderWithIncludeFilter().get_maintenances(other_fake_data)


def test_provider_with_include_and_exclude_filters():
    """Tests matching of include and exclude filter, where the exclude takes precedence."""
    data = NotificationData.init_from_raw("fake_type", b"fake data")
    data.add_data_part("other_type", b"other data")

    class ProviderWithIncludeFilter(GenericProvider):
        """Fake Provider."""

        _include_filter = {data.data_parts[0].type: [data.data_parts[0].content.decode()]}
        _exclude_filter = {data.data_parts[1].type: [data.data_parts[1].content.decode()]}

    # Because the exclude filter and the include filter are matching, we expect the exclude to take
    # precedence
    assert ProviderWithIncludeFilter().get_maintenances(data) == []
