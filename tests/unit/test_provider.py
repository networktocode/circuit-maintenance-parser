"""Tests for generic parser."""
import os

import pytest

from circuit_maintenance_parser import (
    init_parser,
    get_provider_parser_class,
    get_provider_parser_class_from_sender,
    get_provider_data_types,
)
from circuit_maintenance_parser.errors import NonexistentParserError
from circuit_maintenance_parser.providers import (
    GenericProvider,
    EUNetworks,
    NTT,
    PacketFabric,
    Telstra,
    Zayo,
)


dir_path = os.path.dirname(os.path.realpath(__file__))


@pytest.mark.parametrize(
    "raw, provider_type, result_type",
    [
        (b"raw_bytes", "wrong", None),
        (b"raw_bytes", "", GenericProvider),
        (b"raw_bytes", "ntt", NTT),
        (b"raw_bytes", "packetfabric", PacketFabric),
        (b"raw_bytes", "eunetworks", EUNetworks),
        (b"raw_bytes", "zayo", Zayo),
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
        ("packetfabric", PacketFabric, None),
        ("pAcketfabrIc", PacketFabric, None),
        ("ntt", NTT, None),
        ("NTT", NTT, None),
        ("zayo", Zayo, None),
        ("Zayo", Zayo, None),
        ("euNetworks", EUNetworks, None),
        ("EUNetworks", EUNetworks, None),
        ("wrong", None, NonexistentParserError),
    ],
)
def test_get_provider_parser_class(provider_name, result, error):
    """Tests for generic parser."""
    if result:
        assert get_provider_parser_class(provider_name) == result
    elif error:
        with pytest.raises(NonexistentParserError):
            get_provider_parser_class(provider_name)


@pytest.mark.parametrize(
    "email_sender, result, error",
    [
        (PacketFabric.get_default_organizer(), PacketFabric, None),
        (NTT.get_default_organizer(), NTT, None),
        (Zayo.get_default_organizer(), Zayo, None),
        (EUNetworks.get_default_organizer(), EUNetworks, None),
        ("wrong", None, NonexistentParserError),
    ],
)
def test_get_provider_parser_class_from_email(email_sender, result, error):
    """Tests for parser from email."""
    if result:
        assert get_provider_parser_class_from_sender(email_sender) == result
    elif error:
        with pytest.raises(NonexistentParserError):
            get_provider_parser_class_from_sender(email_sender)


@pytest.mark.parametrize(
    "provider_name, result, error",
    [
        ("packetfabric", PacketFabric.get_data_types(), None),
        ("pAcketfabrIc", PacketFabric.get_data_types(), None),
        ("ntt", NTT.get_data_types(), None),
        ("NTT", NTT.get_data_types(), None),
        ("zayo", Zayo.get_data_types(), None),
        ("Zayo", Zayo.get_data_types(), None),
        ("euNetworks", EUNetworks.get_data_types(), None),
        ("EUNetworks", EUNetworks.get_data_types(), None),
        ("TelstRa", Telstra.get_data_types(), None),
        ("Telstra", Telstra.get_data_types(), None),
        ("wrong", None, NonexistentParserError),
    ],
)
def test_get_provider_data_types(provider_name, result, error):
    """Tests for to validate the data types for each provider"""
    if result:
        assert get_provider_data_types(provider_name) == result
    elif error:
        with pytest.raises(NonexistentParserError):
            get_provider_data_types(provider_name)
