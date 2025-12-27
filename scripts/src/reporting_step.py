"""
Reporting Step - Generate markdown reports and polished documents

This module provides a clean interface for Step 4-5 of the document polishing pipeline.
It generates formatted markdown reports from ambiguity detection results and creates
polished versions of documents with clarification markers.
"""

from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path

from ambiguity_detector import Severity, Ambiguity


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

        with open(output_file, 'w', encoding='utf-8') as f:
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

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(self.polished_content)


class ReportingStep:
    """
    Step 4-5: Generate report and polished document from ambiguity detection results.

    This class provides methods to generate markdown reports summarizing detected
    ambiguities and create polished versions of documents with clarification markers.

    Usage:
        step = ReportingStep('session_123', 'document.md', 'claude')
        report = step.generate_report(test_results, ambiguities, model_names)
        polished = step.generate_polished_document(document_content, ambiguities)
    """

    def __init__(self, session_id: str, document_path: str, judge_model: str = 'claude'):
        """
        Initialize reporting step.

        Args:
            session_id: Unique identifier for this polishing session
            document_path: Path to original document
            judge_model: Name of judge model used for detection
        """
        self.session_id = session_id
        self.document_path = str(Path(document_path).absolute())
        self.judge_model = judge_model

    def generate_report(
        self,
        test_results: Dict[str, Dict],
        ambiguities: List[Ambiguity],
        model_names: List[str]
    ) -> str:
        """
        Generate markdown report from ambiguity detection results.

        Args:
            test_results: Dict mapping section_id to {section, results}
            ambiguities: List of detected Ambiguity objects
            model_names: List of model names used in testing

        Returns:
            Formatted markdown report as string
        """
        report = f"""# Documentation Polish Report

**Session ID:** {self.session_id}
**Document:** {self.document_path}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Judge Model:** {self.judge_model}

## Summary

- **Sections Tested:** {len(test_results)}
- **Ambiguities Found:** {len(ambiguities)}
- **Models Used:** {', '.join(model_names)}

### Ambiguities by Severity

"""
        # Count by severity
        severity_counts = {s.value: 0 for s in Severity}
        for amb in ambiguities:
            severity_counts[amb.severity.value] += 1

        for sev, count in severity_counts.items():
            emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(sev, '⚪')
            report += f"- {emoji} **{sev.upper()}:** {count}\n"

        report += "\n## Ambiguities Detected\n\n"

        if not ambiguities:
            report += "*No ambiguities detected. The documentation appears clear.*\n"
        else:
            for i, amb in enumerate(ambiguities, 1):
                severity_emoji = {
                    Severity.CRITICAL: '🔴',
                    Severity.HIGH: '🟠',
                    Severity.MEDIUM: '🟡',
                    Severity.LOW: '🟢'
                }.get(amb.severity, '⚪')

                report += f"### {i}. {amb.section_header} {severity_emoji} ({amb.severity.value})\n\n"
                report += f"**Original Text:**\n```\n{amb.section_content[:500]}\n```\n\n"

                report += "**Interpretations:**\n"
                for model_name, interp in amb.interpretations.items():
                    report += f"\n**{model_name}:**\n"
                    report += f"- Understanding: {interp.interpretation[:300]}\n"
                    if interp.steps:
                        report += f"- Steps: {', '.join(interp.steps[:5])}\n"
                    if interp.assumptions:
                        report += f"- Assumptions: {', '.join(interp.assumptions)}\n"
                    if interp.ambiguities:
                        report += f"- Noted ambiguities: {', '.join(interp.ambiguities)}\n"

                # Add comparison details
                if amb.comparison_details:
                    report += f"\n**Analysis:**\n"
                    details = amb.comparison_details.get('details', '')
                    if details:
                        report += f"- {details}\n"

                    key_diffs = amb.comparison_details.get('key_differences', [])
                    if key_diffs:
                        report += f"- Key differences: {', '.join(key_diffs)}\n"

                report += "\n---\n\n"

        # Note about detailed results
        report += "\n---\n\n"
        report += "*For detailed test results, see `test_results.json` in this workspace directory.*\n"

        return report

    def generate_polished_document(
        self,
        document_content: str,
        ambiguities: List[Ambiguity]
    ) -> str:
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
                Severity.CRITICAL: '🔴 CRITICAL',
                Severity.HIGH: '🟠 HIGH',
                Severity.MEDIUM: '🟡 MEDIUM',
                Severity.LOW: '🟢 LOW'
            }.get(amb.severity, '⚠️')

            clarification = f"\n\n> **{severity_marker} - CLARIFICATION NEEDED:**\n"
            clarification += "> Different interpretations were found:\n"

            for model_name, interp in amb.interpretations.items():
                short_interp = interp.interpretation[:150]
                if len(interp.interpretation) > 150:
                    short_interp += "..."
                clarification += f"> - **{model_name}:** {short_interp}\n"

            # Add key differences if available
            key_diffs = amb.comparison_details.get('key_differences', [])
            if key_diffs:
                clarification += f">\n> **Key differences:** {', '.join(key_diffs)}\n"

            # Simple replacement (will be improved in Increment 3)
            if original in content:
                content = content.replace(original, original + clarification, 1)

        return content


# For testing the module directly
if __name__ == '__main__':
    import sys
    import json

    if len(sys.argv) < 4:
        print("Usage: python reporting_step.py <test_results.json> <ambiguities.json> <document.md> [output_report.md]")
        sys.exit(1)

    test_results_file = sys.argv[1]
    ambiguities_file = sys.argv[2]
    document_file = sys.argv[3]
    output_report = sys.argv[4] if len(sys.argv) > 4 else 'report.md'

    # Load test results
    with open(test_results_file, 'r') as f:
        test_results = json.load(f)

    # Load ambiguities
    with open(ambiguities_file, 'r') as f:
        ambiguities_data = json.load(f)

    # Convert ambiguities JSON to Ambiguity objects
    from ambiguity_detector import Interpretation
    ambiguities = []
    for amb_data in ambiguities_data:
        interpretations = {}
        for model_name, interp_data in amb_data['interpretations'].items():
            interpretations[model_name] = Interpretation(
                model_name=model_name,
                raw_response="",
                interpretation=interp_data.get('interpretation', ''),
                steps=interp_data.get('steps', []),
                assumptions=interp_data.get('assumptions', []),
                ambiguities=interp_data.get('ambiguities', [])
            )

        ambiguities.append(Ambiguity(
            section_id=amb_data['section_id'],
            section_header=amb_data['section_header'],
            section_content=amb_data['section_content'],
            severity=Severity(amb_data['severity']),
            interpretations=interpretations,
            comparison_details=amb_data.get('comparison_details', {})
        ))

    # Read document
    with open(document_file, 'r') as f:
        document_content = f.read()

    # Extract model names from test results
    model_names = []
    for section_data in test_results.values():
        if 'results' in section_data:
            model_names = list(section_data['results'].keys())
            break

    # Generate report
    step = ReportingStep('test_session', document_file, 'claude')
    report_content = step.generate_report(test_results, ambiguities, model_names)

    # Save report
    with open(output_report, 'w') as f:
        f.write(report_content)

    print(f"Report generated: {output_report}")
    print(f"Sections tested: {len(test_results)}")
    print(f"Ambiguities found: {len(ambiguities)}")
