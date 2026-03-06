<<<<<<< HEAD
"""CLI for circuit-maintenance-parser."""

import email
import logging
import sys

import click

from . import SUPPORTED_PROVIDERS, init_provider
from .data import NotificationData
from .provider import ProviderError


@click.command()
@click.option("--data-file", required=True, help="File containing raw data to parse.")
@click.option("--data-type", required=False, help="Type of notification data. Default: Icalendar", default="ical")
@click.option(
    "--provider-type",
    type=click.Choice([provider.get_provider_type() for provider in SUPPORTED_PROVIDERS]),
    default="genericprovider",
    help="Provider type.",
)
@click.option("-v", "--verbose", count=True, help="Increase logging verbosity (repeatable)")
def main(provider_type, data_file, data_type, verbose):
    """Entrypoint into CLI app."""
    # Default logging level is WARNING; specifying -v/--verbose repeatedly can lower the threshold.
    verbosity = logging.WARNING - (10 * verbose)
    logging.basicConfig(level=verbosity)
    provider = init_provider(provider_type)
    if not provider:
        click.echo(f"Provider type {provider} is not supported.", err=True)
        sys.exit(1)

    if data_type == "email":
        if str.lower(data_file[-3:]) == "eml":
            with open(data_file, encoding="utf-8") as email_file:
                msg = email.message_from_file(email_file)
            data = NotificationData.init_from_emailmessage(msg)
        else:
            click.echo("File format not supported, only *.eml", err=True)
            sys.exit(1)

    else:
        with open(data_file, "rb") as raw_filename:
            raw_bytes = raw_filename.read()
        data = NotificationData.init_from_raw(data_type, raw_bytes)

    try:
        parsed_notifications = provider.get_maintenances(data)
    except ProviderError as exc:
        click.echo(f"Provider processing failed: {exc}", err=True)
        sys.exit(1)

    for idx, parsed_notification in enumerate(parsed_notifications):
        click.secho(f"Circuit Maintenance Notification #{idx}", fg="green", bold=True)
        click.secho(parsed_notification.to_json(), fg="yellow")
        click.secho(f"Metadata #{idx}", fg="green", bold=True)
        click.secho(parsed_notification.metadata, fg="blue")
=======
"""Example cli using click."""

import logging

import click

from circuit_maintenance_parser.log import initialize_logging

# Import necessary project related things to use in CLI

log = logging.getLogger(__name__)


@click.command()
@click.option("--test", default="Test Output", help="Test argument")
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Logging level",
)
@click.option("--log-file", default=None, help="Log file to output to debug logs to.")
def main(test, log_level, log_file):
    """Entrypoint into CLI app."""
    initialize_logging(level=log_level, filename=log_file)
    log.info("Entrypoint of the CLI app.")
    print(test)
>>>>>>> 11bbb00 (Cookie initially baked targeting develop by NetworkToCode Cookie Drift Manager Tool)
