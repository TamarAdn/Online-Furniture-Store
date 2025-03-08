#!/usr/bin/env python3
"""
Script to run pre-commit hooks on individual files with backup functionality.
Simplified to work with black, isort, and flake8.
"""
import argparse
import os
import shutil
import subprocess
import sys
from typing import List, Optional


def get_python_files(directory: str = ".") -> List[str]:
    """Get all Python files in the given directory and subdirectories."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                python_files.append(filepath)
    return python_files


def backup_file(filename: str) -> str:
    """Create a backup of the file before modifying it."""
    backup_filename = f"{filename}.bak"
    shutil.copy2(filename, backup_filename)
    print(f"Created backup: {backup_filename}")
    return backup_filename


def run_precommit_on_file(filename: str, hook_id: Optional[str] = None) -> bool:
    """
    Run pre-commit hooks on a single file.
    """
    cmd = ["pre-commit", "run", "--files", filename]
    if hook_id:
        cmd.insert(2, hook_id)

    print(f"\n{'=' * 80}")
    print(f"Running pre-commit on: {filename}")
    print(f"{'=' * 80}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Print the output
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    return result.returncode == 0


def run_specific_tool(filename: str, tool: str) -> bool:
    """
    Run a specific formatting tool directly instead of through pre-commit.
    Useful for targeted fixes.
    """
    commands = {
        "black": ["black", filename],
        "isort": ["isort", filename],
        "flake8": ["flake8", filename],
    }

    if tool not in commands:
        print(f"Unknown tool: {tool}. Available tools: black, isort, flake8")
        return False

    print(f"\nRunning {tool} on {filename}...")
    result = subprocess.run(commands[tool], capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    return result.returncode == 0


def main() -> None:
    """Main function to run the script."""
    parser = argparse.ArgumentParser(
        description="Run pre-commit hooks on individual files with backup functionality"
    )
    parser.add_argument(
        "files", nargs="*", help="Specific files to process (default: all Python files)"
    )
    parser.add_argument("--hook", help="Specific hook ID to run (default: all hooks)")
    parser.add_argument(
        "--tool",
        choices=["black", "isort", "flake8"],
        help="Run a specific tool directly (bypasses pre-commit)",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Interactive mode - process one file at a time",
    )
    parser.add_argument(
        "--no-backup", action="store_true", help="Skip creating backup files"
    )

    args = parser.parse_args()

    # Get files to process - either specified files or all Python files
    files = args.files if args.files else get_python_files()

    if not files:
        print("No Python files found to process.")
        return

    print(f"Found {len(files)} files to process.")

    for file in files:
        if not os.path.isfile(file):
            print(f"Warning: File not found: {file}")
            continue

        # Create backup unless disabled
        backup = None
        if not args.no_backup:
            backup = backup_file(file)

        if args.interactive:
            while True:
                if args.tool:
                    success = run_specific_tool(file, args.tool)
                else:
                    success = run_precommit_on_file(file, args.hook)

                if success:
                    print(f"All checks passed for: {file}")
                    break
                else:
                    print(f"Some checks failed for: {file}")

                    choice = input(
                        "\nPlease fix the issues manually and then:\n"
                        "[r] - Re-check this file\n"
                        "[s] - Skip to next file\n"
                        "[q] - Quit\n"
                        "[u] - Undo changes (restore backup)\n"
                        "[b] - Run black\n"
                        "[i] - Run isort\n"
                        "[f] - Run flake8\n"
                        "Enter choice [r/s/q/u/b/i/f]: "
                    ).lower()

                    if choice == "q":
                        return
                    elif choice == "s":
                        break
                    elif choice == "u" and backup:
                        shutil.copy2(backup, file)
                        print(f"Restored {file} from backup")
                    elif choice == "b":
                        run_specific_tool(file, "black")
                    elif choice == "i":
                        run_specific_tool(file, "isort")
                    elif choice == "f":
                        run_specific_tool(file, "flake8")
                    # Default is to re-check (for 'r' or any other input)
        else:
            if args.tool:
                success = run_specific_tool(file, args.tool)
            else:
                success = run_precommit_on_file(file, args.hook)

            if success:
                print(f"All checks passed for: {file}")
            else:
                print(f"Some checks failed for: {file}")
                if backup:
                    print(f"You can restore from backup: {backup}")


if __name__ == "__main__":
    main()
