"""Command-Line Interface using Click.

Main CLI commands for OpenDental Audit Data Retrieval.
"""

import sys
from pathlib import Path

import click
from keyring.errors import NoKeyringError
from pydantic import ValidationError
from rich.console import Console
from rich.prompt import Confirm, Prompt

from opendental_cli.audit_logger import configure_audit_logging
from opendental_cli.credential_manager import (
    CredentialNotFoundError,
    check_credentials_exist,
    get_credentials,
    set_credentials,
)
from opendental_cli.models.credential import APICredential

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--patnum", type=int, help="Patient Number (required for retrieval)")
@click.option("--aptnum", type=int, help="Appointment Number (required for retrieval)")
@click.option("--output", type=click.Path(), help="Output file path (default: stdout)")
@click.option("--redact-phi", is_flag=True, help="Redact PHI in output")
@click.option("--force", is_flag=True, help="Skip overwrite confirmation")
def main(ctx: click.Context, patnum: int, aptnum: int, output: str, redact_phi: bool, force: bool):
    """OpenDental Audit Data Retrieval CLI.

    Retrieve audit data from OpenDental API endpoints for compliance reporting.

    \b
    Examples:
        # Retrieve data to stdout
        opendental-cli --patnum 12345 --aptnum 67890

        # Save to file
        opendental-cli --patnum 12345 --aptnum 67890 --output audit.json

        # Redact PHI for debugging
        opendental-cli --patnum 12345 --aptnum 67890 --redact-phi
    """
    # Configure audit logging
    configure_audit_logging()

    # If subcommand invoked, let it handle execution
    if ctx.invoked_subcommand is not None:
        return

    # Main retrieval command requires patnum and aptnum
    if patnum is None or aptnum is None:
        console.print("[red]Error: --patnum and --aptnum are required[/red]")
        console.print("\nRun [cyan]opendental-cli --help[/cyan] for usage information")
        sys.exit(1)

    # Validate patnum and aptnum are positive
    if patnum <= 0 or aptnum <= 0:
        console.print("[red]Error: PatNum and AptNum must be positive integers[/red]")
        sys.exit(1)

    # Get credentials
    try:
        credentials = get_credentials()
    except CredentialNotFoundError as e:
        console.print(f"[red]Error: {str(e)}[/red]\n")
        console.print("Please configure credentials first:")
        console.print("[cyan]opendental-cli config set-credentials[/cyan]\n")
        console.print("Or set environment variables:")
        console.print("  [cyan]OPENDENTAL_BASE_URL[/cyan]")
        console.print("  [cyan]OPENDENTAL_DEVELOPER_KEY[/cyan]")
        console.print("  [cyan]OPENDENTAL_CUSTOMER_KEY[/cyan]")
        sys.exit(1)

    # Import here to avoid circular dependency
    import asyncio

    from opendental_cli.models.request import AuditDataRequest
    from opendental_cli.orchestrator import orchestrate_retrieval
    from opendental_cli.output_formatter import write_to_file, write_to_stdout

    # Create request object
    request = AuditDataRequest(
        patnum=patnum,
        aptnum=aptnum,
        output_file=output,
        redact_phi=redact_phi,
        force_overwrite=force,
    )

    # Execute orchestration
    try:
        console.print("[cyan]Fetching audit data...[/cyan]")
        consolidated = asyncio.run(orchestrate_retrieval(request, credentials))

        # Apply PHI redaction if requested
        if redact_phi:
            consolidated = consolidated.apply_phi_redaction()

        # Write output
        if output:
            write_to_file(consolidated, output, force)
        else:
            write_to_stdout(consolidated)

        # Exit with appropriate code
        exit_code = consolidated.exit_code()
        if exit_code == 1:
            console.print("\n[red]✗ All endpoints failed[/red]")
        elif exit_code == 2:
            console.print("\n[yellow]⚠ Partial success (some endpoints failed)[/yellow]")
        else:
            console.print("\n[green]✓ All endpoints succeeded[/green]")

        sys.exit(exit_code)

    except Exception as e:
        console.print(f"[red]✗ Unexpected error: {str(e)}[/red]")
        sys.exit(1)


@main.group()
def config():
    """Configuration management commands."""
    pass


@config.command("set-credentials")
@click.option(
    "--environment",
    type=click.Choice(["production", "staging", "dev"]),
    default="production",
    help="Environment name",
)
def set_credentials_cmd(environment: str):
    """Configure OpenDental API credentials.

    Stores credentials in OS keyring (Windows Credential Manager,
    macOS Keychain, or Linux Secret Service).

    \b
    Examples:
        opendental-cli config set-credentials
        opendental-cli config set-credentials --environment staging
    """
    console.print("[bold]OpenDental API Credential Configuration[/bold]\n")

    # Check if credentials already exist
    if check_credentials_exist(environment):
        console.print(f"[yellow]Credentials already configured for '{environment}' environment.[/yellow]")
        overwrite = Confirm.ask("Overwrite existing credentials?", default=False)
        if not overwrite:
            console.print("[yellow]Operation cancelled.[/yellow]")
            return

    # Prompt for base URL
    base_url = Prompt.ask(
        "\n[cyan]Enter OpenDental API Base URL[/cyan]",
        default="https://example.opendental.com/api/v1",
    )

    # Validate base_url format
    try:
        # Use Pydantic to validate URL
        test_cred = APICredential(
            base_url=base_url,
            developer_key="test",
            customer_key="test",
            environment=environment
        )
    except ValidationError as e:
        console.print(f"[red]Invalid URL format: {e.errors()[0]['msg']}[/red]")
        sys.exit(1)

    # Prompt for Developer Key (hidden input)
    developer_key = Prompt.ask(
        "[cyan]Enter Developer Key[/cyan]",
        password=True,
    )

    if not developer_key:
        console.print("[red]Developer Key cannot be empty[/red]")
        sys.exit(1)

    # Prompt for Developer Portal Key (hidden input)
    # Note: This is the second part of the ODFHIR authorization format
    customer_key = Prompt.ask(
        "[cyan]Enter Developer Portal Key[/cyan]",
        password=True,
    )

    if not customer_key:
        console.print("[red]Developer Portal Key cannot be empty[/red]")
        sys.exit(1)
    
    # Store credentials
    try:
        set_credentials(base_url, developer_key, customer_key, environment)
        console.print(f"\n[green]✓ Credentials stored successfully in OS keyring[/green]")
        console.print(f"[green]  Environment: {environment}[/green]")
        console.print(f"[green]  Base URL: {base_url}[/green]")
        console.print("\n[cyan]You can now run:[/cyan]")
        console.print("  [cyan]opendental-cli --patnum 12345 --aptnum 67890[/cyan]")
    except NoKeyringError as e:
        console.print(f"\n[red]Error: OS keyring is not available[/red]")
        console.print(f"[red]{str(e)}[/red]\n")
        console.print("[yellow]Fallback option:[/yellow]")
        console.print("Set environment variables instead:")
        console.print(f"  [cyan]export OPENDENTAL_BASE_URL=\"{base_url}\"[/cyan]")
        console.print(f"  [cyan]export OPENDENTAL_DEVELOPER_KEY=\"your-developer-key\"[/cyan]")
        console.print(f"  [cyan]export OPENDENTAL_CUSTOMER_KEY=\"your-customer-key\"[/cyan]")
        console.print(f"  [cyan]export OPENDENTAL_ENVIRONMENT=\"{environment}\"[/cyan]")
        console.print("\n[yellow]⚠ Warning: Environment variables are less secure than keyring storage[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error storing credentials: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
