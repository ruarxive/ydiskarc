#!/usr/bin/env python
# -*- coding: utf8 -*-
import logging
from typing import Optional

import typer

import ydiskarc

from .cmds.processor import Project, validate_yandex_url

# Create Typer app
app = typer.Typer(
    name="ydiskarc",
    help="A command-line tool to backup public resources from Yandex.Disk",
    add_completion=False,
)


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration.

    Args:
        verbose: If True, enable verbose logging. If False, disable logging.
    """
    if verbose:
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
        )
    else:
        # Disable logging when not verbose
        logging.disable(logging.CRITICAL)


@app.command("full")
def full(
    url: str = typer.Argument(..., help="URL of the Yandex.Disk public resource to download"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output directory where files will be saved"
    ),
    filename: Optional[str] = typer.Option(
        None,
        "--filename",
        "-f",
        help="Output filename (if not specified, filename will be auto-detected)",
    ),
    metadata: bool = typer.Option(
        False, "--metadata", "-m", help="Extract and save metadata as _metadata.json file"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output with detailed logging information"
    ),
):
    """Download a full copy of public resource files from Yandex.Disk.

    This command downloads a single file or directory from a public Yandex.Disk resource.
    Single files are downloaded with their original format, while directories are downloaded
    as ZIP files containing all files inside.
    """
    setup_logging(verbose)
    if not validate_yandex_url(url):
        typer.echo(
            f"Invalid Yandex.Disk URL: {url}\n"
            "URL must be in format: https://disk.yandex.ru/d/... or https://disk.yandex.ru/i/...",
            err=True,
        )
        raise typer.Exit(1)
    try:
        acmd = Project()
        acmd.full(url, output, filename, metadata, verbose)
    except Exception as e:
        if verbose:
            logging.error(f"Error during full download: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command("sync")
def sync(
    url: str = typer.Argument(..., help="URL of the public Yandex.Disk resource to synchronize"),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help=(
            "Output path where synchronized files will be stored "
            "(defaults to resource ID if not specified)"
        ),
    ),
    update: bool = typer.Option(
        False, "--update", help="Update mode: only download files that do not already exist locally"
    ),
    nofiles: bool = typer.Option(
        False,
        "--nofiles",
        "-n",
        help="Metadata-only mode: collect and save metadata without downloading files",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output with detailed logging information"
    ),
):
    """Synchronize files and metadata from a public Yandex.Disk resource.

    This command recursively synchronizes files and metadata from a public Yandex.Disk
    directory resource to a local directory. It maintains the directory structure
    and saves metadata for each directory level.
    """
    setup_logging(verbose)
    if not validate_yandex_url(url):
        typer.echo(
            f"Invalid Yandex.Disk URL: {url}\n"
            "URL must be in format: https://disk.yandex.ru/d/... or https://disk.yandex.ru/i/...",
            err=True,
        )
        raise typer.Exit(1)
    if output is None:
        output = url.rsplit("/d/", 1)[-1] if "/d/" in url else url.rsplit("/i/", 1)[-1]
    try:
        acmd = Project()
        acmd.sync(url, output, update, nofiles, verbose)
    except Exception as e:
        if verbose:
            logging.error(f"Error during sync: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command("version")
def version():
    """Show version information."""
    typer.echo(f"ydiskarc {ydiskarc.__version__}")


def cli() -> None:
    """Main CLI entry point that shows help when no command is provided."""
    # Typer automatically shows help when no command is provided
    app()


if __name__ == "__main__":
    cli()
