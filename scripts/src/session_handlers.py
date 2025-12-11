"""Session Handlers - Model-specific session management implementations"""

import subprocess
import json
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class SessionError(Exception):
    """Base exception for session errors"""
    pass


class SessionCreationError(SessionError):
    """Failed to create session"""
    pass


class SessionLostError(SessionError):
    """Session no longer valid"""
    pass


class SessionQueryError(SessionError):
    """Query failed within session"""
    pass


class BaseSessionHandler(ABC):
    """Abstract base class for model session handlers"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.timeout = config.get("timeout", 60)

    @abstractmethod
    def create_session(self, document: str, purpose: str) -> str:
        """
        Create session with document context.

        Args:
            document: Full markdown document content
            purpose: System prompt explaining document purpose

        Returns:
            session_id: Session identifier

        Raises:
            SessionCreationError: If session creation fails
        """
        pass

    @abstractmethod
    def query_session(self, session_id: str, prompt: str) -> Dict[str, Any]:
        """
        Query within existing session.

        Args:
            session_id: Session identifier
            prompt: Query prompt

        Returns:
            Model response dict

        Raises:
            SessionLostError: If session no longer valid
            SessionQueryError: If query fails
        """
        pass

    def _run_command(self, cmd: list, input_text: str = None) -> subprocess.CompletedProcess:
        """Execute command with optional input"""
        try:
            result = subprocess.run(
                cmd,
                input=input_text,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            return result
        except subprocess.TimeoutExpired:
            raise SessionQueryError(f"Command timed out after {self.timeout}s")
        except FileNotFoundError:
            raise SessionQueryError(f"Command '{cmd[0]}' not found. Is it installed?")

    def _parse_response(self, stdout: str) -> Dict[str, Any]:
        """Parse response, attempting JSON first"""
        stdout = stdout.strip()
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            # Try stripping markdown code blocks
            stripped = self._strip_markdown_code_blocks(stdout)
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return {"raw_response": stdout}

    def _strip_markdown_code_blocks(self, text: str) -> str:
        """Strip markdown code blocks from text"""
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()


class ClaudeSessionHandler(BaseSessionHandler):
    """Session management for Claude CLI"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.command = config.get("command", "claude")
        self.args = config.get("args", ["-p"])

    def create_session(self, document: str, purpose: str) -> str:
        """
        Create Claude session with document context.

        Uses --output-format json to get session_id from response.
        """
        init_prompt = f"{purpose}\n\nHere is the full document:\n\n{document}"

        cmd = [self.command] + self.args + ["--output-format", "json", init_prompt]

        result = self._run_command(cmd, input_text=None)

        if result.returncode != 0:
            raise SessionCreationError(f"Claude session creation failed: {result.stderr}")

        # Parse JSON response to extract session_id
        try:
            response = json.loads(result.stdout)
            session_id = response.get("session_id")
            if not session_id:
                raise SessionCreationError("No session_id in Claude response")
            return session_id
        except json.JSONDecodeError:
            raise SessionCreationError(f"Failed to parse Claude response: {result.stdout[:200]}")

    def query_session(self, session_id: str, prompt: str) -> Dict[str, Any]:
        """
        Query within existing Claude session.

        Uses -r SESSION_ID to continue session.
        """
        cmd = [self.command] + self.args + ["-r", session_id, prompt]

        result = self._run_command(cmd, input_text=None)

        if result.returncode != 0:
            # Check if session lost
            if "session" in result.stderr.lower() and ("not found" in result.stderr.lower() or "invalid" in result.stderr.lower()):
                raise SessionLostError(f"Claude session {session_id} lost: {result.stderr}")
            raise SessionQueryError(f"Claude query failed: {result.stderr}")

        return self._parse_response(result.stdout)


class GeminiSessionHandler(BaseSessionHandler):
    """Session management for Gemini CLI"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.command = config.get("command", "gemini")
        self.args = config.get("args", [])
        self._session_num = None  # Gemini uses numeric session IDs

    def create_session(self, document: str, purpose: str) -> str:
        """
        Create Gemini session with document context.

        Gemini auto-creates sessions. We use 'latest' to reference
        the most recently created session.
        """
        init_prompt = f"{purpose}\n\nHere is the full document:\n\n{document}"

        cmd = [self.command] + self.args + [init_prompt]

        result = self._run_command(cmd, input_text=None)

        if result.returncode != 0:
            raise SessionCreationError(f"Gemini session creation failed: {result.stderr}")

        # Return "latest" as session identifier
        return "latest"

    def query_session(self, session_id: str, prompt: str) -> Dict[str, Any]:
        """
        Query within existing Gemini session.

        Always uses 'latest' to reference the most recent session.
        """
        cmd = [self.command, "-r", "latest", prompt]

        result = self._run_command(cmd, input_text=None)

        if result.returncode != 0:
            if "session" in result.stderr.lower() and ("not found" in result.stderr.lower() or "invalid" in result.stderr.lower()):
                raise SessionLostError(f"Gemini session lost: {result.stderr}")
            raise SessionQueryError(f"Gemini query failed: {result.stderr}")

        return self._parse_response(result.stdout)


class CodexSessionHandler(BaseSessionHandler):
    """Session management for Codex CLI"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.command = config.get("command", "codex")
        self.args = config.get("args", ["exec", "--skip-git-repo-check"])
        self._session_id = None

    def create_session(self, document: str, purpose: str) -> str:
        """
        Create Codex session with document context.

        Codex auto-creates session on first call, session ID shown in output.
        Note: Codex only maintains one session at a time per working directory.
        """
        init_prompt = f"{purpose}\n\nHere is the full document:\n\n{document}"

        cmd = [self.command] + self.args + [init_prompt]

        result = self._run_command(cmd, input_text=None)

        if result.returncode != 0:
            raise SessionCreationError(f"Codex session creation failed: {result.stderr}")

        # Extract session_id from output (look for "session id:" line)
        session_id = self._extract_session_id(result.stdout + result.stderr)
        if session_id:
            self._session_id = session_id
            return session_id

        # If no explicit session ID found, use "last" as identifier
        self._session_id = "last"
        return "last"

    def _extract_session_id(self, output: str) -> Optional[str]:
        """Extract session ID from Codex output"""
        # Look for pattern like "session id: <uuid>" or "Session ID: <uuid>"
        match = re.search(r"session\s*id:\s*([a-f0-9-]+)", output, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def query_session(self, session_id: str, prompt: str) -> Dict[str, Any]:
        """
        Query within existing Codex session.

        Uses 'resume --last' to continue most recent session.
        Note: Always uses --last due to Codex CLI limitation.
        """
        cmd = [self.command] + self.args + ["resume", "--last", prompt]

        result = self._run_command(cmd, input_text=None)

        if result.returncode != 0:
            if "session" in result.stderr.lower() and ("not found" in result.stderr.lower() or "no" in result.stderr.lower()):
                raise SessionLostError(f"Codex session lost: {result.stderr}")
            raise SessionQueryError(f"Codex query failed: {result.stderr}")

        return self._parse_response(result.stdout)


def get_session_handler(model_name: str, config: Dict[str, Any]) -> BaseSessionHandler:
    """
    Factory function to create appropriate session handler for model.

    Args:
        model_name: "claude", "gemini", or "codex"
        config: Model configuration dict

    Returns:
        Appropriate session handler instance

    Raises:
        ValueError: If model not supported
    """
    handlers = {
        "claude": ClaudeSessionHandler,
        "gemini": GeminiSessionHandler,
        "codex": CodexSessionHandler,
    }

    handler_class = handlers.get(model_name.lower())
    if handler_class is None:
        raise ValueError(f"No session handler for model: {model_name}")

    return handler_class(config)
