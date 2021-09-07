"""Notifications parser init."""

from typing import Type, Optional

from .data import NotificationData
from .errors import NonexistentProviderError, ProviderError
from .provider import (
    GenericProvider,
    Cogent,
    Colt,
    EUNetworks,
    GTT,
    Lumen,
    Megaport,
    Momentum,
    NTT,
    PacketFabric,
    Seaborn,
    Telia,
    Telstra,
    Turkcell,
    Verizon,
    Zayo,
)

SUPPORTED_PROVIDERS = (
    GenericProvider,
    Cogent,
    Colt,
    EUNetworks,
    GTT,
    Lumen,
    Megaport,
    Momentum,
    NTT,
    PacketFabric,
    Seaborn,
    Telia,
    Telstra,
    Turkcell,
    Verizon,
    Zayo,
)

SUPPORTED_PROVIDER_NAMES = [provider.get_provider_type() for provider in SUPPORTED_PROVIDERS]
SUPPORTED_ORGANIZER_EMAILS = [provider.get_default_organizer() for provider in SUPPORTED_PROVIDERS]


def init_provider(provider_type=None) -> Optional[GenericProvider]:
    """Returns an instance of the corresponding Notification Provider."""
    try:
        if not provider_type:
            provider_type = GenericProvider.get_provider_type()
        provider_parser_class = get_provider_class(provider_type)
        return provider_parser_class()

    except NonexistentProviderError:
        return None


def init_data_raw(data_type: str, data_content: bytes) -> NotificationData:
    """Returns an instance of NotificationData from one combination of data type and content."""
    return NotificationData.init(data_type, data_content)


def init_data_email(raw_email_bytes: bytes) -> NotificationData:
    """Returns an instance of NotificationData from a raw email content."""
    return NotificationData.init_from_email_bytes(raw_email_bytes)


def init_data_emailmessage(email_message) -> NotificationData:
    """Returns an instance of NotificationData from an email message."""
    return NotificationData.init_from_emailmessage(email_message)


def get_provider_class(provider_name: str) -> Type[GenericProvider]:
    """Returns the Provider parser class for a specific provider_type."""
    provider_name = provider_name.lower()

    for provider_parser in SUPPORTED_PROVIDERS:
        if provider_parser.get_provider_type() == provider_name:
            break
    else:

        raise NonexistentProviderError(
            f"{provider_name} is not a currently supported provider. Only {', '.join(SUPPORTED_PROVIDER_NAMES)}"
        )

    return provider_parser


def get_provider_class_from_sender(email_sender: str) -> Type[GenericProvider]:
    """Returns the notification parser class for an email sender address."""

    for provider_parser in SUPPORTED_PROVIDERS:
        if provider_parser.get_default_organizer() == email_sender:
            break
    else:
        raise NonexistentProviderError(
            f"{email_sender} is not a currently supported provider parser. Only {', '.join(SUPPORTED_ORGANIZER_EMAILS)}"
        )

    return provider_parser


__all__ = [
    "init_provider",
    "init_data_raw",
    "init_data_email",
    "init_data_emailmessage",
    "get_provider_class",
    "get_provider_class_from_sender",
    "ProviderError",
    "NonexistentProviderError",
]
