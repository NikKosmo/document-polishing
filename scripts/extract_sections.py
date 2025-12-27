#!/usr/bin/env python3
"""
Extract testable sections from markdown document.

Usage:
    python extract_sections.py document.md [--output sections.json] [--workspace dir]
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from extraction_step import ExtractionStep


def main():
    parser = argparse.ArgumentParser(
        description='Extract testable sections from markdown document',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('document', help='Path to markdown document')
    parser.add_argument('--output', default='sections.json',
                       help='Output JSON file (default: sections.json)')
    parser.add_argument('--workspace', help='Workspace directory (optional)')

    args = parser.parse_args()

    # Determine output path
    if args.workspace:
        output_path = Path(args.workspace) / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path(args.output)

    print(f"Extracting sections from: {args.document}")

    # Extract sections
    try:
        step = ExtractionStep(args.document)
        result = step.extract()

        # Save and report
        result.save(str(output_path))

        print(f"\nExtracted {len(result.sections)} sections:")
        for summary in result.summary:
            print(f"  {summary}")

        print(f"\nSaved to: {output_path}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
