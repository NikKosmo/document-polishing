"""Model Interface - Handles communication with AI models via CLI"""

import subprocess
import json
import time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

from session_manager import SessionManager
from session_handlers import SessionCreationError, SessionQueryError


class ModelInterface(ABC):
    """Abstract base class for model interfaces"""
    
    @abstractmethod
    def query(self, prompt: str) -> Dict[str, Any]:
        """Send a query to the model and return response"""
        pass


class CLIModel(ModelInterface):
    """CLI-based model interface using subprocess"""
    
    def __init__(self, command: str, args: list = None, timeout: int = 30):
        self.command = command
        self.args = args or []
        self.timeout = timeout
        
    def query(self, prompt: str) -> Dict[str, Any]:
        """Execute CLI command with prompt and return parsed response"""
        try:
            # Build command
            cmd = [self.command] + self.args

            # Execute with prompt as stdin
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                return {
                    "error": True,
                    "stderr": result.stderr,
                    "raw_response": result.stdout
                }

            # Try to parse as JSON first
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                # Try stripping markdown code blocks and parsing again
                stripped = self._strip_markdown_code_blocks(result.stdout)
                try:
                    return json.loads(stripped)
                except json.JSONDecodeError:
                    # Return as raw text if still not JSON
                    return {
                        "error": False,
                        "raw_response": result.stdout.strip()
                    }

        except subprocess.TimeoutExpired:
            return {
                "error": True,
                "message": f"Timeout after {self.timeout}s"
            }
        except FileNotFoundError:
            return {
                "error": True,
                "message": f"Command '{self.command}' not found. Is it installed?"
            }
        except Exception as e:
            return {
                "error": True,
                "message": str(e)
            }

    def _strip_markdown_code_blocks(self, text: str) -> str:
        """Strip markdown code blocks from text (e.g., ```json ... ```)"""
        text = text.strip()
        # Remove ```json or ``` at start
        if text.startswith('```json'):
            text = text[7:]
        elif text.startswith('```'):
            text = text[3:]
        # Remove ``` at end
        if text.endswith('```'):
            text = text[:-3]
        return text.strip()


class ModelFactory:
    """Factory for creating model instances"""
    
    @staticmethod
    def create_cli_model(name: str, config: Dict[str, Any]) -> CLIModel:
        """Create a CLI model from configuration"""
        return CLIModel(
            command=config.get('command', name),
            args=config.get('args', []),
            timeout=config.get('timeout', 30)
        )
    
    @staticmethod
    def create(name: str, config: Dict[str, Any]) -> ModelInterface:
        """Create appropriate model interface based on config type"""
        model_type = config.get('type', 'cli')
        
        if model_type == 'cli':
            return ModelFactory.create_cli_model(name, config)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")


class ModelManager:
    """Manages multiple model instances with optional session support"""

    def __init__(self, models_config: Dict[str, Dict[str, Any]], session_config: Dict[str, Any] = None):
        self.models = {}
        self.config = models_config
        self.session_config = session_config or {}
        self.session_manager: Optional[SessionManager] = None
        self._sessions_enabled = self.session_config.get("enabled", False)

        # Initialize enabled models
        for name, config in models_config.items():
            if config.get("enabled", True):
                try:
                    self.models[name] = ModelFactory.create(name, config)
                    print(f"✓ Loaded model: {name}")
                except Exception as e:
                    print(f"✗ Failed to load model {name}: {e}")

    def init_sessions(self, document: str, purpose: str = None, model_names: list = None) -> Dict[str, str]:
        """
        Initialize sessions for models with full document context.

        Args:
            document: Full markdown document content
            purpose: System prompt explaining document purpose
            model_names: List of models to init sessions for (defaults to all available)

        Returns:
            Dict of model_name -> session_id for successful inits
        """
        if not self._sessions_enabled:
            return {}

        if model_names is None:
            model_names = list(self.models.keys())

        self.session_manager = SessionManager(self.config, self.session_config)

        # Initialize sessions in parallel
        results = self.session_manager.init_sessions_parallel(model_names, document, purpose)

        for model, session_id in results.items():
            print(f"✓ Session created for {model}: {session_id[:8]}...")

        failed = set(model_names) - set(results.keys())
        for model in failed:
            print(f"✗ Session failed for {model}, will use stateless mode")

        return results

    def query(self, model_name: str, prompt: str, use_session: bool = True) -> Dict[str, Any]:
        """
        Query a specific model, optionally using session.

        Args:
            model_name: Model to query
            prompt: Query prompt
            use_session: Whether to use session if available (default True)

        Returns:
            Model response dict
        """
        if model_name not in self.models:
            return {
                "error": True,
                "message": f"Model '{model_name}' not available"
            }

        # Try session-based query if enabled and available
        if use_session and self.session_manager and self.session_manager.has_session(model_name):
            try:
                return self.session_manager.query_in_session(model_name, prompt)
            except (SessionQueryError, SessionCreationError) as e:
                print(f"  ⚠ Session query failed for {model_name}, falling back to stateless: {e}")
                # Fall through to stateless query

        # Stateless query (original behavior)
        return self.models[model_name].query(prompt)

    def query_all(self, prompt: str, model_names: list = None, use_session: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Query multiple models with the same prompt.

        Args:
            prompt: Query prompt
            model_names: List of models to query (defaults to all available)
            use_session: Whether to use sessions if available

        Returns:
            Dict of model_name -> response dict
        """
        if model_names is None:
            model_names = list(self.models.keys())

        results = {}
        for name in model_names:
            if name in self.models:
                print(f"  Querying {name}...")
                results[name] = self.query(name, prompt, use_session=use_session)
            else:
                results[name] = {
                    "error": True,
                    "message": f"Model '{name}' not found"
                }

        return results

    def cleanup_sessions(self):
        """Cleanup all active sessions"""
        if self.session_manager:
            self.session_manager.cleanup_sessions()
            print("✓ Sessions cleaned up")

    def sessions_enabled(self) -> bool:
        """Check if session management is enabled"""
        return self._sessions_enabled

    def has_active_sessions(self) -> bool:
        """Check if there are any active sessions"""
        return self.session_manager is not None and len(self.session_manager.sessions) > 0

    def list_available(self) -> list:
        """List available model names"""
        return list(self.models.keys())
