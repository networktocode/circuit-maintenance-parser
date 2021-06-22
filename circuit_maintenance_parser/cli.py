"""CLI for circuit-maintenance-parser."""
import logging
import sys

import click

from . import SUPPORTED_PROVIDERS, init_provider, ParsingError


@click.command()
@click.option("--raw-file", required=True, help="File containing raw data to parse.")
@click.option(
    "--parser",
    type=click.Choice([parser.get_provider_type() for parser in SUPPORTED_PROVIDERS]),
    default="ical",
    help="Parser type.",
)
@click.option("-v", "--verbose", count=True, help="Increase logging verbosity (repeatable)")
def main(raw_file, parser, verbose):
    """Entrypoint into CLI app."""
    # Default logging level is WARNING; specifying -v/--verbose repeatedly can lower the threshold.
    verbosity = logging.WARNING - (10 * verbose)
    logging.basicConfig(level=verbosity)

    with open(raw_file, "rb") as raw_filename:
        raw_bytes = raw_filename.read()

    data = {
        "raw": raw_bytes,
        "provider_type": parser,
    }

    parser = init_provider(**data)
    if not parser:
        click.echo(f"Parser type {parser} is not supported.", err=True)
        sys.exit(1)

    try:
        parsed_notifications = parser.process()
    except ParsingError as parsing_error:
        click.echo(f"Parsing failed: {parsing_error}", err=True)
        sys.exit(1)

    for idx, parsed_notification in enumerate(parsed_notifications):
        click.secho(f"Circuit Maintenance Notification #{idx}", fg="green", bold=True)
        click.secho(parsed_notification.to_json(), fg="yellow")
