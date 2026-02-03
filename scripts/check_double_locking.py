#!/usr/bin/env python3
"""
Double-Locking Anti-Pattern Detector

This script scans Python files for the dangerous double-locking pattern where
external code uses explicit locks (e.g., `with state._frame_lock:`) before
accessing StateService properties that already use internal locking.

This pattern causes deadlocks that freeze the entire application.

Usage:
    python scripts/check_double_locking.py web_interface.py
    python scripts/check_double_locking.py web_interface.py app/**/*.py
    python scripts/check_double_locking.py --all

Exit codes:
    0 - No issues found
    1 - Double-locking patterns detected
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple


def check_file(filepath: Path) -> List[Tuple[int, str]]:
    """
    Check file for double-locking anti-patterns.
    
    Args:
        filepath: Path to Python file to check
        
    Returns:
        List of (line_number, line_content) tuples for problematic lines
    """
    issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"⚠️  Warning: Could not read {filepath}: {e}", file=sys.stderr)
        return issues
    
    # Pattern to detect: with state._<something>_lock:
    # This is almost always wrong when used outside StateService class
    lock_pattern = re.compile(r'with\s+state\._\w+_lock:')
    
    for i, line in enumerate(lines, 1):
        if lock_pattern.search(line):
            issues.append((i, line.rstrip()))
    
    return issues


def is_state_service_file(filepath: Path) -> bool:
    """Check if file is the StateService implementation."""
    return filepath.name == 'state.py' and 'services' in filepath.parts


def main():
    parser = argparse.ArgumentParser(
        description='Detect double-locking anti-patterns in Python code'
    )
    parser.add_argument(
        'files',
        nargs='*',
        help='Python files to check (default: web_interface.py)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Check all Python files in project'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Also check StateService file (normally excluded)'
    )
    
    args = parser.parse_args()
    
    # Determine files to check
    if args.all:
        project_root = Path(__file__).parent.parent
        files_to_check = list(project_root.glob('**/*.py'))
        # Exclude test files and virtual environments
        files_to_check = [
            f for f in files_to_check
            if 'test' not in f.parts and 'venv' not in f.parts and '.venv' not in f.parts
        ]
    elif args.files:
        files_to_check = [Path(f) for f in args.files]
    else:
        # Default: check web_interface.py
        files_to_check = [Path('web_interface.py')]
    
    # Check each file
    all_issues = {}
    for filepath in files_to_check:
        if not filepath.exists():
            print(f"⚠️  Warning: File not found: {filepath}", file=sys.stderr)
            continue
        
        # Skip StateService file unless --strict mode
        if not args.strict and is_state_service_file(filepath):
            continue
        
        issues = check_file(filepath)
        if issues:
            all_issues[filepath] = issues
    
    # Report results
    if all_issues:
        print("❌ DOUBLE-LOCKING ANTI-PATTERNS DETECTED!\n")
        print("=" * 80)
        print("External code should NEVER use 'with state._lock:' before accessing")
        print("StateService properties. Properties handle locking internally.")
        print("=" * 80)
        print()
        
        total_issues = 0
        for filepath, issues in all_issues.items():
            print(f"\n📁 {filepath}:")
            for line_num, line_content in issues:
                print(f"  Line {line_num}: {line_content}")
                total_issues += 1
        
        print(f"\n❌ Found {total_issues} potential double-locking issue(s) in {len(all_issues)} file(s)!")
        print()
        print("Fix by removing the 'with state._lock:' wrapper:")
        print("  ❌ WRONG: with state._frame_lock: state.latest_frame = img")
        print("  ✅ RIGHT: state.latest_frame = img")
        print()
        print("See .agent-os/standards/best-practices.md for details.")
        
        sys.exit(1)
    else:
        print("✅ No double-locking issues found!")
        sys.exit(0)


if __name__ == '__main__':
    main()

