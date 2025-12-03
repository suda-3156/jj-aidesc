from pathlib import Path

import click
from rich.console import Console
from rich.padding import Padding

from jj_aidesc import __version__
from jj_aidesc.ai import AI
from jj_aidesc.config import CONFIG_TEMPLATE, Config
from jj_aidesc.editor import Editor
from jj_aidesc.error import AbortError, error_handle
from jj_aidesc.jj import JJClient
from jj_aidesc.logging import setup_logging
from jj_aidesc.prompts import PROMPTS, PROMPTS_DESCRIPTION
from jj_aidesc.provider import get_provider
from jj_aidesc.spinner import get_spinner

console = Console(highlight=False)


@click.group(invoke_without_command=True)
@click.version_option(__version__, "-v", "--version", prog_name="jj-aidesc")
@click.help_option("-h", "--help")
@click.pass_context
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
@click.option(
    "--model",
    "-m",
    type=str,
    help="Model name (default: gemini-2.0-flash)",
)
@click.option(
    "--temperature",
    "-t",
    type=float,
    help="Temperature for AI generation (default: 0.0)",
)
@click.option(
    "--api-key",
    type=str,
    help="Google GenAI API key (overrides env/file)",
)
@click.option(
    "--config",
    "-c",
    "config_path",
    type=click.Path(exists=True, dir_okay=False),
    help="Path to configuration file",
)
@click.option(
    "--language",
    "-l",
    type=str,
    help="Language for the commit message (default: English)",
)
@click.option(
    "--style",
    "-s",
    type=click.Choice(["conventional", "follow", "simple"]),
    help="Description style (default: conventional)",
)
@click.option(
    "--apply",
    "-a",
    is_flag=True,
    help="Apply all descriptions without confirmation",
)
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    help="Generate descriptions but don't apply",
)
@click.option(
    "--revisions",
    "-r",
    default="mutable()",
    help="Target revset (default: mutable())",
)
@error_handle
def main(
    ctx: click.Context,
    verbose: bool,
    model: str | None,
    temperature: float | None,
    api_key: str | None,
    config_path: str | None,
    language: str | None,
    style: str | None,
    apply: bool,
    dry_run: bool,
    revisions: str,
) -> None:
    """Generate AI-powered descriptions for jj commits without description."""
    if ctx.invoked_subcommand is not None:
        return

    setup_logging(verbose)
    Spinner = get_spinner(verbose)

    # Initialize JJ client and check repository
    jj = JJClient()
    if not jj.check_jj_available():
        console.print("[bold red]Error:[/bold red] jj is not installed or not in PATH")
        raise SystemExit(1)

    if not jj.is_in_repo():
        console.print("[bold red]Error:[/bold red] Not in a jj repository")
        raise SystemExit(1)

    # Initialize configuration
    config = Config(
        _model=model,
        _temperature=temperature,
        _api_key=api_key,
        _config_path=config_path,
        _language=language,
        _style=style,
    )

    # Get provider and AI
    provider = get_provider(config)

    # Get existing descriptions for 'follow' style
    existing_descriptions: list[str] | None = None
    if config.style == "follow":
        existing_descriptions = jj.get_existing_descriptions(revisions)

    # Get system prompt
    system_prompt = PROMPTS[config.style]

    ai = AI(
        model=provider.chat_model,
        system_prompt=system_prompt,
        language=config.language,
    )

    editor = Editor()

    # Display configuration
    _display_config(config, provider)

    # Find commits without description
    with Spinner(text="Scanning for commits without description...") as spinner:
        commits = jj.get_commits_without_description(revisions)
        if not commits:
            spinner.succeed("No commits without description found")
            return
        spinner.succeed(f"Found {len(commits)} commit(s)")

    console.print()
    for i, commit in enumerate(commits, 1):
        files_display = ", ".join(commit.files[:3])
        if len(commit.files) > 3:
            files_display += f" (+{len(commit.files) - 3} more)"
        console.print(f"  [{i}] {commit.change_id}  {files_display}")

    console.print()

    # Generate descriptions
    applied_count = 0
    quit_requested = False
    for i, commit in enumerate(commits, 1):
        if quit_requested:
            break

        console.print(f"[bold][{i}/{len(commits)}] {commit.change_id}[/bold]")

        # Reset AI conversation history for each new commit
        ai.reset_history()

        # Get diff
        with Spinner(text="  Getting diff...") as spinner:
            diff = jj.get_diff(commit.change_id)
            spinner.succeed("  Got diff")

        # Generation loop (supports regeneration with feedback)
        description = _generation_loop(
            ai=ai,
            diff=diff,
            existing_descriptions=existing_descriptions,
            jj=jj,
            editor=editor,
            commit=commit,
            dry_run=dry_run,
            apply=apply,
            Spinner=Spinner,
        )

        if description is None:
            # Quit was requested
            quit_requested = True
            console.print("  [yellow]Quit[/yellow]")
        elif description:
            applied_count += 1

        console.print()

    # Summary
    if dry_run:
        console.print(
            f"[bold]Done![/bold] {len(commits)} description(s) generated (dry-run)"
        )
    else:
        console.print(f"[bold]Done![/bold] {applied_count} commit(s) updated.")


@main.command()
@click.help_option("-h", "--help")
@click.option(
    "--config",
    "-c",
    "config_path",
    type=click.Path(dir_okay=False),
    default=".jj-aidesc.yaml",
    help="Path to generate the configuration file (default: .jj-aidesc.yaml)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite existing configuration file",
)
def init(config_path: str, force: bool) -> None:
    """Generate a configuration file template."""
    path = Path(config_path)

    if path.exists() and not force:
        console.print(
            f"[yellow]Warning:[/yellow] {config_path} already exists. "
            "Use --force to overwrite."
        )
        return

    path.write_text(CONFIG_TEMPLATE)
    console.print(f"[green]Created:[/green] {config_path}")


def _display_config(config: Config, provider) -> None:
    console.print()
    prompt_display = f"{PROMPTS_DESCRIPTION[config.style]} ({config.style})"
    console.print(
        f"[dim]Provider:[/dim] {provider.name}  "
        f"[dim]Model:[/dim] {provider.model_name}  "
        f"[dim]Temperature:[/dim] {config.temperature}"
    )
    console.print(
        f"[dim]Style:[/dim] {prompt_display}  [dim]Language:[/dim] {config.language}"
    )
    console.print()


def _generation_loop(
    ai: AI,
    diff: str,
    existing_descriptions: list[str] | None,
    jj: JJClient,
    editor: Editor,
    commit,
    dry_run: bool,
    apply: bool,
    Spinner,
) -> bool | None:
    """
    Generate description with optional regeneration loop.

    Returns:
        True if description was applied
        False if skipped
        None if quit was requested
    """
    feedback: str | None = None

    while True:
        # Generate description
        if feedback:
            with Spinner(text="  Regenerating description...") as spinner:
                description = ai.generate(
                    diff, existing_descriptions, feedback=feedback
                )
                spinner.succeed("  Regenerated description")
        else:
            with Spinner(text="  Generating description...") as spinner:
                description = ai.generate(diff, existing_descriptions)
                spinner.succeed("  Generated description")

        # Display description
        console.print("  ────────────────────────────────")
        console.print(Padding(description, (0, 0, 0, 4)))
        console.print("  ────────────────────────────────")

        if dry_run:
            console.print("  [dim](dry-run, not applied)[/dim]")
            return False

        if apply:
            # Apply without confirmation
            jj.set_description(description, commit.change_id)
            console.print("  [green]✓ Applied[/green]")
            return True

        # Ask for confirmation
        action = _prompt_action()
        if action == "y":
            jj.set_description(description, commit.change_id)
            console.print("  [green]✓ Applied[/green]")
            return True
        elif action == "e":
            try:
                edited = editor.edit(description)
                jj.set_description(edited, commit.change_id)
                console.print("  [green]✓ Applied (edited)[/green]")
                return True
            except AbortError:
                console.print("  [yellow]Skipped[/yellow]")
                return False
        elif action == "r":
            feedback = _prompt_feedback()
            if not feedback:
                console.print("  [yellow]Regeneration cancelled[/yellow]")
                continue
            # Loop will continue with regeneration
        elif action == "n":
            console.print("  [yellow]Skipped[/yellow]")
            return False
        elif action == "q":
            return None


def _prompt_action() -> str:
    console.print("  [dim]y: Apply / n: Skip / e: Edit / r: Regenerate / q: Quit[/dim]")

    while True:
        try:
            choice = click.prompt(
                "  Apply?",
                type=click.Choice(["y", "n", "e", "r", "q"], case_sensitive=False),
                default="y",
                show_choices=False,
                show_default=False,
            )
            return choice.lower()
        except click.Abort:
            return "q"


def _prompt_feedback() -> str:
    console.print("  [dim]Enter feedback for regeneration (or empty to cancel):[/dim]")
    try:
        feedback = click.prompt("  Feedback", default="", show_default=False)
        return feedback.strip()
    except click.Abort:
        return ""


if __name__ == "__main__":
    main()
