"""CLI for circuit-maintenance-parser."""
import logging
import sys

import click

from . import SUPPORTED_PROVIDER_PARSERS, init_parser, ParsingError


@click.command()
@click.option("--raw-file", required=True, help="File containing raw data to parse.")
@click.option(
    "--parser",
    type=click.Choice([parser.get_default_provider() for parser in SUPPORTED_PROVIDER_PARSERS]),
    default="ical",
    help="Parser type.",
)
def main(raw_file, parser):
    """Entrypoint into CLI app."""
    # TODO add verbosity flags to manage the logging level.
    logging.basicConfig(level=logging.INFO)

    with open(raw_file) as raw_filename:
        raw_text = raw_filename.read()

    data = {
        "raw": raw_text,
        "provider_type": parser,
    }

    parser = init_parser(**data)
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
