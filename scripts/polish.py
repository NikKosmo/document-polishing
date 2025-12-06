#!/usr/bin/env python3
"""
Documentation Polishing System - Main Entry Point

Usage:
    python polish.py <document.md> [options]
    python polish.py --list-models
    python polish.py --version
"""

import sys
import argparse
import yaml
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from model_interface import ModelManager
from document_processor import DocumentProcessor
from prompt_generator import PromptGenerator
from ambiguity_detector import AmbiguityDetector, Severity


__version__ = "0.2.0"


class DocumentPolisher:
    """Main polishing orchestrator"""

    def __init__(self, document_path: str, config_path: str = "config.yaml"):
        self.document_path = Path(document_path)
        self.config_path = Path(config_path)

        # Load configuration
        self.config = self._load_config()

        # Initialize components
        self.model_manager = ModelManager(self.config['models'])
        self.processor = DocumentProcessor(str(self.document_path))
        self.prompt_gen = PromptGenerator()

        # Setup workspace with document name included
        doc_name = self.document_path.stem
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.session_id = f"polish_{doc_name}_{timestamp}"
        self.workspace = Path(self.config['settings']['workspace_dir']) / self.session_id
        self.workspace.mkdir(parents=True, exist_ok=True)

        # Judge model for LLM-as-Judge strategy
        self.judge_model = 'claude'

        # Setup logging
        self.log_file = self.workspace / "polish.log"
        self._log(f"Session ID: {self.session_id}")
        self._log(f"Workspace: {self.workspace}")
        self._log(f"Document: {self.document_path}")
        self._log(f"Config loaded from: {self.config_path}")
        self._log(f"Judge model: {self.judge_model}")

        print(f"Session ID: {self.session_id}")
        print(f"Workspace: {self.workspace}")

    def _log(self, message: str):
        """Write to both console and log file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"

        # Write to log file
        with open(self.log_file, 'a') as f:
            f.write(log_message + '\n')

    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            print(f"ERROR: Config file not found: {self.config_path}")
            print(f"Please create config.yaml or specify path with --config")
            sys.exit(1)

        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def _create_judge_query_func(self):
        """Create a query function for the LLM judge"""
        def query_func(prompt: str):
            return self.model_manager.query(self.judge_model, prompt)
        return query_func

    def _create_ambiguity_detector(self) -> AmbiguityDetector:
        """Create ambiguity detector with appropriate strategy"""
        # Check if judge model is available
        if self.judge_model in self.model_manager.list_available():
            print(f"  Using LLM-as-Judge strategy (judge: {self.judge_model})")
            return AmbiguityDetector(
                strategy='llm_judge',
                llm_query_func=self._create_judge_query_func()
            )
        else:
            print(f"  Judge model '{self.judge_model}' not available, using simple strategy")
            return AmbiguityDetector(strategy='simple', similarity_threshold=0.7)

    def polish(self, models: list = None, profile: str = None):
        """Run the polishing process"""
        print(f"\n{'='*60}")
        print(f"Starting Documentation Polish")
        print(f"Document: {self.document_path}")
        print(f"{'='*60}\n")

        # Determine which models to use
        if models is None:
            if profile:
                models = self.config['profiles'][profile]['models']
            else:
                default_profile = self.config['settings']['default_profile']
                models = self.config['profiles'][default_profile]['models']

        print(f"Using models: {', '.join(models)}\n")
        self._log(f"Using models: {', '.join(models)}")

        # Step 1: Extract sections
        print("Step 1: Extracting testable sections...")
        self._log("Step 1: Extracting testable sections...")
        sections = self.processor.extract_sections()
        print(f"  Found {len(sections)} sections")
        self._log(f"Found {len(sections)} sections")
        for i, summary in enumerate(self.processor.get_section_summary()):
            print(f"  {summary}")

        if len(sections) == 0:
            print("\n⚠️  No testable sections found in document")
            return

        # Step 2: Test sections with models
        print(f"\nStep 2: Testing sections with models...")
        self._log("Step 2: Testing sections with models...")
        test_results = {}

        for i, section in enumerate(sections):
            print(f"\n  Testing section [{i}]: {section['header']}")
            self._log(f"Testing section [{i}]: {section['header']}")
            prompt = self.prompt_gen.create_interpretation_prompt(section)

            # Query all models
            results = self.model_manager.query_all(prompt, models)
            self._log(f"Section [{i}] completed - queried {len(results)} models")
            test_results[f"section_{i}"] = {
                'section': section,
                'results': results
            }

        # Save test results
        results_file = self.workspace / "test_results.json"
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        print(f"\n  Test results saved to: {results_file}")

        # Step 3: Detect ambiguities using ambiguity_detector module
        print(f"\nStep 3: Detecting ambiguities...")
        self._log("Step 3: Detecting ambiguities...")
        detector = self._create_ambiguity_detector()
        ambiguities = detector.detect(test_results)
        print(f"  Found {len(ambiguities)} potential ambiguities")
        self._log(f"Found {len(ambiguities)} potential ambiguities")

        # Print summary by severity
        severity_counts = {}
        for amb in ambiguities:
            sev = amb.severity.value
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        if severity_counts:
            print(f"  Breakdown: {', '.join(f'{k}: {v}' for k, v in severity_counts.items())}")

        # Save ambiguities
        ambiguities_file = self.workspace / "ambiguities.json"
        with open(ambiguities_file, 'w') as f:
            json.dump([a.to_dict() for a in ambiguities], f, indent=2)
        print(f"  Ambiguities saved to: {ambiguities_file}")

        # Step 4: Generate report
        print(f"\nStep 4: Generating report...")
        self._log("Step 4: Generating report...")
        report = self._generate_report(test_results, ambiguities)

        report_file = self.workspace / "report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"  Report saved to: {report_file}")
        self._log(f"Report saved to: {report_file}")

        # Step 5: Create polished version (if ambiguities found)
        if ambiguities:
            print(f"\nStep 5: Creating polished version...")
            polished_content = self._create_polished_version(ambiguities)

            polished_file = self.workspace / f"{self.document_path.stem}_polished.md"
            with open(polished_file, 'w') as f:
                f.write(polished_content)
            print(f"  Polished document saved to: {polished_file}")
        else:
            print(f"\n✓ No ambiguities found - document is clear!")
            polished_file = None

        # Summary
        print(f"\n{'='*60}")
        print(f"Polish Complete!")
        print(f"{'='*60}")
        print(f"Workspace: {self.workspace}")
        print(f"Report: {report_file}")
        if polished_file:
            print(f"Polished: {polished_file}")

        self._log(f"Polish complete - {len(ambiguities)} ambiguities found")
        self._log(f"Workspace: {self.workspace}")
        self._log(f"Log file: {self.log_file}")
        print()

        return {
            'workspace': str(self.workspace),
            'report': str(report_file),
            'polished': str(polished_file) if polished_file else None,
            'ambiguities_found': len(ambiguities)
        }

    def _generate_report(self, test_results: dict, ambiguities: list) -> str:
        """Generate markdown report"""
        report = f"""# Documentation Polish Report

            **Session ID:** {self.session_id}
            **Document:** {self.document_path}
            **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            **Judge Model:** {self.judge_model}

## Summary

            - **Sections Tested:** {len(test_results)}
            - **Ambiguities Found:** {len(ambiguities)}
            - **Models Used:** {', '.join(self.model_manager.list_available())}

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

        # Detailed results section
        report += "\n## Detailed Test Results\n\n"
        report += "<details>\n<summary>Click to expand raw results</summary>\n\n"

        for section_id, data in test_results.items():
            section = data['section']
            report += f"### {section['header']}\n\n"

            for model, response in data['results'].items():
                report += f"**{model}:**\n"
                if isinstance(response, dict) and response.get('error'):
                    report += f"- Error: {response.get('message', 'Unknown error')}\n"
                else:
                    # Truncate long responses
                    resp_str = json.dumps(response, indent=2, default=str)
                    if len(resp_str) > 1000:
                        resp_str = resp_str[:1000] + "\n... (truncated)"
                    report += f"```json\n{resp_str}\n```\n"
                report += "\n"

        report += "</details>\n"

        return report

    def _create_polished_version(self, ambiguities: list) -> str:
        """Create polished version with clarifications"""
        content = self.processor.get_full_content()

        # For now, add clarification notes after ambiguous sections
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


def main():
    parser = argparse.ArgumentParser(
        description='Documentation Polishing System',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('document', nargs='?', help='Path to markdown document')
    parser.add_argument('--models', help='Comma-separated list of models to use')
    parser.add_argument('--profile', help='Profile to use (quick, standard, thorough)')
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    parser.add_argument('--list-models', action='store_true', help='List available models')
    parser.add_argument('--version', action='store_true', help='Show version')
    parser.add_argument('--judge', default='claude', help='Model to use as judge (default: claude)')

    args = parser.parse_args()

    if args.version:
        print(f"Documentation Polishing System v{__version__}")
        return

    if args.list_models:
        config_path = Path(args.config)
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
            print("Available models:")
            for name, cfg in config['models'].items():
                status = "✓" if cfg.get('enabled', True) else "✗"
                print(f"  {status} {name} ({cfg.get('type', 'unknown')})")
        else:
            print("Config file not found")
        return

    if not args.document:
        parser.print_help()
        return

    # Parse models if provided
    models = None
    if args.models:
        models = [m.strip() for m in args.models.split(',')]

    # Run polishing
    polisher = DocumentPolisher(args.document, args.config)

    # Set judge model if specified
    if args.judge:
        polisher.judge_model = args.judge

    result = polisher.polish(models=models, profile=args.profile)


if __name__ == "__main__":
    main()