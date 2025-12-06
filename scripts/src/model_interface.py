"""Model Interface - Handles communication with AI models via CLI"""

import subprocess
import json
import time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


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
    """Manages multiple model instances"""
    
    def __init__(self, models_config: Dict[str, Dict[str, Any]]):
        self.models = {}
        self.config = models_config
        
        # Initialize enabled models
        for name, config in models_config.items():
            if config.get('enabled', True):
                try:
                    self.models[name] = ModelFactory.create(name, config)
                    print(f"✓ Loaded model: {name}")
                except Exception as e:
                    print(f"✗ Failed to load model {name}: {e}")
    
    def query(self, model_name: str, prompt: str) -> Dict[str, Any]:
        """Query a specific model"""
        if model_name not in self.models:
            return {
                "error": True,
                "message": f"Model '{model_name}' not available"
            }
        
        return self.models[model_name].query(prompt)
    
    def query_all(self, prompt: str, model_names: list = None) -> Dict[str, Dict[str, Any]]:
        """Query multiple models with the same prompt"""
        if model_names is None:
            model_names = list(self.models.keys())
        
        results = {}
        for name in model_names:
            if name in self.models:
                print(f"  Querying {name}...")
                results[name] = self.query(name, prompt)
            else:
                results[name] = {
                    "error": True,
                    "message": f"Model '{name}' not found"
                }
        
        return results
    
    def list_available(self) -> list:
        """List available model names"""
        return list(self.models.keys())
