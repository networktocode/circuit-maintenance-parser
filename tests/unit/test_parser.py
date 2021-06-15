"""Tests for generic parser."""
import os

import pytest

from circuit_maintenance_parser import init_parser, get_parser, get_parser_from_sender, get_provider_data_type
from circuit_maintenance_parser import ICal
from circuit_maintenance_parser.errors import NonexistentParserError
from circuit_maintenance_parser.parsers.ntt import ParserNTT
from circuit_maintenance_parser.parsers.packetfabric import ParserPacketFabric
from circuit_maintenance_parser.parsers.zayo import ParserZayo
from circuit_maintenance_parser.parsers.eunetworks import ParserEUNetworks

dir_path = os.path.dirname(os.path.realpath(__file__))


@pytest.mark.parametrize(
    "raw, provider_type, result_type",
    [
        (b"raw_bytes", "wrong", None),
        (b"raw_bytes", "", ICal),
        (b"raw_bytes", "ical", ICal),
        (b"raw_bytes", "ntt", ParserNTT),
        (b"raw_bytes", "packetfabric", ParserPacketFabric),
        (b"raw_bytes", "eunetworks", ParserEUNetworks),
        (b"raw_bytes", "zayo", ParserZayo),
    ],
)
def test_init_parser(raw, provider_type, result_type):
    """Tests for init_parser."""
    result = init_parser(raw=raw, provider_type=provider_type)
    if result_type:
        assert isinstance(result, result_type)
    else:
        assert result is None


@pytest.mark.parametrize(
    "provider_name, result, error",
    [
        ("packetfabric", ParserPacketFabric, None),
        ("pAcketfabrIc", ParserPacketFabric, None),
        ("ntt", ParserNTT, None),
        ("NTT", ParserNTT, None),
        ("zayo", ParserZayo, None),
        ("Zayo", ParserZayo, None),
        ("euNetworks", ParserEUNetworks, None),
        ("EUNetworks", ParserEUNetworks, None),
        ("iCal", ICal, None),
        ("wrong", None, NonexistentParserError),
    ],
)
def test_get_parser(provider_name, result, error):
    """Tests for generic parser."""
    if result:
        assert get_parser(provider_name) == result
    elif error:
        with pytest.raises(NonexistentParserError):
            get_parser(provider_name)


@pytest.mark.parametrize(
    "email_sender, result, error",
    [
        (ParserPacketFabric.get_default_organizer(), ParserPacketFabric, None),
        (ParserNTT.get_default_organizer(), ParserNTT, None),
        (ParserZayo.get_default_organizer(), ParserZayo, None),
        (ParserEUNetworks.get_default_organizer(), ParserEUNetworks, None),
        ("wrong", None, NonexistentParserError),
    ],
)
def test_get_parser_from_email(email_sender, result, error):
    """Tests for parser from email."""
    if result:
        assert get_parser_from_sender(email_sender) == result
    elif error:
        with pytest.raises(NonexistentParserError):
            get_parser_from_sender(email_sender)


@pytest.mark.parametrize(
    "provider_name, result, error",
    [
        ("packetfabric", ParserPacketFabric.get_data_type(), None),
        ("pAcketfabrIc", ParserPacketFabric.get_data_type(), None),
        ("ntt", ParserNTT.get_data_type(), None),
        ("NTT", ParserNTT.get_data_type(), None),
        ("zayo", ParserZayo.get_data_type(), None),
        ("Zayo", ParserZayo.get_data_type(), None),
        ("euNetworks", ParserEUNetworks.get_data_type(), None),
        ("EUNetworks", ParserEUNetworks.get_data_type(), None),
        ("iCal", ICal.get_data_type(), None),
        ("wrong", None, NonexistentParserError),
    ],
)
def test_get_provider_data_type(provider_name, result, error):
    """Tests for generic parser."""
    if result:
        assert get_provider_data_type(provider_name) == result
    elif error:
        with pytest.raises(NonexistentParserError):
            get_provider_data_type(provider_name)