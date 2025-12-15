#!/usr/bin/env python
"""The main entry point. Invoke as `ydiskarc' or `python -m ydiskarc`."""
import sys

import typer


def main() -> None:
    """Main entry point with proper error handling.

    Shows help information when ydiskarc is started without any options.
    Typer automatically displays help when no command is provided.
    """
    try:
        from .core import app

        # Typer automatically shows help when no command is provided
        app()
    except KeyboardInterrupt:
        typer.echo("\nAborted by user", err=True)
        sys.exit(130)  # Standard exit code for Ctrl-C
    except typer.Exit as e:
        # Typer handles exit codes through typer.Exit exception
        sys.exit(e.exit_code)
    except SystemExit:
        # Re-raise SystemExit to preserve exit codes
        raise
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
