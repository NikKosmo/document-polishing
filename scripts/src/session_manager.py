"""Session Manager - Orchestrates model sessions for document-level context"""

import logging
import concurrent.futures
from typing import Dict, Any, Optional

from session_handlers import (
    BaseSessionHandler,
    SessionCreationError,
    SessionLostError,
    SessionQueryError,
    get_session_handler,
)


logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages model sessions for document-level context.

    Creates and maintains sessions per model, allowing section queries
    to have full document context.
    """

    def __init__(self, models_config: Dict[str, Dict[str, Any]], session_config: Dict[str, Any]):
        """
        Initialize SessionManager.

        Args:
            models_config: Configuration for each model (from config.yaml models section)
            session_config: Session management configuration (from config.yaml session_management)
        """
        self.models_config = models_config
        self.session_config = session_config
        self.mode = session_config.get("mode", "auto-recreate")
        self.query_format = session_config.get("query_format", "resend-chunk")
        self.purpose_prompt = session_config.get("purpose_prompt", "")
        self.max_retries = session_config.get("max_retries", 1)
        self.retry_delay = session_config.get("retry_delay_seconds", 2)

        # Active sessions: model_name -> session_id
        self.sessions: Dict[str, str] = {}
        # Session handlers: model_name -> handler instance
        self.handlers: Dict[str, BaseSessionHandler] = {}
        # Document content for session recreation
        self._document: Optional[str] = None
        self._purpose: Optional[str] = None

    def init_session(self, model_name: str, document: str, purpose: str = None) -> str:
        """
        Create session with full document context for a model.

        Args:
            model_name: "claude", "gemini", or "codex"
            document: Full markdown document content
            purpose: System prompt explaining document purpose (overrides config)

        Returns:
            session_id: Session identifier for this model

        Raises:
            SessionCreationError: If session creation fails
        """
        # Store for potential recreation
        self._document = document
        self._purpose = purpose or self.purpose_prompt

        # Get or create handler
        if model_name not in self.handlers:
            model_config = self.models_config.get(model_name, {})
            self.handlers[model_name] = get_session_handler(model_name, model_config)

        handler = self.handlers[model_name]

        try:
            session_id = handler.create_session(document, self._purpose)
            self.sessions[model_name] = session_id
            logger.info(f"Session created for {model_name}: {session_id}")
            return session_id
        except SessionCreationError as e:
            logger.error(f"Failed to create session for {model_name}: {e}")
            raise

    def init_sessions_parallel(
        self, model_names: list, document: str, purpose: str = None
    ) -> Dict[str, str]:
        """
        Create sessions for multiple models in parallel.

        Args:
            model_names: List of model names to initialize
            document: Full markdown document content
            purpose: System prompt explaining document purpose

        Returns:
            Dict of model_name -> session_id for successful inits
        """
        self._document = document
        self._purpose = purpose or self.purpose_prompt
        results = {}

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self.init_session, model, document, self._purpose): model
                for model in model_names
            }
            for future in concurrent.futures.as_completed(futures):
                model = futures[future]
                try:
                    session_id = future.result()
                    results[model] = session_id
                except SessionCreationError as e:
                    logger.error(f"Session init failed for {model}: {e}")
                    # Continue without session for this model

        return results

    def query_in_session(self, model_name: str, prompt: str) -> Dict[str, Any]:
        """
        Query model within existing session.

        Args:
            model_name: Model to query
            prompt: Section-specific prompt

        Returns:
            Model response dict

        Raises:
            SessionLostError: If session no longer valid (and mode is fail-fast)
            SessionQueryError: If query fails after retries
        """
        if model_name not in self.sessions:
            raise SessionQueryError(f"No active session for model: {model_name}")

        session_id = self.sessions[model_name]
        handler = self.handlers[model_name]

        retries = 0
        while retries <= self.max_retries:
            try:
                return handler.query_session(session_id, prompt)
            except SessionLostError as e:
                if self.mode == "auto-recreate" and self._document:
                    logger.warning(f"{model_name} session lost, recreating...")
                    try:
                        self.recreate_session(model_name)
                        session_id = self.sessions[model_name]
                        retries += 1
                        continue
                    except SessionCreationError:
                        raise SessionQueryError(f"Failed to recreate session: {e}")
                else:
                    # fail-fast mode
                    raise
            except SessionQueryError as e:
                retries += 1
                if retries > self.max_retries:
                    logger.error(f"{model_name} query failed after {self.max_retries} retries: {e}")
                    raise
                logger.warning(f"{model_name} query failed, retrying ({retries}/{self.max_retries})...")
                import time
                time.sleep(self.retry_delay)

        raise SessionQueryError(f"Query failed after {self.max_retries} retries")

    def recreate_session(self, model_name: str) -> str:
        """
        Recreate session for a model (for auto-recreate mode).

        Args:
            model_name: Model to recreate session for

        Returns:
            New session_id

        Raises:
            SessionCreationError: If recreation fails
        """
        if not self._document:
            raise SessionCreationError("No document stored for session recreation")

        # Remove old session
        if model_name in self.sessions:
            del self.sessions[model_name]

        # Create new session
        return self.init_session(model_name, self._document, self._purpose)

    def has_session(self, model_name: str) -> bool:
        """Check if model has an active session"""
        return model_name in self.sessions

    def get_session_id(self, model_name: str) -> Optional[str]:
        """Get session ID for a model"""
        return self.sessions.get(model_name)

    def cleanup_sessions(self):
        """
        Cleanup all active sessions.

        Note: Most CLIs don't have explicit session close commands,
        so this mainly clears internal state.
        """
        logger.info(f"Cleaning up {len(self.sessions)} sessions")
        self.sessions.clear()
        self._document = None
        self._purpose = None

    def list_sessions(self) -> Dict[str, str]:
        """List all active sessions"""
        return dict(self.sessions)

    def build_section_prompt(self, section_content: str, analysis_prompt: str) -> str:
        """
        Build prompt for section query based on configured query format.

        Args:
            section_content: The section content to analyze
            analysis_prompt: The analysis question/instructions

        Returns:
            Formatted prompt string
        """
        if self.query_format == "resend-chunk":
            return f"""Analyze the following section from the document:

---
{section_content}
---

{analysis_prompt}"""
        else:
            # reference-header format (Phase 4 optimization)
            # For now, fall back to resend-chunk
            return f"""Analyze the following section from the document:

---
{section_content}
---

{analysis_prompt}"""
