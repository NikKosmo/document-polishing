#!/usr/bin/env python3
"""
Run whole-document comprehension testing from a YAML question set.

Usage:
    python test_questions.py --questions path/to/questions.yaml --document path/to/doc.md
    python test_questions.py --questions path/to/questions.yaml --document path/to/doc.md --models claude,gemini
    python test_questions.py --questions path/to/questions.yaml --document path/to/doc.md -o workspace/
"""

import argparse
import sys
from pathlib import Path

import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from questioning_step import QuestioningStep, load_question_set


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for standalone question testing."""
    parser = argparse.ArgumentParser(
        description="Run whole-document question testing", formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--questions", required=True, help="Path to YAML question set file")
    parser.add_argument("--document", required=True, help="Path to document under test")
    parser.add_argument("--models", help="Comma-separated model names (optional)")
    parser.add_argument("--judge", default="claude", help="Judge model name (default: claude)")
    parser.add_argument("-o", "--output", default="workspace", help="Output directory (default: workspace)")
    parser.add_argument("--config", default="config.yaml", help="Path to config file (default: config.yaml)")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Load config
    try:
        with open(args.config, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        return 1

    # Load question set
    try:
        question_set = load_question_set(args.questions)
    except Exception as e:  # noqa: BLE001
        print(f"Error loading question set: {e}", file=sys.stderr)
        return 1

    # Load document
    document_path = Path(args.document).resolve()
    if not document_path.exists():
        print(f"Error: Document file not found: {document_path}", file=sys.stderr)
        return 1

    with open(document_path, "r", encoding="utf-8") as f:
        document_content = f.read()

    # Determine models
    if args.models:
        model_names = [m.strip() for m in args.models.split(",") if m.strip()]
    else:
        default_profile = config["settings"]["default_profile"]
        model_names = list(config["profiles"][default_profile]["models"])

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    questions_path = Path(args.questions).resolve()
    print(f"Question set: {questions_path}")
    print(f"Document: {document_path}")
    print(f"Questions: {len(question_set.questions)}")
    print(f"Models: {', '.join(model_names)}")
    print(f"Judge: {args.judge}")

    try:
        step = QuestioningStep(config["models"], config.get("session_management", {}), judge_model=args.judge)
        result = step.run(question_set=question_set, document_content=document_content, model_names=model_names)
        result.save(str(output_dir))

        print("\nQuestion testing complete!")
        print(f"Responses saved to: {output_dir / 'question_responses.json'}")
        print(f"Evaluations saved to: {output_dir / 'question_evaluations.json'}")
        print(f"Document score: {result.document_score:.3f}")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
