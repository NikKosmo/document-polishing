"""
Testing Step - Test sections with AI models

This module provides a clean interface for Step 2 of the document polishing pipeline.
It queries multiple AI models to collect their interpretations of documentation sections.
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path

from model_interface import ModelManager
from prompt_generator import PromptGenerator
from session_manager import SessionManager


@dataclass
class TestingResult:
    """
    Result of testing sections with AI models.

    Contains test results mapping section IDs to section data and model responses,
    along with metadata about which models were tested and how many sections.
    """
    test_results: Dict[str, Dict] = field(default_factory=dict)
    model_names: List[str] = field(default_factory=list)
    sections_tested: int = 0

    def save(self, output_path: str):
        """
        Save testing result to JSON file.

        Args:
            output_path: Path to output test_results.json file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, default=str, ensure_ascii=False)

    @classmethod
    def load(cls, input_path: str) -> 'TestingResult':
        """
        Load testing result from JSON file.

        Args:
            input_path: Path to input test_results.json file

        Returns:
            TestingResult instance

        Raises:
            FileNotFoundError: If input file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Testing result not found: {input_path}")

        with open(input_file, 'r', encoding='utf-8') as f:
            test_results = json.load(f)

        # Extract model names from first section
        model_names = []
        sections_tested = len(test_results)

        for section_data in test_results.values():
            if 'results' in section_data:
                model_names = list(section_data['results'].keys())
                break

        return cls(
            test_results=test_results,
            model_names=model_names,
            sections_tested=sections_tested
        )


class TestingStep:
    """
    Step 2: Test documentation sections with AI models.

    This class wraps ModelManager and PromptGenerator to provide a clean interface
    for testing sections and collecting model interpretations.

    Usage:
        step = TestingStep(models_config, session_config, session_manager)
        result = step.test_sections(sections, ['claude', 'gemini'])
        result.save('test_results.json')
    """

    def __init__(
        self,
        models_config: Dict,
        session_config: Dict = None,
        session_manager: SessionManager = None
    ):
        """
        Initialize testing step.

        Args:
            models_config: Model configuration dict from config.yaml
            session_config: Optional session management configuration
            session_manager: Optional pre-initialized SessionManager instance
        """
        self.models_config = models_config
        self.session_config = session_config or {}

        # Initialize ModelManager
        self.model_manager = ModelManager(models_config, session_config)

        # Use provided session manager if available
        if session_manager:
            self.model_manager.session_manager = session_manager

        # Initialize PromptGenerator
        self.prompt_gen = PromptGenerator()

    def test_sections(
        self,
        sections: List[Dict],
        model_names: List[str],
        use_sessions: bool = True
    ) -> TestingResult:
        """
        Test sections with multiple AI models.

        Queries each model for every section and collects interpretations.

        Args:
            sections: List of section dicts from extraction step
            model_names: List of model names to query
            use_sessions: Whether to use session management if available

        Returns:
            TestingResult containing test_results dict and metadata
        """
        test_results = {}

        for i, section in enumerate(sections):
            section_id = f"section_{i}"

            # Generate prompt for this section
            prompt = self.prompt_gen.create_interpretation_prompt(section)

            # Query all models
            results = self.model_manager.query_all(
                prompt,
                model_names,
                use_session=use_sessions
            )

            # Store results
            test_results[section_id] = {
                'section': section,
                'results': results
            }

        return TestingResult(
            test_results=test_results,
            model_names=model_names,
            sections_tested=len(sections)
        )


# Convenience function for simple usage
def test_sections_with_models(
    sections: List[Dict],
    model_names: List[str],
    models_config: Dict,
    session_config: Dict = None
) -> TestingResult:
    """
    Test sections with models (convenience function).

    Args:
        sections: List of section dicts
        model_names: List of model names to query
        models_config: Model configuration
        session_config: Optional session configuration

    Returns:
        TestingResult with test results and metadata
    """
    step = TestingStep(models_config, session_config)
    return step.test_sections(sections, model_names)


# For testing the module directly
if __name__ == '__main__':
    import sys
    import yaml

    if len(sys.argv) < 3:
        print("Usage: python testing_step.py <sections.json> <models> [config.yaml] [output.json]")
        print("  Example: python testing_step.py sections.json claude,gemini config.yaml test_results.json")
        sys.exit(1)

    sections_file = sys.argv[1]
    model_names = [m.strip() for m in sys.argv[2].split(',')]
    config_file = sys.argv[3] if len(sys.argv) > 3 else 'config.yaml'
    output_file = sys.argv[4] if len(sys.argv) > 4 else 'test_results.json'

    # Load sections
    with open(sections_file, 'r') as f:
        sections_data = json.load(f)
        sections = sections_data.get('sections', sections_data)

    # Load config
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    print(f"Testing {len(sections)} sections with models: {', '.join(model_names)}")

    # Test sections
    step = TestingStep(config['models'], config.get('session_management', {}))
    result = step.test_sections(sections, model_names, use_sessions=False)

    # Save results
    result.save(output_file)

    print(f"\nTesting complete!")
    print(f"Sections tested: {result.sections_tested}")
    print(f"Models used: {', '.join(result.model_names)}")
    print(f"Results saved to: {output_file}")
