"""Tests for Providers."""

import os
from unittest.mock import patch

import pytest

from circuit_maintenance_parser.data import NotificationData
from circuit_maintenance_parser.errors import ProcessorError, ProviderError
from circuit_maintenance_parser.parser import EmailDateParser, Parser
from circuit_maintenance_parser.parsers.openai import OpenAIParser
from circuit_maintenance_parser.processor import CombinedProcessor, SimpleProcessor
from circuit_maintenance_parser.provider import AquaComms, GenericProvider

# pylint: disable=use-implicit-booleaness-not-comparison
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
    "provider_class",
    [ProviderWithOneProcessor, ProviderWithTwoProcessors],
)
def test_provide_get_maintenances(provider_class):
    """Tests GenericProvider."""
    provider = provider_class()

    with patch("circuit_maintenance_parser.provider.GenericProcessor.process") as mock_processor:
        provider.get_maintenances(fake_data)
        assert mock_processor.call_count == 1


@pytest.mark.parametrize(
    "provider_class",
    [ProviderWithOneProcessor, ProviderWithTwoProcessors],
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


@pytest.mark.parametrize(
    "provider_class",
    [GenericProvider, AquaComms],
)
def test_provider_gets_mlparser(provider_class):
    """Test to check the any provider gets a default ML parser when ENV is activated."""
    os.environ["PARSER_OPENAI_API_KEY"] = "some_api_key"
    data = NotificationData.init_from_raw("text/plain", b"fake data")
    data.add_data_part("text/html", b"other data")

    provider = provider_class()

    with patch("circuit_maintenance_parser.processor.GenericProcessor.process") as mock_processor:
        mock_processor.return_value = [{"a": "b"}]
        provider.get_maintenances(data)

    assert provider._processors[-1] == CombinedProcessor(  # pylint: disable=protected-access
        data_parsers=[EmailDateParser, OpenAIParser]
    )


def test_add_subject_to_text_appends_subject_to_text_parts():
    """Test that add_subject_to_text appends subject to text/* and html parts when not already present."""
    provider = GenericProvider()

    # Create test data with email subject and various content types
    data = NotificationData()
    data.add_data_part("email-header-subject", b"Test Maintenance Subject")
    data.add_data_part("text/plain", b"This is plain text content")
    data.add_data_part("text/html", b"<html><body>This is HTML content</body></html>")
    data.add_data_part("html", b"<div>Another HTML content</div>")
    data.add_data_part("application/pdf", b"binary pdf content")

    # Verify initial state - subject should not be in content
    text_part = data.data_parts[1]  # text/plain part
    html_part = data.data_parts[2]  # text/html part
    html_part2 = data.data_parts[3]  # html part

    assert b"Test Maintenance Subject" not in text_part.content
    assert b"Test Maintenance Subject" not in html_part.content
    assert b"Test Maintenance Subject" not in html_part2.content

    # Call the method
    provider.add_subject_to_text(data)

    # Verify subject was appended to text/* and html parts
    text_part_after = data.data_parts[1]  # text/plain part
    html_part_after = data.data_parts[2]  # text/html part
    html_part2_after = data.data_parts[3]  # html part
    pdf_part_after = data.data_parts[4]  # application/pdf part

    assert b"Test Maintenance Subject" in text_part_after.content
    assert text_part_after.content == b"This is plain text content\nTest Maintenance Subject"

    assert b"Test Maintenance Subject" in html_part_after.content
    assert html_part_after.content == b"<html><body>This is HTML content</body></html>\nTest Maintenance Subject"

    assert b"Test Maintenance Subject" in html_part2_after.content
    assert html_part2_after.content == b"<div>Another HTML content</div>\nTest Maintenance Subject"

    # PDF part should remain unchanged
    assert pdf_part_after.content == b"binary pdf content"
    assert b"Test Maintenance Subject" not in pdf_part_after.content


def test_add_subject_to_text_skips_when_subject_already_present():
    """Test that add_subject_to_text skips parts that already contain the subject."""
    provider = GenericProvider()

    # Create test data where subject is already in the content
    data = NotificationData()
    data.add_data_part("email-header-subject", b"Test Subject")
    data.add_data_part("text/plain", b"Content with Test Subject already included")
    data.add_data_part("text/html", b"<html>No subject here</html>")

    # Call the method
    provider.add_subject_to_text(data)

    # First part should remain unchanged since subject is already there
    text_part = data.data_parts[1]
    assert text_part.content == b"Content with Test Subject already included"

    # Second part should have subject appended
    html_part = data.data_parts[2]
    assert html_part.content == b"<html>No subject here</html>\nTest Subject"


def test_add_subject_to_text_no_subject_header():
    """Test that add_subject_to_text does nothing when no email-header-subject part exists."""
    provider = GenericProvider()

    # Create test data without email-header-subject
    data = NotificationData()
    data.add_data_part("text/plain", b"This is plain text content")
    data.add_data_part("text/html", b"<html><body>This is HTML content</body></html>")

    original_text_content = data.data_parts[0].content
    original_html_content = data.data_parts[1].content

    # Call the method
    provider.add_subject_to_text(data)

    # Content should remain unchanged
    assert data.data_parts[0].content == original_text_content
    assert data.data_parts[1].content == original_html_content


def test_add_subject_to_text_handles_decode_errors():
    """Test that add_subject_to_text handles decode errors gracefully."""
    provider = GenericProvider()

    # Create test data with invalid UTF-8 sequences
    data = NotificationData()
    data.add_data_part("email-header-subject", b"\xff\xfe")  # Invalid UTF-8
    data.add_data_part("text/plain", b"\x80\x81")  # Invalid UTF-8

    # This should not raise an exception due to errors="ignore" in decode()
    provider.add_subject_to_text(data)
