#!/usr/bin/env python3
"""
Delete all non-text files recursively in a directory.
"""

import os
import sys
import argparse
import mimetypes
from pathlib import Path


def is_text_file(filepath):
    """
    Check if a file is a text file by examining its content.
    Returns True if the file is text, False otherwise.
    """
    try:
        # First check MIME type
        mime_type, _ = mimetypes.guess_type(filepath)
        if mime_type and mime_type.startswith('text/'):
            return True

        # Check by reading a sample of the file
        with open(filepath, 'rb') as f:
            # Read first 8192 bytes
            chunk = f.read(8192)
            if not chunk:  # Empty file
                return True

            # Check for null bytes (binary indicator)
            if b'\x00' in chunk:
                return False

            # Try to decode as text
            try:
                chunk.decode('utf-8')
                return True
            except UnicodeDecodeError:
                # Try other common encodings
                for encoding in ['latin-1', 'ascii', 'utf-16']:
                    try:
                        chunk.decode(encoding)
                        return True
                    except UnicodeDecodeError:
                        continue
                return False

    except Exception:
        # If we can't read the file, assume it's not text
        return False


def delete_non_text_files(directory, dry_run=False):
    """
    Recursively delete all non-text files in the given directory.
    """
    deleted_files = []
    errors = []

    for root, dirs, files in os.walk(directory):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for filename in files:
            filepath = os.path.join(root, filename)

            # Skip hidden files
            if filename.startswith('.'):
                continue

            try:
                if not is_text_file(filepath):
                    if dry_run:
                        print(f"Would delete: {filepath}")
                    else:
                        os.remove(filepath)
                        print(f"Deleted: {filepath}")
                    deleted_files.append(filepath)
            except Exception as e:
                error_msg = f"Error processing {filepath}: {str(e)}"
                errors.append(error_msg)
                print(f"ERROR: {error_msg}", file=sys.stderr)

    return deleted_files, errors


def main():
    parser = argparse.ArgumentParser(
        description='Recursively delete all non-text files in a directory'
    )
    parser.add_argument(
        'directory',
        help='Directory to process'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    parser.add_argument(
        '--yes',
        '-y',
        action='store_true',
        help='Skip confirmation prompt'
    )

    args = parser.parse_args()

    # Validate directory
    directory = Path(args.directory).resolve()
    if not directory.exists():
        print(f"Error: Directory '{directory}' does not exist", file=sys.stderr)
        sys.exit(1)
    if not directory.is_dir():
        print(f"Error: '{directory}' is not a directory", file=sys.stderr)
        sys.exit(1)

    # Confirmation prompt
    if not args.dry_run and not args.yes:
        print(f"This will DELETE all non-text files in '{directory}' and its subdirectories.")
        print("This action cannot be undone!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Aborted.")
            sys.exit(0)

    # Process files
    print(f"{'Scanning' if args.dry_run else 'Processing'} directory: {directory}")
    deleted_files, errors = delete_non_text_files(directory, args.dry_run)

    # Summary
    print(f"\n{'Would delete' if args.dry_run else 'Deleted'} {len(deleted_files)} files")
    if errors:
        print(f"Encountered {len(errors)} errors")

    if args.dry_run and deleted_files:
        print("\nRun without --dry-run to actually delete these files")


if __name__ == '__main__':
    main()
