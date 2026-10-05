#!/usr/bin/env python
# -*- coding: utf8 -*-
import logging
from typing import Optional

import typer

import ydiskarc

from .client import YandexDiskClient
from .cmds.processor import Project

# Create Typer app
app = typer.Typer(
    name="ydiskarc",
    help="A command-line tool to backup public resources from Yandex.Disk",
    add_completion=False,
)


PACKAGE_LOGGER_NAME = "ydiskarc"
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging(verbose: bool = False) -> None:
    """Setup ydiskarc-package logging.

    Configures the ``ydiskarc`` package logger only — never the root logger —
    so third-party libraries (urllib3, requests, tqdm, etc.) keep their own
    handlers and levels. Calling this function never invokes
    ``logging.basicConfig`` or ``logging.disable``; those are process-global
    side-effects that should be left to the application embedder.

    Args:
        verbose: If True, attach a ``StreamHandler`` at ``DEBUG`` level so the
            user sees every log record emitted from ``ydiskarc.*``. If False,
            the package logger emits nothing (records below ``WARNING`` are
            dropped; ``WARNING``+ propagate to the root handler if any).
    """
    logger = logging.getLogger(PACKAGE_LOGGER_NAME)

    # Drop any handlers we previously attached so re-invocation is idempotent.
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    if verbose:
        logger.setLevel(logging.DEBUG)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        logger.addHandler(stream_handler)
        # Make sure propagation doesn't double-emit when the root logger is
        # already configured with its own handler.
        logger.propagate = False
    else:
        logger.setLevel(logging.WARNING)
        # Keep propagation on so warnings still surface if the embedder
        # configured the root logger; ensure no ydiskarc-owned handler is left.
        logger.propagate = True


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
    if not YandexDiskClient.validate_yandex_url(url):
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
    parallel: int = typer.Option(
        1,
        "--parallel",
        "-p",
        min=1,
        help="Number of concurrent file downloads (default: 1 — sequential)",
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
    if not YandexDiskClient.validate_yandex_url(url):
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
        acmd.sync(url, output, update, nofiles, verbose, parallel=parallel)
    except Exception as e:
        if verbose:
            logging.error(f"Error during sync: {e}")
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command("version")
def version():
    """Show version information."""
    typer.echo(f"ydiskarc {ydiskarc.__version__}")


@app.command("configure")
def configure(
    key: str = typer.Option(..., "--key", "-k", help="Yandex OAuth token to store in .ydiskarc"),
    projectdir: Optional[str] = typer.Option(
        None,
        "--projectdir",
        "-p",
        help="Directory in which to write .ydiskarc (defaults to the current directory)",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
):
    """Persist a Yandex OAuth key to ``.ydiskarc`` with restricted permissions.

    The resulting ``.ydiskarc`` file is created with mode ``0o600`` (POSIX) so
    the OAuth token is not world-readable. Any existing fields in the file
    are preserved.
    """
    setup_logging(verbose)
    try:
        Project().configure(key=key, projectdir=projectdir)
        typer.echo("Configuration saved.")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


def cli() -> None:
    """Main CLI entry point that shows help when no command is provided."""
    # Typer automatically shows help when no command is provided
    app()


if __name__ == "__main__":
    cli()
