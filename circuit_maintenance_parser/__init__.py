"""Circuit-maintenance-parser init."""

from typing import Optional, Type

from .data import NotificationData
from .errors import NonexistentProviderError, ProviderError
from .output import Maintenance
from .provider import (
    AWS,
    BSO,
    GTT,
    HGC,
    NTT,
    AquaComms,
    Apple,
    Arelion,
    Cogent,
    Colt,
    CrownCastle,
    Equinix,
    EUNetworks,
    GenericProvider,
    GlobalCloudXchange,
    Google,
    Lumen,
    Megaport,
    Momentum,
    Netflix,
    PacketFabric,
    PCCW,
    Seaborn,
    Sparkle,
    Tata,
    Telia,
    Telstra,
    Turkcell,
    Verizon,
    Windstream,
    Zayo,
)

SUPPORTED_PROVIDERS = (
    GenericProvider,
    Apple,
    AquaComms,
    Arelion,
    AWS,
    BSO,
    Cogent,
    Colt,
    CrownCastle,
    Equinix,
    EUNetworks,
    GlobalCloudXchange,
    Google,
    GTT,
    HGC,
    Lumen,
    Megaport,
    Momentum,
    Netflix,
    NTT,
    PacketFabric,
    PCCW,
    Seaborn,
    Sparkle,
    Tata,
    Telia,
    Telstra,
    Turkcell,
    Verizon,
    Windstream,
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
    "NotificationData",
    "get_provider_class",
    "get_provider_class_from_sender",
    "ProviderError",
    "NonexistentProviderError",
    "Maintenance",
]
