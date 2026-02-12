#!/usr/bin/env python3
"""Split large CIDR files into chunks for Microsoft Entra Named Location limits."""

import argparse
import sys
from pathlib import Path


DEFAULT_CHUNK_SIZE = 2000


def read_cidrs(filepath: Path) -> list[str]:
    """Read CIDRs from a file, skipping empty lines and comments."""
    cidrs = []
    with open(filepath, 'r') as f:
        for line in f:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                cidrs.append(stripped)
    return cidrs


def write_chunk(cidrs: list[str], output_path: Path) -> None:
    """Write CIDRs to a file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for cidr in cidrs:
            f.write(f"{cidr}\n")


def chunk_file(
    input_path: Path,
    output_dir: Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    prefix: str | None = None,
    dry_run: bool = False
) -> list[Path]:
    """Split a file into chunks.

    Args:
        input_path: Path to input file
        output_dir: Directory for output chunks
        chunk_size: Maximum CIDRs per chunk
        prefix: Prefix for chunk files (default: input filename without extension)
        dry_run: If True, don't write files

    Returns:
        List of output file paths
    """
    cidrs = read_cidrs(input_path)

    if not cidrs:
        print(f"Warning: No CIDRs found in {input_path}", file=sys.stderr)
        return []

    if prefix is None:
        prefix = input_path.stem

    # Calculate number of chunks needed
    num_chunks = (len(cidrs) + chunk_size - 1) // chunk_size

    output_files = []

    for i in range(num_chunks):
        start = i * chunk_size
        end = min((i + 1) * chunk_size, len(cidrs))
        chunk_cidrs = cidrs[start:end]

        # Use 001-based indexing
        chunk_num = i + 1
        output_filename = f"{prefix}-part-{chunk_num:03d}.txt"
        output_path = output_dir / output_filename

        if dry_run:
            print(f"Would create: {output_path} ({len(chunk_cidrs)} CIDRs)")
        else:
            write_chunk(chunk_cidrs, output_path)
            print(f"Created: {output_path} ({len(chunk_cidrs)} CIDRs)")

        output_files.append(output_path)

    return output_files


def main():
    parser = argparse.ArgumentParser(
        description='Split large CIDR files into chunks'
    )
    parser.add_argument(
        'input',
        type=Path,
        help='Input file to chunk'
    )
    parser.add_argument(
        'output_dir',
        type=Path,
        help='Output directory for chunks'
    )
    parser.add_argument(
        '-s', '--size',
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f'Chunk size (default: {DEFAULT_CHUNK_SIZE})'
    )
    parser.add_argument(
        '-p', '--prefix',
        help='Prefix for chunk filenames (default: input filename)'
    )
    parser.add_argument(
        '-n', '--dry-run',
        action='store_true',
        help='Show what would be done without writing files'
    )
    parser.add_argument(
        '--all-providers',
        action='store_true',
        help='Chunk all provider files that exceed chunk size'
    )

    args = parser.parse_args()

    if args.all_providers:
        # Chunk all provider files that exceed the chunk size
        providers_dir = Path('lists/providers')
        chunks_dir = Path('lists/chunks')

        if not providers_dir.exists():
            print(f"Error: {providers_dir} does not exist", file=sys.stderr)
            sys.exit(1)

        for provider_file in sorted(providers_dir.glob('*.txt')):
            cidrs = read_cidrs(provider_file)
            if len(cidrs) > args.size:
                output_dir = chunks_dir / provider_file.stem
                print(f"\n{provider_file.name} ({len(cidrs)} CIDRs) -> {output_dir}/")
                chunk_file(
                    provider_file,
                    output_dir,
                    args.size,
                    provider_file.stem,
                    args.dry_run
                )
            else:
                print(f"{provider_file.name} ({len(cidrs)} CIDRs) - no chunking needed")
    else:
        # Single file mode
        if not args.input.exists():
            print(f"Error: {args.input} does not exist", file=sys.stderr)
            sys.exit(1)

        output_files = chunk_file(
            args.input,
            args.output_dir,
            args.size,
            args.prefix,
            args.dry_run
        )

        if not output_files:
            sys.exit(1)


if __name__ == '__main__':
    main()
