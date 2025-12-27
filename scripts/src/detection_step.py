"""
Detection Step - Detect ambiguities in model interpretations

This module provides a clean interface for Step 3 of the document polishing pipeline.
It uses ambiguity detection strategies (LLM-as-Judge or simple comparison) to identify
disagreements between model interpretations.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from pathlib import Path

from ambiguity_detector import (
    AmbiguityDetector,
    Ambiguity,
    Severity,
    JudgeFailureError
)
from model_interface import ModelManager


# Setup judge logger
def _setup_judge_logger(workspace: Path):
    """Setup logger for judge responses"""
    judge_logger = logging.getLogger('judge_responses')
    judge_logger.setLevel(logging.INFO)

    # Remove existing handlers
    judge_logger.handlers = []

    # Add file handler
    log_file = workspace / "judge_responses.log"
    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter('%(message)s'))
    judge_logger.addHandler(handler)

    return judge_logger


@dataclass
class DetectionResult:
    """
    Result of ambiguity detection.

    Contains detected ambiguities, severity counts, and metadata about
    the detection strategy used.
    """
    ambiguities: List[Ambiguity] = field(default_factory=list)
    severity_counts: Dict[str, int] = field(default_factory=dict)
    strategy: str = "llm_judge"
    judge_model: Optional[str] = None

    def save(self, output_path: str):
        """
        Save ambiguities to JSON file.

        Args:
            output_path: Path to output ambiguities.json file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        ambiguities_data = [amb.to_dict() for amb in self.ambiguities]

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(ambiguities_data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, input_path: str) -> 'DetectionResult':
        """
        Load ambiguities from JSON file.

        Args:
            input_path: Path to input ambiguities.json file

        Returns:
            DetectionResult instance

        Raises:
            FileNotFoundError: If input file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        from ambiguity_detector import Interpretation

        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Ambiguities file not found: {input_path}")

        with open(input_file, 'r', encoding='utf-8') as f:
            ambiguities_data = json.load(f)

        # Convert JSON to Ambiguity objects
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

        # Calculate severity counts
        severity_counts = {}
        for amb in ambiguities:
            sev = amb.severity.value
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        return cls(
            ambiguities=ambiguities,
            severity_counts=severity_counts,
            strategy="unknown",  # Can't determine from saved file
            judge_model=None
        )


class DetectionStep:
    """
    Step 3: Detect ambiguities in model interpretations.

    This class wraps AmbiguityDetector to provide a clean interface for
    detecting disagreements between model interpretations using different strategies.

    Usage:
        step = DetectionStep('llm_judge', 'claude', models_config, workspace=workspace_path)
        result = step.detect(test_results)  # May raise JudgeFailureError
        result.save('ambiguities.json')
    """

    def __init__(
        self,
        strategy: str = 'llm_judge',
        judge_model: str = 'claude',
        models_config: Dict = None,
        session_manager=None,
        workspace: Path = None
    ):
        """
        Initialize detection step.

        Args:
            strategy: Detection strategy - 'llm_judge' or 'simple'
            judge_model: Name of model to use as judge (for llm_judge strategy)
            models_config: Model configuration dict from config.yaml
            session_manager: Optional SessionManager instance
            workspace: Optional workspace directory for judge response logging
        """
        self.strategy = strategy
        self.judge_model = judge_model
        self.models_config = models_config or {}
        self.workspace = Path(workspace) if workspace else Path.cwd()

        # Setup judge logger if workspace provided
        if workspace:
            _setup_judge_logger(self.workspace)

        # Initialize model manager if needed for judge queries
        self.model_manager = None
        if strategy == 'llm_judge' and models_config:
            self.model_manager = ModelManager(models_config, {})
            if session_manager:
                self.model_manager.session_manager = session_manager

    def _create_judge_query_func(self) -> Callable:
        """
        Create query function for LLM-as-Judge strategy.

        Returns:
            Function that takes a prompt and returns model response
        """
        if not self.model_manager:
            raise ValueError("Model manager not initialized for llm_judge strategy")

        def query_func(prompt: str):
            return self.model_manager.query(self.judge_model, prompt, use_session=False)

        return query_func

    def detect(self, test_results: Dict[str, Dict]) -> DetectionResult:
        """
        Detect ambiguities in test results.

        Args:
            test_results: Dict mapping section_id to {section, results}

        Returns:
            DetectionResult with detected ambiguities and metadata

        Raises:
            JudgeFailureError: If LLM judge fails (timeout, invalid response, etc.)
                              This triggers fail-fast behavior - caller should stop processing.
        """
        # Create ambiguity detector with appropriate strategy
        if self.strategy == 'llm_judge':
            if not self.model_manager:
                raise ValueError("Model manager required for llm_judge strategy")

            if self.judge_model not in self.model_manager.list_available():
                raise ValueError(f"Judge model '{self.judge_model}' not available")

            detector = AmbiguityDetector(
                strategy='llm_judge',
                llm_query_func=self._create_judge_query_func()
            )
        elif self.strategy == 'simple':
            detector = AmbiguityDetector(
                strategy='simple',
                similarity_threshold=0.7
            )
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

        # Detect ambiguities (may raise JudgeFailureError)
        ambiguities = detector.detect(test_results)

        # Calculate severity counts
        severity_counts = {}
        for amb in ambiguities:
            sev = amb.severity.value
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        return DetectionResult(
            ambiguities=ambiguities,
            severity_counts=severity_counts,
            strategy=self.strategy,
            judge_model=self.judge_model if self.strategy == 'llm_judge' else None
        )


# Convenience function for simple usage
def detect_ambiguities_in_results(
    test_results: Dict[str, Dict],
    strategy: str = 'llm_judge',
    judge_model: str = 'claude',
    models_config: Dict = None
) -> DetectionResult:
    """
    Detect ambiguities in test results (convenience function).

    Args:
        test_results: Dict mapping section_id to {section, results}
        strategy: Detection strategy - 'llm_judge' or 'simple'
        judge_model: Judge model name (for llm_judge strategy)
        models_config: Model configuration

    Returns:
        DetectionResult with detected ambiguities

    Raises:
        JudgeFailureError: If judge fails
    """
    step = DetectionStep(strategy, judge_model, models_config)
    return step.detect(test_results)


# For testing the module directly
if __name__ == '__main__':
    import sys
    import yaml

    if len(sys.argv) < 2:
        print("Usage: python detection_step.py <test_results.json> [config.yaml] [judge_model] [output.json]")
        print("  Example: python detection_step.py test_results.json config.yaml claude ambiguities.json")
        sys.exit(1)

    test_results_file = sys.argv[1]
    config_file = sys.argv[2] if len(sys.argv) > 2 else 'config.yaml'
    judge_model = sys.argv[3] if len(sys.argv) > 3 else 'claude'
    output_file = sys.argv[4] if len(sys.argv) > 4 else 'ambiguities.json'

    # Load test results
    with open(test_results_file, 'r') as f:
        test_results = json.load(f)

    # Load config
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    print(f"Detecting ambiguities in {len(test_results)} sections...")
    print(f"Strategy: llm_judge (judge: {judge_model})")

    # Detect ambiguities
    try:
        step = DetectionStep('llm_judge', judge_model, config['models'])
        result = step.detect(test_results)

        # Save results
        result.save(output_file)

        print(f"\nDetection complete!")
        print(f"Ambiguities found: {len(result.ambiguities)}")
        if result.severity_counts:
            print(f"Breakdown: {', '.join(f'{k}: {v}' for k, v in result.severity_counts.items())}")
        print(f"Results saved to: {output_file}")

    except JudgeFailureError as e:
        print(f"\nERROR: Judge comparison failed!")
        print(f"Section: {e.section_id}")
        print(f"Reason: {e.reason}")
        if e.details:
            print(f"Details: {e.details}")
        sys.exit(1)
