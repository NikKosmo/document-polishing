"""
Reporting Step - Generate markdown reports and polished documents

This module provides a clean interface for Step 5 of the document polishing pipeline.
It generates formatted markdown reports from ambiguity detection results and creates
polished versions of documents with clarification markers.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ambiguity_detector import Ambiguity, Severity


@dataclass
class ReportingResult:
    """
    Result of report generation.

    Contains the generated report content, optional polished document content,
    and count of ambiguities found.
    """

    report_content: str
    polished_content: Optional[str] = None
    ambiguities_found: int = 0

    def save_report(self, output_path: str):
        """
        Save report to markdown file.

        Args:
            output_path: Path to output report.md file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(self.report_content)

    def save_polished(self, output_path: str):
        """
        Save polished document to markdown file.

        Args:
            output_path: Path to output polished.md file

        Raises:
            ValueError: If no polished content exists
        """
        if self.polished_content is None:
            raise ValueError("No polished content to save (no ambiguities found)")

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(self.polished_content)


class ReportingStep:
    """
    Step 6: Generate report and polished document from ambiguity detection results.

    This class provides methods to generate markdown reports summarizing detected
    ambiguities and create polished versions of documents with clarification markers.

    Usage:
        step = ReportingStep('session_123', 'document.md', 'claude')
        report = step.generate_report(test_results, ambiguities, model_names)
        polished = step.generate_polished_document(document_content, ambiguities)
    """

    def __init__(self, session_id: str, document_path: str, judge_model: str = "claude"):
        """
        Initialize reporting step.

        Args:
            session_id: Unique identifier for this polishing session
            document_path: Path to original document
            judge_model: Name of judge model used for detection
        """
        self.session_id = session_id
        self.document_path = Path(document_path).resolve().name
        self.judge_model = judge_model

    def generate_report(
        self,
        test_results: Dict[str, Dict],
        ambiguities: List[Ambiguity],
        model_names: List[str],
        question_result: Optional[Any] = None,
    ) -> str:
        """
        Generate markdown report from ambiguity detection results.

        Args:
            test_results: Dict mapping section_id to {section, results}
            ambiguities: List of detected Ambiguity objects
            model_names: List of model names used in testing
            question_result: Optional QuestioningResult for comprehension testing

        Returns:
            Formatted markdown report as string
        """
        report = f"""# Documentation Polish Report

**Session ID:** {self.session_id}
**Document:** {self.document_path}
**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Judge Model:** {self.judge_model}

## Summary

- **Sections Tested:** {len(test_results)}
- **Ambiguities Found:** {len(ambiguities)}
- **Models Used:** {", ".join(model_names)}

### Ambiguities by Severity

"""
        # Count by severity
        severity_counts = {s.value: 0 for s in Severity}
        for amb in ambiguities:
            severity_counts[amb.severity.value] += 1

        for sev, count in severity_counts.items():
            emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(sev, "⚪")
            report += f"- {emoji} **{sev.upper()}:** {count}\n"

        report += "\n## Ambiguities Detected\n\n"

        if not ambiguities:
            report += "*No ambiguities detected. The documentation appears clear.*\n"
        else:
            for i, amb in enumerate(ambiguities, 1):
                severity_emoji = {
                    Severity.CRITICAL: "🔴",
                    Severity.HIGH: "🟠",
                    Severity.MEDIUM: "🟡",
                    Severity.LOW: "🟢",
                }.get(amb.severity, "⚪")

                report += f"### {i}. {amb.section_header} {severity_emoji} ({amb.severity.value})\n\n"

                quoted_lines = "\n".join(f"> {line}" for line in amb.section_content.splitlines())
                report += f"**Original Text:**\n{quoted_lines}\n\n"

                report += "**Interpretations:**\n"
                for model_name, interp in amb.interpretations.items():
                    report += f"\n**{model_name}:**\n"
                    report += f"- Understanding: {interp.interpretation}\n"
                    if interp.steps:
                        report += f"- Steps: {', '.join(interp.steps)}\n"
                    if interp.assumptions:
                        report += f"- Assumptions: {', '.join(interp.assumptions)}\n"
                    if interp.ambiguities:
                        report += f"- Noted ambiguities: {', '.join(interp.ambiguities)}\n"

                # Add comparison details
                if amb.comparison_details:
                    report += "\n**Analysis:**\n"
                    details = amb.comparison_details.get("details", "")
                    if details:
                        report += f"- {details}\n"

                    key_diffs = amb.comparison_details.get("key_differences", [])
                    if key_diffs:
                        report += f"- Key differences: {', '.join(key_diffs)}\n"

                    # Show shared concerns if present
                    if amb.comparison_details.get("reason") == "Models agreed but all noted similar concerns":
                        shared_concerns = amb.comparison_details.get("shared_concerns", [])
                        if shared_concerns:
                            report += "\n**Shared Concerns:**\n"
                            for concern in shared_concerns:
                                report += f"- {concern}\n"

                report += "\n---\n\n"

        if question_result is not None:
            report += self._generate_comprehension_section(question_result)

        # Note about detailed results
        report += "\n---\n\n"
        report += "*For detailed test results, see `test_results.json` in this workspace directory.*\n"

        return report

    def _generate_comprehension_section(self, question_result: Any) -> str:
        """Generate optional comprehension testing section from Step 5 results."""
        questions = question_result.question_set.questions
        models = question_result.model_names

        section = "\n---\n\n"
        section += "## Comprehension Testing\n\n"
        section += f"- **Questions tested:** {len(questions)}\n"
        section += f"- **Models:** {', '.join(models)}\n"
        section += f"- **Judge:** {question_result.judge_model}\n\n"

        # Verdict table with category
        header = "| Question | Category | " + " | ".join(models) + " |\n"
        separator = "|----------|----------|" + "|".join(["---------"] * len(models)) + "|\n"
        section += header
        section += separator

        for question in questions:
            model_evaluations = question_result.evaluations.get(question.id, {})
            verdict_cells = []
            for model in models:
                ev = model_evaluations.get(model)
                if ev:
                    emoji = {"correct": "✅", "partial": "🟡", "incorrect": "❌", "evasive": "⚪"}.get(ev.verdict, "")
                    verdict_cells.append(f"{emoji} {ev.verdict}")
                else:
                    verdict_cells.append("n/a")
            section += f"| {question.id} | {question.category} | " + " | ".join(verdict_cells) + " |\n"

        total_questions = len(questions)
        score_ratio = question_result.document_score
        score_pct = score_ratio * 100
        section += f"\n**Score: {score_pct:.0f}%** ({total_questions} questions)\n"

        # Consensus summary
        if question_result.consensus:
            all_correct = sum(1 for v in question_result.consensus.values() if v == "all correct")
            mixed = sum(1 for v in question_result.consensus.values() if v == "mixed")
            all_incorrect = sum(1 for v in question_result.consensus.values() if v not in {"all correct", "mixed"})
            if all_correct == total_questions:
                section += "\nAll models answered all questions correctly"
                section += " — document is clear on tested topics.\n"
            else:
                section += f"\nConsensus: {all_correct} all-correct, {mixed} mixed, {all_incorrect} all-incorrect\n"

        # Per-question detail
        section += "\n### Question Details\n"

        for question in questions:
            model_evaluations = question_result.evaluations.get(question.id, {})
            section += f"\n#### {question.id} ({question.category}, {question.difficulty})\n\n"
            section += f"**Question:**\n> {question.question.strip()}\n\n"

            # Expected key points and anti-points
            section += "**Expected key points:**\n"
            for kp in question.expected.key_points:
                section += f"- {kp}\n"
            if question.expected.anti_points:
                section += "\n**Anti-points (must NOT appear):**\n"
                for ap in question.expected.anti_points:
                    section += f"- {ap}\n"

            # Per-model evaluation
            for model in models:
                ev = model_evaluations.get(model)
                if not ev:
                    continue
                emoji = {"correct": "✅", "partial": "🟡", "incorrect": "❌", "evasive": "⚪"}.get(ev.verdict, "")
                section += f"\n**{model}:** {emoji} {ev.verdict}"
                section += f" ({ev.matched_key_points}/{ev.total_key_points} key points)\n"

                # Model's actual answer (first 300 chars)
                if ev.answer_text:
                    answer_preview = ev.answer_text.strip().replace("\n", " ")
                    if len(answer_preview) > 300:
                        answer_preview = answer_preview[:300] + "..."
                    section += f"- Answer: {answer_preview}\n"

                # Key point coverage
                for kp, matched in ev.key_point_coverage.items():
                    mark = "✓" if matched else "✗"
                    section += f"- {mark} {kp}\n"

                # Anti-point violations
                if ev.anti_points_present:
                    section += f"- ⚠️ Anti-points triggered: {', '.join(ev.anti_points_present)}\n"

                # Judge reasoning
                if ev.reasoning:
                    section += f"- Reasoning: {ev.reasoning}\n"

            # Consensus for this question
            consensus = question_result.consensus.get(question.id, "")
            if consensus:
                section += f"\n**Consensus:** {consensus}\n"

        return section

    def generate_polished_document(self, document_content: str, ambiguities: List[Ambiguity]) -> str:
        """
        Create polished version of document with clarification markers.

        Adds clarification notes after ambiguous sections to highlight areas
        that need improvement. Full fix generation will be in Increment 3.

        Args:
            document_content: Full original document text
            ambiguities: List of detected Ambiguity objects

        Returns:
            Polished document with clarification markers as string
        """
        content = document_content

        # Add clarification notes after ambiguous sections
        # (Full fix generation will be in Increment 3)

        for amb in ambiguities:
            original = amb.section_content

            # Create clarification note based on severity
            severity_marker = {
                Severity.CRITICAL: "🔴 CRITICAL",
                Severity.HIGH: "🟠 HIGH",
                Severity.MEDIUM: "🟡 MEDIUM",
                Severity.LOW: "🟢 LOW",
            }.get(amb.severity, "⚠️")

            clarification = f"\n\n> **{severity_marker} - CLARIFICATION NEEDED:**\n"
            clarification += "> Different interpretations were found:\n"

            for model_name, interp in amb.interpretations.items():
                short_interp = interp.interpretation[:150]
                if len(interp.interpretation) > 150:
                    short_interp += "..."
                clarification += f"> - **{model_name}:** {short_interp}\n"

            # Add key differences if available
            key_diffs = amb.comparison_details.get("key_differences", [])
            if key_diffs:
                clarification += f">\n> **Key differences:** {', '.join(key_diffs)}\n"

            # Simple replacement (will be improved in Increment 3)
            if original in content:
                content = content.replace(original, original + clarification, 1)

        return content


# For testing the module directly
if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 4:
        print("Usage: python reporting_step.py <test_results.json> <ambiguities.json> <document.md> [output_report.md]")
        sys.exit(1)

    test_results_file = sys.argv[1]
    ambiguities_file = sys.argv[2]
    document_file = sys.argv[3]
    output_report = sys.argv[4] if len(sys.argv) > 4 else "report.md"

    # Load test results
    with open(test_results_file, "r") as f:
        test_results = json.load(f)

    # Load ambiguities
    with open(ambiguities_file, "r") as f:
        ambiguities_data = json.load(f)

    # Convert ambiguities JSON to Ambiguity objects
    from ambiguity_detector import Interpretation

    ambiguities = []
    for amb_data in ambiguities_data:
        interpretations = {}
        for model_name, interp_data in amb_data["interpretations"].items():
            interpretations[model_name] = Interpretation(
                model_name=model_name,
                raw_response="",
                interpretation=interp_data.get("interpretation", ""),
                steps=interp_data.get("steps", []),
                assumptions=interp_data.get("assumptions", []),
                ambiguities=interp_data.get("ambiguities", []),
            )

        ambiguities.append(
            Ambiguity(
                section_id=amb_data["section_id"],
                section_header=amb_data["section_header"],
                section_content=amb_data["section_content"],
                severity=Severity(amb_data["severity"]),
                interpretations=interpretations,
                comparison_details=amb_data.get("comparison_details", {}),
            )
        )

    # Read document
    with open(document_file, "r") as f:
        document_content = f.read()

    # Extract model names from test results
    model_names = []
    for section_data in test_results.values():
        if "results" in section_data:
            model_names = list(section_data["results"].keys())
            break

    # Generate report
    step = ReportingStep("test_session", document_file, "claude")
    report_content = step.generate_report(test_results, ambiguities, model_names)

    # Save report
    with open(output_report, "w") as f:
        f.write(report_content)

    print(f"Report generated: {output_report}")
    print(f"Sections tested: {len(test_results)}")
    print(f"Ambiguities found: {len(ambiguities)}")
