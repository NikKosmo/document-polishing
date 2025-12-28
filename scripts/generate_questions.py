#!/usr/bin/env python3
"""
Generate Questions CLI - Question-based testing framework

Generates questions from documentation sections using template-based approach.

Usage:
    python generate_questions.py generate <sections_json> <document_md> [--output workspace/]
    python generate_questions.py validate <questions_json>
    python generate_questions.py coverage <questions_json>

Commands:
    generate - Generate questions from sections
    validate - Validate existing questions
    coverage - Show coverage report
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
    Question,
    QuestionValidator,
    TestableElement
)


def cmd_generate(args):
    """Generate questions from sections."""
    print(f"Question Generation")
    print("=" * 70)
    print()

    # Load sections
    sections_path = Path(args.sections_json)
    if not sections_path.exists():
        print(f"❌ Error: Sections file not found: {sections_path}")
        return 1

    with open(sections_path, 'r', encoding='utf-8') as f:
        sections_data = json.load(f)

    sections = sections_data.get('sections', [])
    print(f"📄 Loaded {len(sections)} sections from {sections_path.name}")

    # Load document
    document_path = Path(args.document_md)
    if not document_path.exists():
        print(f"❌ Error: Document not found: {document_path}")
        return 1

    with open(document_path, 'r', encoding='utf-8') as f:
        document_text = f.read()

    print(f"📄 Loaded document: {document_path.name}")
    print()

    # Generate questions
    print("🔄 Generating questions...")
    print()

    step = QuestioningStep(template_path=args.template_path)
    result = step.generate_questions(
        sections=sections,
        document_text=document_text,
        document_path=str(document_path)
    )

    # Display statistics
    stats = result.statistics
    print("📊 Generation Statistics")
    print("-" * 70)
    print(f"  Total questions: {stats['total_questions']}")
    print(f"  Section coverage: {stats['coverage']['sections_covered']}/{stats['coverage']['total_sections']} sections ({stats['coverage']['section_coverage_pct']}%)")
    print(f"  Element coverage: {stats['coverage']['elements_covered']}/{stats['coverage']['total_elements']} elements ({stats['coverage']['element_coverage_pct']}%)")
    print()
    print(f"  By category:")
    for category, count in stats['by_category'].items():
        print(f"    - {category}: {count}")
    print()
    print(f"  By difficulty:")
    for difficulty, count in stats['by_difficulty'].items():
        print(f"    - {difficulty}: {count}")
    print()

    # Save result
    output_dir = args.output
    result.save(output_dir)
    output_path = Path(output_dir) / 'questions.json'
    print(f"✅ Saved questions to: {output_path}")
    print()

    # Coverage assessment
    section_coverage = stats['coverage']['section_coverage_pct']
    element_coverage = stats['coverage']['element_coverage_pct']

    if section_coverage >= 70.0 and element_coverage >= 60.0:
        print("✅ Coverage targets met (70% sections, 60% elements)")
    else:
        print(f"⚠️  Coverage below targets:")
        if section_coverage < 70.0:
            print(f"   - Section coverage: {section_coverage}% (target: 70%)")
        if element_coverage < 60.0:
            print(f"   - Element coverage: {element_coverage}% (target: 60%)")

    return 0


def cmd_validate(args):
    """Validate existing questions."""
    print(f"Question Validation")
    print("=" * 70)
    print()

    # Load questions
    questions_path = Path(args.questions_json)
    if not questions_path.exists():
        print(f"❌ Error: Questions file not found: {questions_path}")
        return 1

    result = QuestioningResult.load(str(questions_path.parent))
    questions = result.questions

    print(f"📄 Loaded {len(questions)} questions from {questions_path.name}")
    print()

    # Validate each question
    validator = QuestionValidator()
    valid_count = 0
    invalid_count = 0
    issues = []

    print("🔍 Validating questions...")
    print()

    for question in questions:
        # Create stub element for validation (we don't have original elements)
        element = TestableElement(
            element_type=question.metadata.get('testable_element', 'unknown'),
            text=question.metadata.get('element_text', ''),
            section_id=question.target_sections[0] if question.target_sections else 'unknown',
            section_title='',
            start_line=question.expected_answer.get('source_lines', [0])[0],
            end_line=question.expected_answer.get('source_lines', [0, 0])[1],
            context=question.expected_answer['text']  # Use answer as context
        )

        is_valid, reason = validator.validate(
            question.question_text,
            question.expected_answer['text'],
            element
        )

        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
            issues.append({
                'question_id': question.question_id,
                'question': question.question_text[:80] + '...' if len(question.question_text) > 80 else question.question_text,
                'reason': reason
            })

    # Display results
    print(f"✅ Valid questions: {valid_count}")
    print(f"❌ Invalid questions: {invalid_count}")
    print()

    if issues:
        print("Issues found:")
        print("-" * 70)
        for issue in issues:
            print(f"  [{issue['question_id']}] {issue['question']}")
            print(f"    Reason: {issue['reason']}")
            print()

    return 0 if invalid_count == 0 else 1


def cmd_coverage(args):
    """Show coverage report."""
    print(f"Coverage Report")
    print("=" * 70)
    print()

    # Load questions
    questions_path = Path(args.questions_json)
    if not questions_path.exists():
        print(f"❌ Error: Questions file not found: {questions_path}")
        return 1

    result = QuestioningResult.load(str(questions_path.parent))
    stats = result.statistics

    # Display overview
    print("📊 Overview")
    print("-" * 70)
    print(f"  Document: {result.document_path}")
    print(f"  Generated: {result.generation_timestamp}")
    print(f"  Version: {result.generator_version}")
    print(f"  Total questions: {stats['total_questions']}")
    print()

    # Display coverage
    print("📈 Coverage Metrics")
    print("-" * 70)
    coverage = stats['coverage']
    print(f"  Section coverage:")
    print(f"    - Covered: {coverage['sections_covered']}/{coverage['total_sections']} sections")
    print(f"    - Percentage: {coverage['section_coverage_pct']}%")
    print(f"    - Target: 70.0%")
    print(f"    - Status: {'✅ Met' if coverage['section_coverage_pct'] >= 70.0 else '❌ Below target'}")
    print()
    print(f"  Element coverage:")
    print(f"    - Covered: {coverage['elements_covered']}/{coverage['total_elements']} elements")
    print(f"    - Percentage: {coverage['element_coverage_pct']}%")
    print(f"    - Target: 60.0%")
    print(f"    - Status: {'✅ Met' if coverage['element_coverage_pct'] >= 60.0 else '❌ Below target'}")
    print()

    # Display breakdown
    print("📋 Question Breakdown")
    print("-" * 70)
    print(f"  By scope:")
    print(f"    - Section-level: {stats['section_level']}")
    print(f"    - Document-level: {stats['document_level']}")
    print()
    print(f"  By category:")
    for category, count in sorted(stats['by_category'].items()):
        print(f"    - {category}: {count}")
    print()
    print(f"  By difficulty:")
    for difficulty, count in sorted(stats['by_difficulty'].items()):
        print(f"    - {difficulty}: {count}")
    print()
    print(f"  Adversarial questions: {stats['adversarial']}")
    print()

    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Question-based testing framework CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate questions from sections
  python generate_questions.py generate workspace/sections.json document.md --output workspace/

  # Validate generated questions
  python generate_questions.py validate workspace/questions.json

  # Show coverage report
  python generate_questions.py coverage workspace/questions.json
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Generate command
    parser_gen = subparsers.add_parser('generate', help='Generate questions from sections')
    parser_gen.add_argument('sections_json', help='Path to sections.json file')
    parser_gen.add_argument('document_md', help='Path to source document')
    parser_gen.add_argument('--output', default='workspace/', help='Output directory (default: workspace/)')
    parser_gen.add_argument('--template-path', help='Path to question_templates.json (optional)')

    # Validate command
    parser_val = subparsers.add_parser('validate', help='Validate existing questions')
    parser_val.add_argument('questions_json', help='Path to questions.json file')

    # Coverage command
    parser_cov = subparsers.add_parser('coverage', help='Show coverage report')
    parser_cov.add_argument('questions_json', help='Path to questions.json file')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Route to command
    if args.command == 'generate':
        return cmd_generate(args)
    elif args.command == 'validate':
        return cmd_validate(args)
    elif args.command == 'coverage':
        return cmd_coverage(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
