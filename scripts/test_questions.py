#!/usr/bin/env python3
"""
Test Questions CLI - Question-based testing framework

Generates questions from documentation sections, collects model answers,
and evaluates comprehension using LLM-as-Judge.

Usage:
    python test_questions.py generate <sections_json> <document_md> [--output workspace/]
    python test_questions.py test <questions_json> --session <session_metadata> --models claude,gemini
    python test_questions.py evaluate <answers_json> --judge claude
    python test_questions.py auto <sections_json> <document_md> [options]

Commands:
    generate  - Generate questions from sections
    test      - Collect answers from models
    evaluate  - Evaluate answers with LLM-as-Judge
    auto      - Run full pipeline (generate → test → evaluate)
"""

import sys
import json
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from questioning_step import (
    QuestioningStep,
    QuestioningResult,
    Question
)
from session_manager import SessionManager
import yaml


def create_session_manager(document_content: str, models: list, purpose: str = None) -> SessionManager:
    """
    Create SessionManager and initialize sessions with document context.

    Args:
        document_content: Full document text for context
        models: List of model names to use
        purpose: Optional purpose prompt

    Returns:
        Initialized SessionManager with active sessions
    """
    from session_init_step import SessionInitStep

    # Create minimal models config
    models_config = {}
    for model in models:
        models_config[model] = {
            'command': model,
            'timeout': 30
        }

    # Create session config
    session_config = {
        'enabled': True,
        'mode': 'continue-on-error',
        'max_retries': 2
    }

    # Initialize sessions with document context
    if purpose is None:
        purpose = "This document is being tested for comprehension. Please analyze questions about this documentation."

    session_init_step = SessionInitStep(models_config, session_config)
    session_result = session_init_step.init_sessions(
        document_content=document_content,
        model_names=models,
        purpose_prompt=purpose
    )

    return session_result.session_manager


def cmd_generate(args):
    """Generate questions from sections (Phase 2-3)."""
    print(f"Generating questions from {args.sections}")
    print(f"Document: {args.document}")

    # Load sections
    with open(args.sections, 'r', encoding='utf-8') as f:
        sections_data = json.load(f)
        sections = sections_data.get('sections', [])

    # Load document text
    document_text = Path(args.document).read_text(encoding='utf-8')

    # Initialize questioning step
    step = QuestioningStep(
        enable_document_level=args.document_level
    )

    # Generate questions
    result = step.generate_questions(
        sections=sections,
        document_text=document_text,
        document_path=args.document
    )

    # Save to output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    result.save(str(output_dir))

    print(f"\n✓ Generated {len(result.questions)} questions")
    print(f"  Section-level: {result.statistics['section_level']}")
    print(f"  Document-level: {result.statistics['document_level']}")
    print(f"  Coverage: {result.statistics['coverage']['section_coverage_pct']:.1f}% sections, "
          f"{result.statistics['coverage']['element_coverage_pct']:.1f}% elements")
    print(f"  Saved to: {output_dir / 'questions.json'}")

    return 0


def cmd_test(args):
    """Collect answers from models (Phase 4)."""
    print(f"Collecting answers for {args.questions}")
    print(f"Models: {args.models}")

    # Parse models list
    models = [m.strip() for m in args.models.split(',')]

    # Load questions
    questions_file = Path(args.questions)
    with open(questions_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        questions = [Question.from_dict(q) for q in data.get('questions', [])]

    # Load sections file for document content
    sections_path = questions_file.parent / 'sections.json'
    with open(sections_path, 'r', encoding='utf-8') as f:
        sections_data = json.load(f)
        document_content = sections_data.get('document_content', '')

    # Create session manager with document context
    print(f"\nInitializing sessions with document context...")
    session_manager = create_session_manager(document_content, models)

    # Initialize questioning step
    step = QuestioningStep(session_manager=session_manager)

    # Collect answers
    print(f"Collecting answers from {len(models)} models...")
    answers = step.collect_answers(
        questions=questions,
        models=models,
        session_manager=session_manager
    )

    # Save answers
    output_file = questions_file.parent / 'answers.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        # Convert QuestionAnswer objects to dicts
        serializable_answers = {}
        for qid, model_answers in answers.items():
            serializable_answers[qid] = {
                model: answer.to_dict()
                for model, answer in model_answers.items()
            }
        json.dump({
            'questions': data.get('questions', []),
            'answers': serializable_answers
        }, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Collected {len(answers)} question answers")
    print(f"  Saved to: {output_file}")

    return 0


def cmd_evaluate(args):
    """Evaluate answers with LLM-as-Judge (Phase 4)."""
    print(f"Evaluating answers in {args.answers}")
    print(f"Judge model: {args.judge}")

    # Load answers file
    with open(args.answers, 'r', encoding='utf-8') as f:
        data = json.load(f)
        questions = [Question.from_dict(q) for q in data.get('questions', [])]
        answers_data = data.get('answers', {})

    # Load sections file (needed for context during evaluation)
    sections_path = Path(args.answers).parent / 'sections.json'
    with open(sections_path, 'r', encoding='utf-8') as f:
        sections_data = json.load(f)
        sections = sections_data.get('sections', [])
        document_content = sections_data.get('document_content', '')

    # Create session manager for judge with document context
    print(f"\nInitializing judge session with document context...")
    session_manager = create_session_manager(
        document_content,
        [args.judge],
        purpose="You are evaluating model answers to questions about this documentation. Please judge answers for correctness."
    )

    # Initialize questioning step
    step = QuestioningStep(session_manager=session_manager)

    # Reconstruct answers dict
    from questioning_step import QuestionAnswer
    answers = {}
    for qid, model_answers in answers_data.items():
        answers[qid] = {
            model: QuestionAnswer.from_dict(ans)
            for model, ans in model_answers.items()
        }

    # Evaluate answers
    print(f"\nEvaluating {len(questions)} questions...")
    results = step.evaluate_answers(
        questions=questions,
        answers=answers,
        sections=sections,
        session_manager=session_manager,
        judge_model=args.judge
    )

    # Detect issues
    issues = step.detect_issues(results)

    # Calculate summary statistics
    consensus_counts = {}
    for result in results.values():
        consensus = result.consensus
        consensus_counts[consensus] = consensus_counts.get(consensus, 0) + 1

    # Save results
    output_file = Path(args.answers).parent / 'question_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_questions': len(results),
            'consensus_breakdown': consensus_counts,
            'issues_detected': len(issues),
            'issues': issues,
            'results': {qid: r.to_dict() for qid, r in results.items()}
        }, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Evaluation complete")
    print(f"  Consensus breakdown:")
    for consensus_type, count in consensus_counts.items():
        print(f"    {consensus_type}: {count}")
    print(f"  Issues detected: {len(issues)}")
    print(f"  Saved to: {output_file}")

    return 0


def cmd_auto(args):
    """Run full pipeline (generate → test → evaluate)."""
    print("Running full question-based testing pipeline...")
    print()

    # Run generate
    print("=" * 60)
    print("Step 1: Generating Questions")
    print("=" * 60)
    cmd_generate(args)
    print()

    # Run test
    print("=" * 60)
    print("Step 2: Collecting Answers")
    print("=" * 60)
    # Update args for test command
    args.questions = str(Path(args.output) / 'questions.json')
    cmd_test(args)
    print()

    # Run evaluate
    print("=" * 60)
    print("Step 3: Evaluating Answers")
    print("=" * 60)
    args.answers = str(Path(args.output) / 'answers.json')
    cmd_evaluate(args)
    print()

    print("=" * 60)
    print("Pipeline Complete!")
    print("=" * 60)

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Question-based testing framework CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate questions from sections
  python test_questions.py generate workspace/sections.json document.md --output workspace/

  # Collect answers from models
  python test_questions.py test workspace/questions.json --session workspace/session_metadata.json --models claude,gemini

  # Evaluate answers with judge
  python test_questions.py evaluate workspace/answers.json --judge claude

  # Run full pipeline
  python test_questions.py auto workspace/sections.json document.md --output workspace/ --session workspace/session_metadata.json --models claude,gemini --judge claude
"""
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate questions from sections')
    gen_parser.add_argument('sections', help='Path to sections.json')
    gen_parser.add_argument('document', help='Path to source document')
    gen_parser.add_argument('--output', default='workspace', help='Output directory (default: workspace)')
    gen_parser.add_argument('--document-level', action='store_true', default=False, help='Include document-level questions (default: False)')
    gen_parser.add_argument('--no-document-level', dest='document_level', action='store_false', help='Disable document-level questions')

    # Test command
    test_parser = subparsers.add_parser('test', help='Collect answers from models')
    test_parser.add_argument('questions', help='Path to questions.json')
    test_parser.add_argument('--session', required=False, help='Path to session_metadata.json (optional, will create new if not provided)')
    test_parser.add_argument('--models', required=True, help='Comma-separated list of models')

    # Evaluate command
    eval_parser = subparsers.add_parser('evaluate', help='Evaluate answers with LLM-as-Judge')
    eval_parser.add_argument('answers', help='Path to answers.json')
    eval_parser.add_argument('--judge', default='claude', help='Judge model (default: claude)')

    # Auto command
    auto_parser = subparsers.add_parser('auto', help='Run full pipeline')
    auto_parser.add_argument('sections', help='Path to sections.json')
    auto_parser.add_argument('document', help='Path to source document')
    auto_parser.add_argument('--output', default='workspace', help='Output directory')
    auto_parser.add_argument('--session', required=False, help='Path to session_metadata.json (optional, will create new if not provided)')
    auto_parser.add_argument('--models', required=True, help='Comma-separated list of models')
    auto_parser.add_argument('--judge', default='claude', help='Judge model')
    auto_parser.add_argument('--document-level', action='store_true', default=False, help='Include document-level questions (default: False)')
    auto_parser.add_argument('--no-document-level', dest='document_level', action='store_false', help='Disable document-level questions')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Route to command handler
    if args.command == 'generate':
        return cmd_generate(args)
    elif args.command == 'test':
        return cmd_test(args)
    elif args.command == 'evaluate':
        return cmd_evaluate(args)
    elif args.command == 'auto':
        return cmd_auto(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
