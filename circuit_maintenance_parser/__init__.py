"""Notifications parser init."""

from typing import Type, Optional, Iterable

from .errors import NonexistentParserError, ParsingError
<<<<<<< HEAD

from .providers import (
    GenericProvider,
    EUNetworks,
    Lumen,
    Megaport,
    NTT,
    PacketFabric,
    Telstra,
    Zayo,
)

SUPPORTED_PROVIDERS = (
    GenericProvider,
    EUNetworks,
    Lumen,
    Megaport,
    NTT,
    PacketFabric,
    Telstra,
    Zayo,
=======
from .parser import MaintenanceNotification, ICal
from .parsers.eunetworks import ParserEUNetworks
from .parsers.lumen import ParserLumen
from .parsers.megaport import ParserMegaport
from .parsers.ntt import ParserNTT
from .parsers.packetfabric import ParserPacketFabric
from .parsers.telstra import ParserTelstra
from .parsers.zayo import ParserZayo
from .parsers.cogent import ParserCogent


SUPPORTED_PROVIDER_PARSERS = (
    ParserCogent,
    ParserEUNetworks,
    ParserLumen,
    ParserMegaport,
    ParserNTT,
    ParserPacketFabric,
    ParserTelstra,
    ParserZayo,
    ICal,
>>>>>>> orIGin/develop
)

SUPPORTED_PROVIDER_NAMES = [provider.get_provider_type() for provider in SUPPORTED_PROVIDERS]
SUPPORTED_ORGANIZER_EMAILS = [provider.get_default_organizer() for provider in SUPPORTED_PROVIDERS]


def init_parser(**kwargs) -> Optional[GenericProvider]:
    """Returns an instance of the corresponding Notification Parser."""
    try:
        provider_type = kwargs.get("provider_type")
        if not provider_type:
            provider_type = GenericProvider.get_provider_type()
        provider_parser_class = get_provider_class(provider_type)
        return provider_parser_class(**kwargs)

    except NonexistentParserError:
        return None


def get_provider_class(provider_name: str) -> Type[GenericProvider]:
    """Returns the Provider parser class for a specific provider_type."""
    provider_name = provider_name.lower()

    for provider_parser in SUPPORTED_PROVIDERS:
        if provider_parser.get_provider_type() == provider_name:
            break
    else:

        raise NonexistentParserError(
            f"{provider_name} is not a currently supported parser. Only {', '.join(SUPPORTED_PROVIDER_NAMES)}"
        )

    return provider_parser


def get_provider_class_from_sender(email_sender: str) -> Type[GenericProvider]:
    """Returns the notification parser class for an email sender address."""

    for provider_parser in SUPPORTED_PROVIDERS:
        if provider_parser.get_default_organizer() == email_sender:
            break
    else:
        raise NonexistentParserError(
            f"{email_sender} is not a currently supported provider parser. Only {', '.join(SUPPORTED_ORGANIZER_EMAILS)}"
        )

    return provider_parser


def get_provider_data_types(provider_name: str) -> Iterable[str]:
    """Returns the expected data types for each provider."""
    provider_name = provider_name.lower()

    for provider in SUPPORTED_PROVIDERS:
        if provider.get_provider_type() == provider_name:
            break
    else:
        raise NonexistentParserError(
            f"{provider_name} is not a currently supported provider. Only {', '.join(SUPPORTED_PROVIDER_NAMES)}"
        )

    return provider.get_data_types()


__all__ = [
    "init_parser",
    "get_provider_class",
    "get_provider_class_from_sender",
    "get_provider_data_types",
    "ParsingError",
]
