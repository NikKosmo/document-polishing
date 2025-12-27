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
import logging
from pathlib import Path
from datetime import datetime
import json
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from model_interface import ModelManager
from document_processor import DocumentProcessor
from prompt_generator import PromptGenerator
from ambiguity_detector import AmbiguityDetector, Severity, JudgeFailureError

# Import step modules
from extraction_step import ExtractionStep
from session_init_step import SessionInitStep
from testing_step import TestingStep
from detection_step import DetectionStep
from reporting_step import ReportingStep


__version__ = "0.2.0"


class DocumentPolisher:
    """Main polishing orchestrator"""

    def __init__(self, document_path: str, config_path: str = "config.yaml"):
        self.document_path = Path(document_path)
        self.config_path = Path(config_path)

        # Load configuration
        self.config = self._load_config()

        # Get session management config (with defaults)
        self.session_config = self.config.get("session_management", {"enabled": False})

        # Initialize components
        self.model_manager = ModelManager(
            self.config["models"],
            session_config=self.session_config
        )
        self.processor = DocumentProcessor(str(self.document_path))
        self.prompt_gen = PromptGenerator()

        # Setup workspace with document name included
        doc_name = self.document_path.stem
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.session_id = f"polish_{doc_name}_{timestamp}"
        self.workspace = Path(self.config['settings']['workspace_dir']) / self.session_id
        self.workspace.mkdir(parents=True, exist_ok=True)

        # Copy original document to workspace for reference
        original_doc_copy = self.workspace / f"original_{self.document_path.name}"
        shutil.copy2(self.document_path, original_doc_copy)

        # Judge model for LLM-as-Judge strategy
        self.judge_model = 'claude'

        # Setup logging
        self.log_file = self.workspace / "polish.log"
        self._log(f"Session ID: {self.session_id}")
        self._log(f"Workspace: {self.workspace}")
        self._log(f"Document: {self.document_path}")
        self._log(f"Original document copied to: {original_doc_copy}")
        self._log(f"Config loaded from: {self.config_path}")
        self._log(f"Judge model: {self.judge_model}")

        # Setup judge response logger
        self._setup_judge_logger()

        print(f"Session ID: {self.session_id}")
        print(f"Workspace: {self.workspace}")

    def _log(self, message: str):
        """Write to both console and log file"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"

        # Write to log file
        with open(self.log_file, 'a') as f:
            f.write(log_message + '\n')

    def _setup_judge_logger(self):
        """Setup logger for judge responses"""
        judge_logger = logging.getLogger('judge_responses')
        judge_logger.setLevel(logging.INFO)

        # Create file handler
        judge_file = self.workspace / "judge_responses.log"
        handler = logging.FileHandler(judge_file, mode='w')
        handler.setLevel(logging.INFO)

        # Create formatter (just the message, no timestamp prefix)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)

        # Add handler to logger
        judge_logger.addHandler(handler)

        # Prevent propagation to root logger
        judge_logger.propagate = False

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
        extraction_step = ExtractionStep(str(self.document_path))
        extraction_result = extraction_step.extract()
        sections = extraction_result.sections

        # Save extraction result
        extraction_result.save(str(self.workspace / "sections.json"))

        print(f"  Found {len(sections)} sections")
        self._log(f"Found {len(sections)} sections")
        for summary in extraction_result.summary:
            print(f"  {summary}")

        if len(sections) == 0:
            print("\n⚠️  No testable sections found in document")
            return

        # Step 1.5: Initialize sessions (if enabled)
        session_init_result = None
        if self.model_manager.sessions_enabled():
            print(f"\nStep 1.5: Initializing model sessions with document context...")
            self._log("Step 1.5: Initializing model sessions...")
            purpose_prompt = self.session_config.get(
                "purpose_prompt",
                "This document defines standards and requirements. Please analyze sections within this context."
            )
            session_init_step = SessionInitStep(
                self.config['models'],
                self.session_config
            )
            session_init_result = session_init_step.init_sessions(
                extraction_result.document_content,
                models,
                purpose_prompt
            )
            # Transfer session manager to model_manager
            self.model_manager.session_manager = session_init_result.session_manager

            # Save session metadata
            session_init_result.save(str(self.workspace / "session_metadata.json"))
            self._log(f"Sessions initialized: {len(session_init_result.session_ids)} of {len(models)} models")
        else:
            self._log("Session management disabled, using stateless mode")

        # Step 2: Test sections with models
        print(f"\nStep 2: Testing sections with models...")
        self._log("Step 2: Testing sections with models...")
        testing_step = TestingStep(
            self.config['models'],
            self.session_config,
            self.model_manager.session_manager if session_init_result else None
        )

        for i, section in enumerate(sections):
            print(f"\n  Testing section [{i}]: {section['header']}")
            self._log(f"Testing section [{i}]: {section['header']}")

        testing_result = testing_step.test_sections(
            sections,
            models,
            use_sessions=(session_init_result is not None)
        )
        test_results = testing_result.test_results

        # Save test results
        results_file = self.workspace / "test_results.json"
        testing_result.save(str(results_file))
        print(f"\n  Test results saved to: {results_file}")

        # Step 3: Detect ambiguities
        print(f"\nStep 3: Detecting ambiguities...")
        self._log("Step 3: Detecting ambiguities...")
        detection_step = DetectionStep(
            strategy='llm_judge',
            judge_model=self.judge_model,
            models_config=self.config['models'],
            workspace=self.workspace
        )

        try:
            detection_result = detection_step.detect(test_results)
            ambiguities = detection_result.ambiguities
        except JudgeFailureError as e:
            # Fail-fast: Judge failure means we cannot proceed with valid results
            error_msg = f"ERROR: {e}"
            print(f"\n{'='*60}")
            print(f"❌ JUDGE COMPARISON FAILED")
            print(f"{'='*60}")
            print(f"Section: {e.section_id}")
            print(f"Reason: {e.reason}")
            if e.details:
                print(f"Details: {e.details}")
            print(f"\nStopping polish process - cannot proceed without valid judge comparisons.")
            print(f"See logs at: {self.log_file}")
            print(f"{'='*60}\n")

            self._log(error_msg)
            self._log(f"Judge failure - aborting polish process")

            # Cleanup sessions before exit
            if self.model_manager.has_active_sessions():
                self.model_manager.cleanup_sessions()
                self._log("Sessions cleaned up")

            # Return error result instead of continuing with bogus data
            return {
                'workspace': str(self.workspace),
                'report': None,
                'polished': None,
                'ambiguities_found': 0,
                'error': str(e),
                'error_type': 'judge_failure'
            }

        print(f"  Found {len(ambiguities)} potential ambiguities")
        self._log(f"Found {len(ambiguities)} potential ambiguities")

        # Print summary by severity
        if detection_result.severity_counts:
            print(f"  Breakdown: {', '.join(f'{k}: {v}' for k, v in detection_result.severity_counts.items())}")

        # Save ambiguities
        ambiguities_file = self.workspace / "ambiguities.json"
        detection_result.save(str(ambiguities_file))
        print(f"  Ambiguities saved to: {ambiguities_file}")

        # Step 4: Generate report
        print(f"\nStep 4: Generating report...")
        self._log("Step 4: Generating report...")
        reporting_step = ReportingStep(
            self.session_id,
            str(self.document_path),
            self.judge_model
        )
        report_content = reporting_step.generate_report(
            test_results,
            ambiguities,
            models
        )

        report_file = self.workspace / "report.md"
        with open(report_file, 'w') as f:
            f.write(report_content)
        print(f"  Report saved to: {report_file}")
        self._log(f"Report saved to: {report_file}")

        # Step 5: Create polished version (if ambiguities found)
        if ambiguities:
            print(f"\nStep 5: Creating polished version...")
            polished_content = reporting_step.generate_polished_document(
                extraction_result.document_content,
                ambiguities
            )

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
        print(f"Original: {self.workspace / f'original_{self.document_path.name}'}")
        print(f"Report: {report_file}")
        if polished_file:
            print(f"Polished: {polished_file}")

        self._log(f"Polish complete - {len(ambiguities)} ambiguities found")
        self._log(f"Workspace: {self.workspace}")
        self._log(f"Log file: {self.log_file}")

        # Cleanup sessions
        if self.model_manager.has_active_sessions():
            self.model_manager.cleanup_sessions()
            self._log("Sessions cleaned up")

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

        # Note about detailed results
        report += "\n---\n\n"
        report += "*For detailed test results, see `test_results.json` in this workspace directory.*\n"

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