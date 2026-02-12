#!/usr/bin/env python3
"""Validate CIDR format and detect duplicates in IP block lists."""

import argparse
import ipaddress
import sys
from pathlib import Path


def validate_cidr(line: str) -> tuple[bool, str | None]:
    """Validate a single CIDR line.

    Returns:
        Tuple of (is_valid, error_message)
    """
    line = line.strip()

    # Skip empty lines and comments
    if not line or line.startswith('#'):
        return True, None

    try:
        network = ipaddress.ip_network(line, strict=False)
        if network.version != 4:
            return False, f"IPv6 not supported: {line}"
        return True, None
    except ValueError as e:
        return False, str(e)


def validate_file(filepath: Path) -> dict:
    """Validate a single file.

    Returns:
        Dictionary with validation results
    """
    results = {
        'file': str(filepath),
        'total_lines': 0,
        'valid_cidrs': 0,
        'invalid_cidrs': 0,
        'duplicates': 0,
        'errors': [],
        'duplicate_entries': set(),
    }

    seen_cidrs = set()

    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            results['total_lines'] += 1
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                continue

            is_valid, error = validate_cidr(stripped)

            if not is_valid:
                results['invalid_cidrs'] += 1
                results['errors'].append({
                    'line': line_num,
                    'content': stripped,
                    'error': error
                })
            else:
                # Normalize CIDR for duplicate detection
                try:
                    normalized = str(ipaddress.ip_network(stripped, strict=False))
                    if normalized in seen_cidrs:
                        results['duplicates'] += 1
                        results['duplicate_entries'].add(normalized)
                    else:
                        seen_cidrs.add(normalized)
                        results['valid_cidrs'] += 1
                except ValueError:
                    pass  # Already handled above

    results['duplicate_entries'] = sorted(results['duplicate_entries'])
    return results


def print_results(results: dict, verbose: bool = False) -> None:
    """Print validation results for a single file."""
    print(f"\n{results['file']}")
    print("-" * len(results['file']))
    print(f"  Total lines:    {results['total_lines']}")
    print(f"  Valid CIDRs:    {results['valid_cidrs']}")
    print(f"  Invalid CIDRs:  {results['invalid_cidrs']}")
    print(f"  Duplicates:     {results['duplicates']}")

    if results['errors']:
        print("\n  Errors:")
        for error in results['errors'][:10]:  # Limit output
            print(f"    Line {error['line']}: {error['content']} - {error['error']}")
        if len(results['errors']) > 10:
            print(f"    ... and {len(results['errors']) - 10} more errors")

    if verbose and results['duplicate_entries']:
        print("\n  Duplicates found:")
        for dup in results['duplicate_entries'][:10]:  # Limit output
            print(f"    {dup}")
        if len(results['duplicate_entries']) > 10:
            print(f"    ... and {len(results['duplicate_entries']) - 10} more")


def main():
    parser = argparse.ArgumentParser(
        description='Validate CIDR format in IP block lists'
    )
    parser.add_argument(
        'paths',
        nargs='+',
        type=Path,
        help='Files or directories to validate'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show duplicate entries'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Only show errors'
    )

    args = parser.parse_args()

    # Collect all files to validate
    files = []
    for path in args.paths:
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(path.glob('*.txt'))
        else:
            print(f"Warning: {path} does not exist", file=sys.stderr)

    if not files:
        print("No files to validate", file=sys.stderr)
        sys.exit(1)

    # Validate all files
    all_results = []
    total_errors = 0

    for filepath in sorted(files):
        results = validate_file(filepath)
        all_results.append(results)
        total_errors += results['invalid_cidrs']

        if not args.quiet:
            print_results(results, args.verbose)

    # Summary
    if not args.quiet and len(all_results) > 1:
        print("\n" + "=" * 50)
        print("Summary")
        print("=" * 50)
        print(f"Files validated: {len(all_results)}")
        total_cidrs = sum(r['valid_cidrs'] for r in all_results)
        total_dups = sum(r['duplicates'] for r in all_results)
        print(f"Total valid CIDRs: {total_cidrs}")
        print(f"Total errors: {total_errors}")
        print(f"Total duplicates: {total_dups}")

    # Exit with error code if any invalid CIDRs found
    sys.exit(1 if total_errors > 0 else 0)


if __name__ == '__main__':
    main()
