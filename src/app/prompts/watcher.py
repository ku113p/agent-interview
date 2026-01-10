import argparse
import sys
import time
from pathlib import Path
from typing import NoReturn

from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError

# Default prompts directory
PROMPTS_DIR = Path(__file__).parent


def check_templates(directory: Path, verbose: bool = False) -> bool:
    """
    Scans the directory for .j2 files and validates their syntax.
    Returns True if all templates are valid, False otherwise.
    """
    env = Environment(loader=FileSystemLoader(str(directory)))

    # Get all .j2 files
    templates = list(directory.glob("**/*.j2"))
    if verbose:
        print(f"Checking {len(templates)} templates in {directory}...")

    has_errors = False

    for template_path in templates:
        rel_path = template_path.relative_to(directory)
        try:
            # We use env.loader.load to actually parse the template
            # which triggers syntax validation
            if env.loader:
                env.loader.load(env, str(rel_path))
            if verbose:
                print(f"✅ {rel_path}")
        except TemplateSyntaxError as e:
            has_errors = True
            print(f"❌ {rel_path}: {e.message}")
            print(f"   Line {e.lineno}: {e.source if e.source else 'Unknown source'}")
        except Exception as e:
            has_errors = True
            print(f"❌ {rel_path}: Unexpected error - {e}")

    return not has_errors


def watch_templates(directory: Path) -> NoReturn:
    """
    Continuously monitors templates for changes and validates them.
    """
    print(f"👀 Watching templates in {directory}...")
    print("Press Ctrl+C to stop.")

    # Simple polling mechanism
    last_mtimes: dict[Path, float] = {}

    try:
        while True:
            _check_cycle(directory, last_mtimes)
            time.sleep(1.0)

    except KeyboardInterrupt:
        print("\nStopping watcher.")
        sys.exit(0)


def _check_cycle(directory: Path, last_mtimes: dict[Path, float]) -> None:
    templates = list(directory.glob("**/*.j2"))

    for template_path in templates:
        mtime = template_path.stat().st_mtime
        if template_path not in last_mtimes or mtime > last_mtimes[template_path]:
            # File changed or new file
            last_mtimes[template_path] = mtime
            _validate_and_report(template_path, directory)


def _validate_and_report(template_path: Path, directory: Path) -> None:
    rel_path = template_path.relative_to(directory)
    timestamp = time.strftime("%H:%M:%S")

    try:
        # Validate single file
        env = Environment(loader=FileSystemLoader(str(directory)))
        if env.loader:
            env.loader.load(env, str(rel_path))
        print(f"[{timestamp}] ✅ {rel_path} valid")
    except TemplateSyntaxError as e:
        print(f"[{timestamp}] ❌ {rel_path}: {e.message} (Line {e.lineno})")
    except Exception as e:
        print(f"[{timestamp}] ❌ {rel_path}: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage and validate Jinja2 prompts.")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # 'check' command
    check_parser = subparsers.add_parser("check", help="Validate all templates once")
    check_parser.add_argument(
        "--dir", type=Path, default=PROMPTS_DIR, help="Directory to check"
    )
    check_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show all files"
    )

    # 'watch' command
    watch_parser = subparsers.add_parser("watch", help="Watch templates for changes")
    watch_parser.add_argument(
        "--dir", type=Path, default=PROMPTS_DIR, help="Directory to watch"
    )

    args = parser.parse_args()

    if args.command == "check":
        success = check_templates(args.dir, args.verbose)
        sys.exit(0 if success else 1)
    elif args.command == "watch":
        watch_templates(args.dir)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
