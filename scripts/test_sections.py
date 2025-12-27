#!/usr/bin/env python3
"""
Test documentation sections with AI models.

Usage:
    python test_sections.py sections.json --models claude,gemini \
        [--config config.yaml] [--output test_results.json] [--workspace dir]
"""

import argparse
import sys
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from extraction_step import ExtractionResult
from testing_step import TestingStep


def main():
    parser = argparse.ArgumentParser(
        description='Test documentation sections with AI models',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('sections_file', help='Path to sections.json')
    parser.add_argument('--models', required=True,
                       help='Comma-separated model names (e.g., claude,gemini)')
    parser.add_argument('--config', default='config.yaml',
                       help='Path to config file (default: config.yaml)')
    parser.add_argument('--output', default='test_results.json',
                       help='Output JSON file (default: test_results.json)')
    parser.add_argument('--workspace', help='Workspace directory (optional)')
    parser.add_argument('--no-sessions', action='store_true',
                       help='Disable session management (use stateless queries)')

    args = parser.parse_args()

    # Load sections
    try:
        sections_result = ExtractionResult.load(args.sections_file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Load config
    try:
        with open(args.config) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        return 1

    # Parse models
    model_names = [m.strip() for m in args.models.split(',')]

    # Determine output path
    if args.workspace:
        output_path = Path(args.workspace) / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path(args.output)

    print(f"Testing {len(sections_result.sections)} sections with models: {', '.join(model_names)}")
    if args.no_sessions:
        print("Session management: disabled (stateless mode)")
    else:
        session_enabled = config.get('session_management', {}).get('enabled', False)
        print(f"Session management: {'enabled' if session_enabled else 'disabled'}")

    # Test sections
    try:
        step = TestingStep(
            config['models'],
            config.get('session_management', {}),
            session_manager=None
        )
        result = step.test_sections(
            sections_result.sections,
            model_names,
            use_sessions=not args.no_sessions
        )

        # Save and report
        result.save(str(output_path))

        print(f"\nTesting complete!")
        print(f"Sections tested: {result.sections_tested}")
        print(f"Models used: {', '.join(result.model_names)}")
        print(f"\nSaved to: {output_path}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
