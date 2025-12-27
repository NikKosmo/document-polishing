"""
Session Initialization Step - Initialize model sessions with document context

This module provides a clean interface for Step 1.5 of the document polishing pipeline.
It initializes model sessions with full document context to improve interpretation quality.
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path

from session_manager import SessionManager


@dataclass
class SessionInitResult:
    """
    Result of session initialization.

    Contains session IDs for successfully initialized models, list of failed models,
    the SessionManager instance, and whether sessions are enabled.
    """
    session_ids: Dict[str, str] = field(default_factory=dict)
    failed_models: List[str] = field(default_factory=list)
    session_manager: Optional[SessionManager] = None
    enabled: bool = True

    def save(self, output_path: str):
        """
        Save session metadata to JSON file.

        Note: SessionManager instance is not serialized - only metadata.

        Args:
            output_path: Path to output session_metadata.json file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'session_ids': self.session_ids,
            'failed_models': self.failed_models,
            'enabled': self.enabled
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, input_path: str) -> 'SessionInitResult':
        """
        Load session metadata from JSON file.

        Note: SessionManager instance cannot be reconstructed from saved metadata.
        This loads only the metadata (session IDs, failed models, enabled status).

        Args:
            input_path: Path to input session_metadata.json file

        Returns:
            SessionInitResult instance (without SessionManager)

        Raises:
            FileNotFoundError: If input file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Session metadata not found: {input_path}")

        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return cls(
            session_ids=data.get('session_ids', {}),
            failed_models=data.get('failed_models', []),
            session_manager=None,  # Cannot reconstruct from saved file
            enabled=data.get('enabled', True)
        )


class SessionInitStep:
    """
    Step 1.5: Initialize model sessions with document context.

    This class wraps SessionManager to provide a clean interface for initializing
    model sessions with full document context, improving section interpretation quality.

    Usage:
        step = SessionInitStep(models_config, session_config)
        result = step.init_sessions(document_content, ['claude', 'gemini'])
        result.save('session_metadata.json')
    """

    def __init__(self, models_config: Dict, session_config: Dict):
        """
        Initialize session init step.

        Args:
            models_config: Model configuration dict from config.yaml
            session_config: Session management configuration dict
        """
        self.models_config = models_config
        self.session_config = session_config
        self.enabled = session_config.get('enabled', False)

    def init_sessions(
        self,
        document_content: str,
        model_names: List[str],
        purpose_prompt: str = None
    ) -> SessionInitResult:
        """
        Initialize sessions for specified models with document context.

        Args:
            document_content: Full markdown document text
            model_names: List of model names to initialize sessions for
            purpose_prompt: Optional purpose/system prompt (overrides config)

        Returns:
            SessionInitResult containing:
                - session_ids: Dict mapping model names to session IDs
                - failed_models: List of models that failed to initialize
                - session_manager: SessionManager instance (for use in testing step)
                - enabled: Whether sessions are enabled
        """
        # Check if sessions are enabled
        if not self.enabled:
            return SessionInitResult(
                session_ids={},
                failed_models=[],
                session_manager=None,
                enabled=False
            )

        # Use configured purpose prompt if not provided
        if purpose_prompt is None:
            purpose_prompt = self.session_config.get(
                'purpose_prompt',
                'This document defines standards and requirements. Please analyze sections within this context.'
            )

        # Create session manager
        session_manager = SessionManager(self.models_config, self.session_config)

        # Initialize sessions in parallel
        session_results = session_manager.init_sessions_parallel(
            model_names,
            document_content,
            purpose_prompt
        )

        # Determine which models failed
        failed_models = list(set(model_names) - set(session_results.keys()))

        return SessionInitResult(
            session_ids=session_results,
            failed_models=failed_models,
            session_manager=session_manager,
            enabled=True
        )


# Convenience function for simple usage
def initialize_model_sessions(
    document_content: str,
    model_names: List[str],
    models_config: Dict,
    session_config: Dict,
    purpose_prompt: str = None
) -> SessionInitResult:
    """
    Initialize model sessions (convenience function).

    Args:
        document_content: Full document text
        model_names: List of model names
        models_config: Model configuration
        session_config: Session configuration
        purpose_prompt: Optional purpose prompt

    Returns:
        SessionInitResult with session info and SessionManager
    """
    step = SessionInitStep(models_config, session_config)
    return step.init_sessions(document_content, model_names, purpose_prompt)


# For testing the module directly
if __name__ == '__main__':
    import sys
    import yaml

    if len(sys.argv) < 3:
        print("Usage: python session_init_step.py <document.md> <models> [config.yaml] [output.json]")
        print("  Example: python session_init_step.py document.md claude,gemini config.yaml session_metadata.json")
        sys.exit(1)

    document_file = sys.argv[1]
    model_names = [m.strip() for m in sys.argv[2].split(',')]
    config_file = sys.argv[3] if len(sys.argv) > 3 else 'config.yaml'
    output_file = sys.argv[4] if len(sys.argv) > 4 else 'session_metadata.json'

    # Read document
    with open(document_file, 'r') as f:
        document_content = f.read()

    # Load config
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    # Check if sessions are enabled
    session_config = config.get('session_management', {})
    if not session_config.get('enabled', False):
        print("Session management is disabled in config.")
        print("Set session_management.enabled: true in config.yaml to use sessions.")
        sys.exit(1)

    print(f"Initializing sessions for models: {', '.join(model_names)}")
    print(f"Document: {document_file}")

    # Initialize sessions
    step = SessionInitStep(config['models'], session_config)
    result = step.init_sessions(document_content, model_names)

    # Save metadata
    result.save(output_file)

    print(f"\nSession initialization complete!")
    print(f"Successful: {len(result.session_ids)}")
    for model, session_id in result.session_ids.items():
        print(f"  {model}: {session_id[:16]}...")

    if result.failed_models:
        print(f"Failed: {len(result.failed_models)}")
        for model in result.failed_models:
            print(f"  {model}")

    print(f"\nMetadata saved to: {output_file}")
