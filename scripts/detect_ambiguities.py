#!/usr/bin/env python3
"""
Detect ambiguities from model test results.

Usage:
    python detect_ambiguities.py test_results.json \
        [--config config.yaml] [--judge claude] [--strategy llm_judge] \
        [--output ambiguities.json] [--workspace dir]
"""

import argparse
import sys
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from testing_step import TestingResult
from detection_step import DetectionStep
from ambiguity_detector import JudgeFailureError


def main():
    parser = argparse.ArgumentParser(
        description='Detect ambiguities from model test results',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('test_results_file', help='Path to test_results.json')
    parser.add_argument('--config', default='config.yaml',
                       help='Path to config file (default: config.yaml)')
    parser.add_argument('--judge', default='claude',
                       help='Judge model name (default: claude)')
    parser.add_argument('--strategy', default='llm_judge',
                       choices=['llm_judge', 'simple'],
                       help='Detection strategy (default: llm_judge)')
    parser.add_argument('--output', default='ambiguities.json',
                       help='Output JSON file (default: ambiguities.json)')
    parser.add_argument('--workspace', help='Workspace directory (optional)')

    args = parser.parse_args()

    # Load test results
    try:
        testing_result = TestingResult.load(args.test_results_file)
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

    # Determine workspace path for judge logs
    workspace = Path(args.workspace) if args.workspace else Path.cwd()

    # Determine output path
    if args.workspace:
        output_path = Path(args.workspace) / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path(args.output)

    print(f"Detecting ambiguities in {len(testing_result.test_results)} sections...")
    print(f"Strategy: {args.strategy}")
    if args.strategy == 'llm_judge':
        print(f"Judge model: {args.judge}")

    # Detect ambiguities
    try:
        step = DetectionStep(
            strategy=args.strategy,
            judge_model=args.judge,
            models_config=config['models'],
            workspace=workspace
        )
        result = step.detect(testing_result.test_results)

        # Save and report
        result.save(str(output_path))

        print(f"\nDetection complete!")
        print(f"Ambiguities found: {len(result.ambiguities)}")
        if result.severity_counts:
            print("Breakdown:")
            for severity, count in result.severity_counts.items():
                emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(severity, '⚪')
                print(f"  {emoji} {severity}: {count}")

        print(f"\nSaved to: {output_path}")

        return 0

    except JudgeFailureError as e:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"❌ JUDGE COMPARISON FAILED", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"Section: {e.section_id}", file=sys.stderr)
        print(f"Reason: {e.reason}", file=sys.stderr)
        if e.details:
            print(f"Details: {e.details}", file=sys.stderr)
        print(f"{'='*60}\n", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
