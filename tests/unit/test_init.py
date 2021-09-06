"""Tests for generic parser."""
import os
from pathlib import Path
import email

import pytest

from circuit_maintenance_parser import (
    init_provider,
    get_provider_class,
    get_provider_class_from_sender,
    init_data_raw,
    init_data_email,
    init_data_emailmessage,
)
from circuit_maintenance_parser.data import NotificationData
from circuit_maintenance_parser.errors import NonexistentProviderError
from circuit_maintenance_parser.provider import (
    GenericProvider,
    EUNetworks,
    NTT,
    PacketFabric,
    Zayo,
)


dir_path = os.path.dirname(os.path.realpath(__file__))


def test_init_data_raw():
    """Test the init_data_raw function."""
    data = init_data_raw("my_type", b"my_content")
    assert isinstance(data, NotificationData)
    assert len(data.data_parts) == 1
    assert data.data_parts[0].type == "my_type"
    assert data.data_parts[0].content == b"my_content"


def test_init_data_email():
    """Test the email data load."""
    with open(Path(dir_path, "data", "email", "test_sample_message.eml"), "rb") as email_file:
        email_raw_data = email_file.read()
    data = init_data_email(email_raw_data)
    assert isinstance(data, NotificationData)
    assert len(data.data_parts) == 7


def test_init_data_emailmessage():
    """Test the emailmessage data load."""
    with open(Path(dir_path, "data", "email", "test_sample_message.eml"), "rb") as email_file:
        email_raw_data = email_file.read()
    raw_email_string = email_raw_data.decode("utf-8")
    email_message = email.message_from_string(raw_email_string)
    data = init_data_emailmessage(email_message)
    assert isinstance(data, NotificationData)
    assert len(data.data_parts) == 7


@pytest.mark.parametrize(
    "provider_type, result_type, extended_data",
    [
        ("wrong", None, {}),
        ("", GenericProvider, {"provider_type": "a"}),
        ("ntt", NTT, {"organizer": "a"}),
        ("packetfabric", PacketFabric, {"provider_type": "a", "organizer": "a"}),
        ("eunetworks", EUNetworks, {}),
        ("zayo", None, {"non supported attribute": 1}),
    ],
)
def test_init_provider(provider_type, result_type, extended_data):
    """Tests for init_provider."""
    provider = init_provider(provider_type=provider_type, default_data=extended_data)
    if result_type:
        assert isinstance(provider, result_type)
        if "provider_type" in extended_data:
            assert provider.provider_type == extended_data["provider_type"]
        if "organizer" in extended_data:
            assert provider.organizer == extended_data["organizer"]
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
        (PacketFabric().get_default_organizer(), PacketFabric, None),
        (NTT().get_default_organizer(), NTT, None),
        (Zayo().get_default_organizer(), Zayo, None),
        (EUNetworks().get_default_organizer(), EUNetworks, None),
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
