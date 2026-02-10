"""Interactive initialization for Sine configuration.

Provides ESLint-style project setup with auto-detection and user prompts.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import click

from sine.rules_loader import get_built_in_rules_path


def detect_project_type() -> dict[str, bool]:
    """Auto-detect project characteristics from current directory.

    Returns:
        Dictionary with boolean flags for detected project types:
        - python: Has pyproject.toml or setup.py
        - javascript: Has package.json
        - typescript: Has tsconfig.json
        - git: Has .git directory
    """
    cwd = Path.cwd()

    return {
        "python": (cwd / "pyproject.toml").exists() or (cwd / "setup.py").exists(),
        "javascript": (cwd / "package.json").exists(),
        "typescript": (cwd / "tsconfig.json").exists(),
        "git": (cwd / ".git").exists(),
    }


def prompt_user_config(project_info: dict[str, bool]) -> dict:
    """Interactively prompt user for configuration preferences.

    Args:
        project_info: Detected project characteristics

    Returns:
        Dictionary with user configuration choices:
        - config_file: "pyproject.toml" or "sine.toml"
        - target: List of directories to analyze
        - format: Output format ("text", "json", "sarif")
    """
    config = {}

    # Ask about config file location
    if project_info["python"]:
        use_pyproject = click.confirm("Use pyproject.toml for configuration?", default=True)
        config["config_file"] = "pyproject.toml" if use_pyproject else "sine.toml"
    else:
        config["config_file"] = "sine.toml"

    # Ask about target directories
    default_target = "src" if (Path.cwd() / "src").exists() else "."
    target = click.prompt(
        "Which directories should Sine analyze?",
        default=default_target,
        type=str,
    )
    config["target"] = [t.strip() for t in target.split(",")]

    # Ask about format
    config["format"] = click.prompt(
        "Default output format?",
        type=click.Choice(["text", "json", "sarif"]),
        default="text",
    )

    return config


def generate_config_content(config: dict, rules_dir: Path) -> str:
    """Generate TOML configuration content.

    Args:
        config: User configuration dictionary
        rules_dir: Path to rules directory

    Returns:
        TOML configuration string
    """
    prefix = "[tool.sine]\n" if config["config_file"] == "pyproject.toml" else ""

    target_str = ", ".join([f'"{t}"' for t in config["target"]])

    return f"""{prefix}rules_dir = "{rules_dir}"
target = [{target_str}]
format = "{config["format"]}"
"""


def copy_built_in_rules_to_local(rules_dir: Path, selected_ids: list[str] | None = None) -> None:
    """Copy built-in rules to local directory.

    Args:
        rules_dir: Destination directory for rules
        selected_ids: If provided, only copy rules with these IDs
                     (e.g., ["ARCH-001", "ARCH-003"])
    """
    built_in_path = get_built_in_rules_path()

    rules_dir.mkdir(parents=True, exist_ok=True)

    for rule_file in built_in_path.glob("*.yaml"):
        if selected_ids:
            # Extract ID from filename (e.g., "ARCH-001.yaml" -> "ARCH-001")
            rule_id = rule_file.stem
            if rule_id not in selected_ids:
                continue

        dest = rules_dir / rule_file.name
        shutil.copy2(rule_file, dest)
        click.echo(f"  Copied {rule_file.name}")


def run_init(
    rules_dir: Path,
    copy_built_in_rules: bool,
    interactive: bool = True,
) -> None:
    """Run the initialization workflow.

    Args:
        rules_dir: Directory for local rules
        copy_built_in_rules: Whether to copy built-in rules to local directory
        interactive: Whether to prompt user for choices (vs using defaults)
    """
    click.echo("Initializing Sine for your project...\n")

    # Detect project type
    project_info = detect_project_type()

    if interactive:
        click.echo("Detected project characteristics:")
        for key, value in project_info.items():
            click.echo(f"  {key}: {value}")
        click.echo()

    # Get user configuration
    if interactive:
        config = prompt_user_config(project_info)
    else:
        # Non-interactive defaults
        config = {
            "config_file": "pyproject.toml" if project_info["python"] else "sine.toml",
            "target": ["."],
            "format": "text",
        }

    config_file = Path.cwd() / config["config_file"]

    # Check if config already exists
    if config["config_file"] == "sine.toml" and config_file.exists():
        if interactive:
            if not click.confirm(f"{config['config_file']} already exists. Overwrite?"):
                click.echo("Initialization cancelled.")
                sys.exit(0)
        else:
            click.echo(
                f"Error: {config['config_file']} already exists. "
                "Remove it first or run interactively.",
                err=True,
            )
            sys.exit(1)

    # Write configuration
    config_content = generate_config_content(config, rules_dir)

    if config["config_file"] == "pyproject.toml" and config_file.exists():
        # Append to existing pyproject.toml
        with config_file.open("a") as f:
            f.write("\n" + config_content)
        click.echo(f"✓ Added [tool.sine] section to {config['config_file']}")
    else:
        # Create new file
        with config_file.open("w") as f:
            f.write(config_content)
        click.echo(f"✓ Created {config['config_file']}")

    # Handle rules directory
    if copy_built_in_rules:
        if interactive:
            click.echo("\nAvailable built-in rules:")
            click.echo("  ARCH-001: HTTP resilience wrappers")
            click.echo("  ARCH-003: Logging best practices")
            click.echo("  PATTERN-DISC-006: Adapter pattern")
            click.echo("  PATTERN-DISC-010: Pipeline pattern")
            click.echo("  PATTERN-DISC-011: Dependency Injection")
            click.echo("  PATTERN-DISC-012: Context managers")
            click.echo("  PATTERN-DISC-015: Exception hierarchy")

            copy_all = click.confirm("\nCopy all built-in rules?", default=True)

            if copy_all:
                copy_built_in_rules_to_local(rules_dir)
            else:
                # TODO: Allow selecting specific rules
                click.echo("Selective rule copying not yet implemented. Copying all.")
                copy_built_in_rules_to_local(rules_dir)
        else:
            copy_built_in_rules_to_local(rules_dir)

        click.echo(f"✓ Copied built-in rules to {rules_dir}")
    else:
        # Just create the directory
        rules_dir.mkdir(parents=True, exist_ok=True)
        click.echo(f"✓ Created {rules_dir} directory")

    # Final instructions
    click.echo("\n" + "=" * 50)
    click.echo("Sine initialization complete!")
    click.echo("=" * 50)
    click.echo("\nNext steps:")
    click.echo("  1. Review the configuration in " + config["config_file"])
    if not copy_built_in_rules:
        click.echo(f"  2. Add custom rules to {rules_dir}/")
        click.echo("     (Built-in rules are always available automatically)")
    click.echo("  3. Run 'sine check' to start enforcing patterns")
    click.echo("\nFor more info: https://github.com/coreyt/sine")
