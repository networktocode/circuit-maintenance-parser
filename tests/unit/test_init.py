"""Tests for generic parser."""

import os

import pytest

from circuit_maintenance_parser import (
    get_provider_class,
    get_provider_class_from_sender,
    init_provider,
)
from circuit_maintenance_parser.errors import NonexistentProviderError
from circuit_maintenance_parser.provider import (
    NTT,
    EUNetworks,
    GenericProvider,
    PacketFabric,
    Zayo,
)

dir_path = os.path.dirname(os.path.realpath(__file__))


@pytest.mark.parametrize(
    "provider_type, result_type",
    [
        ("wrong", None),
        ("", GenericProvider),
        ("ntt", NTT),
        ("packetfabric", PacketFabric),
        ("eunetworks", EUNetworks),
        ("zayo", Zayo),
    ],
)
def test_init_provider(provider_type, result_type):
    """Tests for init_provider."""
    provider = init_provider(provider_type=provider_type)
    if result_type:
        assert isinstance(provider, result_type)
    else:
        assert provider is None


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
        ("wrong", None, NonexistentProviderError),
    ],
)
def test_get_provider_class(provider_name, result, error):
    """Tests for generic parser."""
    if result:
        assert get_provider_class(provider_name) == result
    elif error:
        with pytest.raises(error):
            get_provider_class(provider_name)


@pytest.mark.parametrize(
    "email_sender, result, error",
    [
        (PacketFabric.get_default_organizer(), PacketFabric, None),
        (NTT.get_default_organizer(), NTT, None),
        (Zayo.get_default_organizer(), Zayo, None),
        (EUNetworks.get_default_organizer(), EUNetworks, None),
        ("wrong", None, NonexistentProviderError),
    ],
)
def test_get_provider_class_from_email(email_sender, result, error):
    """Tests for parser from email."""
    if result:
        assert get_provider_class_from_sender(email_sender) == result
    elif error:
        with pytest.raises(error):
            get_provider_class_from_sender(email_sender)
