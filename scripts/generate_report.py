#!/usr/bin/env python3
"""
Generate report and polished document from detected ambiguities.

Usage:
    python generate_report.py test_results.json ambiguities.json \
        --document original.md [--output-report report.md] \
        [--output-polished polished.md] [--workspace dir]
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from testing_step import TestingResult
from detection_step import DetectionResult
from reporting_step import ReportingStep


def main():
    parser = argparse.ArgumentParser(
        description='Generate report and polished document from detected ambiguities',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('test_results_file', help='Path to test_results.json')
    parser.add_argument('ambiguities_file', help='Path to ambiguities.json')
    parser.add_argument('--document', required=True,
                       help='Original document path')
    parser.add_argument('--session-id', default='standalone',
                       help='Session ID for report header (default: standalone)')
    parser.add_argument('--judge', default='claude',
                       help='Judge model name (default: claude)')
    parser.add_argument('--output-report', default='report.md',
                       help='Output report file (default: report.md)')
    parser.add_argument('--output-polished',
                       help='Output polished document (default: {doc}_polished.md)')
    parser.add_argument('--workspace', help='Workspace directory (optional)')

    args = parser.parse_args()

    # Load test results and ambiguities
    try:
        testing_result = TestingResult.load(args.test_results_file)
        detection_result = DetectionResult.load(args.ambiguities_file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Read document content
    try:
        with open(args.document) as f:
            document_content = f.read()
    except FileNotFoundError:
        print(f"Error: Document not found: {args.document}", file=sys.stderr)
        return 1

    # Determine output paths
    if args.workspace:
        report_path = Path(args.workspace) / args.output_report
        if args.output_polished:
            polished_path = Path(args.workspace) / args.output_polished
        else:
            doc_stem = Path(args.document).stem
            polished_path = Path(args.workspace) / f"{doc_stem}_polished.md"
    else:
        report_path = Path(args.output_report)
        if args.output_polished:
            polished_path = Path(args.output_polished)
        else:
            doc_stem = Path(args.document).stem
            polished_path = Path(f"{doc_stem}_polished.md")

    print(f"Generating report from {len(testing_result.test_results)} sections...")
    print(f"Ambiguities found: {len(detection_result.ambiguities)}")

    # Generate report
    try:
        step = ReportingStep(args.session_id, args.document, args.judge)
        report_content = step.generate_report(
            testing_result.test_results,
            detection_result.ambiguities,
            testing_result.model_names
        )

        # Save report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            f.write(report_content)
        print(f"\nReport saved to: {report_path}")

        # Generate polished document (if ambiguities found)
        if detection_result.ambiguities:
            polished_content = step.generate_polished_document(
                document_content,
                detection_result.ambiguities
            )
            polished_path.parent.mkdir(parents=True, exist_ok=True)
            with open(polished_path, 'w') as f:
                f.write(polished_content)
            print(f"Polished document saved to: {polished_path}")
        else:
            print("No ambiguities found - no polished document generated")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
