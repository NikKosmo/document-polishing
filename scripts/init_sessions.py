#!/usr/bin/env python3
"""
Initialize model sessions with document context.

Usage:
    python init_sessions.py sections.json --models claude,gemini \
        [--config config.yaml] [--output session_metadata.json] [--workspace dir]
"""

import argparse
import sys
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from extraction_step import ExtractionResult
from session_init_step import SessionInitStep


def main():
    parser = argparse.ArgumentParser(
        description='Initialize model sessions with document context',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('sections_file', help='Path to sections.json')
    parser.add_argument('--models', required=True,
                       help='Comma-separated model names (e.g., claude,gemini)')
    parser.add_argument('--config', default='config.yaml',
                       help='Path to config file (default: config.yaml)')
    parser.add_argument('--output', default='session_metadata.json',
                       help='Output JSON file (default: session_metadata.json)')
    parser.add_argument('--workspace', help='Workspace directory (optional)')

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

    # Check if sessions are enabled
    session_config = config.get('session_management', {})
    if not session_config.get('enabled', False):
        print("Warning: Session management is disabled in config.", file=sys.stderr)
        print("Set session_management.enabled: true in config.yaml to use sessions.", file=sys.stderr)
        return 1

    # Determine output path
    if args.workspace:
        output_path = Path(args.workspace) / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path(args.output)

    print(f"Initializing sessions for models: {', '.join(model_names)}")

    # Initialize sessions
    try:
        step = SessionInitStep(config['models'], session_config)
        result = step.init_sessions(
            sections_result.document_content,
            model_names,
            session_config.get('purpose_prompt')
        )

        # Save and report
        result.save(str(output_path))

        print(f"\nSessions initialized: {len(result.session_ids)}")
        for model, session_id in result.session_ids.items():
            print(f"  {model}: {session_id[:16]}...")

        if result.failed_models:
            print(f"\nFailed models: {', '.join(result.failed_models)}")

        print(f"\nSaved to: {output_path}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
