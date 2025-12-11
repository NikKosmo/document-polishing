"""Unit tests for session management functionality"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import subprocess
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "src"))

from session_handlers import (
    BaseSessionHandler,
    ClaudeSessionHandler,
    GeminiSessionHandler,
    CodexSessionHandler,
    SessionCreationError,
    SessionLostError,
    SessionQueryError,
    get_session_handler,
)
from session_manager import SessionManager


class TestClaudeSessionHandler(unittest.TestCase):
    """Tests for ClaudeSessionHandler"""

    def setUp(self):
        self.config = {
            "command": "claude",
            "args": ["-p"],
            "timeout": 60,
        }
        self.handler = ClaudeSessionHandler(self.config)

    @patch("session_handlers.subprocess.run")
    def test_create_session_success(self, mock_run):
        """Test successful Claude session creation"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"session_id": "test-session-123", "result": "ok"}',
            stderr="",
        )

        session_id = self.handler.create_session("# Test Document", "Analyze this document")

        self.assertEqual(session_id, "test-session-123")
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        self.assertIn("claude", call_args[0][0])
        self.assertIn("--output-format", call_args[0][0])
        self.assertIn("json", call_args[0][0])

    @patch("session_handlers.subprocess.run")
    def test_create_session_failure(self, mock_run):
        """Test Claude session creation failure"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: authentication failed",
        )

        with self.assertRaises(SessionCreationError):
            self.handler.create_session("# Test Document", "Analyze this")

    @patch("session_handlers.subprocess.run")
    def test_create_session_no_session_id(self, mock_run):
        """Test Claude session creation when no session_id in response"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"result": "ok"}',  # No session_id
            stderr="",
        )

        with self.assertRaises(SessionCreationError):
            self.handler.create_session("# Test Document", "Analyze this")

    @patch("session_handlers.subprocess.run")
    def test_query_session_success(self, mock_run):
        """Test successful Claude session query"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"interpretation": "This is my analysis"}',
            stderr="",
        )

        result = self.handler.query_session("test-session-123", "Analyze section 1")

        self.assertEqual(result["interpretation"], "This is my analysis")
        call_args = mock_run.call_args
        self.assertIn("-r", call_args[0][0])
        self.assertIn("test-session-123", call_args[0][0])

    @patch("session_handlers.subprocess.run")
    def test_query_session_lost(self, mock_run):
        """Test Claude session query when session is lost"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: session not found",
        )

        with self.assertRaises(SessionLostError):
            self.handler.query_session("old-session-123", "Analyze section 1")

    @patch("session_handlers.subprocess.run")
    def test_query_session_error(self, mock_run):
        """Test Claude session query with general error"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: rate limit exceeded",
        )

        with self.assertRaises(SessionQueryError):
            self.handler.query_session("test-session-123", "Analyze section 1")


class TestGeminiSessionHandler(unittest.TestCase):
    """Tests for GeminiSessionHandler"""

    def setUp(self):
        self.config = {
            "command": "gemini",
            "args": [],
            "timeout": 60,
        }
        self.handler = GeminiSessionHandler(self.config)

    @patch("session_handlers.subprocess.run")
    def test_create_session_success(self, mock_run):
        """Test that Gemini session is created and returns 'latest'"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Session created",
            stderr="",
        )

        session_id = self.handler.create_session("Test document content", "Test purpose")

        self.assertEqual(session_id, "latest")
        mock_run.assert_called_once()

        # Verify the command was called correctly
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args[0], "gemini")
        self.assertIn("Test document content", call_args[-1])
        self.assertIn("Test purpose", call_args[-1])

    @patch("session_handlers.subprocess.run")
    def test_create_session_failure(self, mock_run):
        """Test that session creation failure raises SessionCreationError"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: API key invalid",
        )

        with self.assertRaises(SessionCreationError) as context:
            self.handler.create_session("Test document", "Test purpose")

        self.assertIn("Gemini session creation failed", str(context.exception))
        self.assertIn("API key invalid", str(context.exception))

    @patch("session_handlers.subprocess.run")
    def test_query_session_success(self, mock_run):
        """Test that Gemini session queries use 'latest'"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"response": "test"}',
            stderr="",
        )

        result = self.handler.query_session("latest", "Test prompt")

        # Verify command uses -r latest
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args, ["gemini", "-r", "latest", "Test prompt"])

    @patch("session_handlers.subprocess.run")
    def test_query_session_lost(self, mock_run):
        """Test that query failure raises SessionLostError for session errors"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: Session not found",
        )

        with self.assertRaises(SessionLostError) as context:
            self.handler.query_session("latest", "Test prompt")

        self.assertIn("Gemini session lost", str(context.exception))

    @patch("session_handlers.subprocess.run")
    def test_query_non_session_error(self, mock_run):
        """Test that non-session errors raise SessionQueryError"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: Rate limit exceeded",
        )

        with self.assertRaises(SessionQueryError) as context:
            self.handler.query_session("latest", "Test prompt")

        self.assertIn("Gemini query failed", str(context.exception))
        self.assertIn("Rate limit exceeded", str(context.exception))


class TestCodexSessionHandler(unittest.TestCase):
    """Tests for CodexSessionHandler"""

    def setUp(self):
        self.config = {
            "command": "codex",
            "args": ["exec", "--skip-git-repo-check"],
            "timeout": 60,
        }
        self.handler = CodexSessionHandler(self.config)

    @patch("session_handlers.subprocess.run")
    def test_create_session_success_with_id(self, mock_run):
        """Test successful Codex session creation with session ID in output"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Starting session...\nsession id: abc-123-def\nDone",
            stderr="",
        )

        session_id = self.handler.create_session("# Test Document", "Analyze this document")

        self.assertEqual(session_id, "abc-123-def")

    @patch("session_handlers.subprocess.run")
    def test_create_session_success_no_id(self, mock_run):
        """Test successful Codex session creation without explicit session ID"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Processing complete",
            stderr="",
        )

        session_id = self.handler.create_session("# Test Document", "Analyze this document")

        self.assertEqual(session_id, "last")  # Falls back to "last"

    @patch("session_handlers.subprocess.run")
    def test_create_session_failure(self, mock_run):
        """Test Codex session creation failure"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: command failed",
        )

        with self.assertRaises(SessionCreationError):
            self.handler.create_session("# Test Document", "Analyze this")

    @patch("session_handlers.subprocess.run")
    def test_query_session_success(self, mock_run):
        """Test successful Codex session query"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"result": "analysis complete"}',
            stderr="",
        )

        result = self.handler.query_session("last", "Analyze section 1")

        self.assertEqual(result["result"], "analysis complete")
        call_args = mock_run.call_args
        self.assertIn("resume", call_args[0][0])
        self.assertIn("--last", call_args[0][0])

    @patch("session_handlers.subprocess.run")
    def test_query_session_lost(self, mock_run):
        """Test Codex session query when no session exists"""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: no session found",
        )

        with self.assertRaises(SessionLostError):
            self.handler.query_session("last", "Analyze section 1")


class TestGetSessionHandler(unittest.TestCase):
    """Tests for get_session_handler factory function"""

    def test_get_claude_handler(self):
        """Test getting Claude session handler"""
        handler = get_session_handler("claude", {"command": "claude"})
        self.assertIsInstance(handler, ClaudeSessionHandler)

    def test_get_gemini_handler(self):
        """Test getting Gemini session handler"""
        handler = get_session_handler("gemini", {"command": "gemini"})
        self.assertIsInstance(handler, GeminiSessionHandler)

    def test_get_codex_handler(self):
        """Test getting Codex session handler"""
        handler = get_session_handler("codex", {"command": "codex"})
        self.assertIsInstance(handler, CodexSessionHandler)

    def test_get_unknown_handler(self):
        """Test getting handler for unknown model"""
        with self.assertRaises(ValueError):
            get_session_handler("unknown_model", {})

    def test_case_insensitive(self):
        """Test handler lookup is case insensitive"""
        handler = get_session_handler("CLAUDE", {"command": "claude"})
        self.assertIsInstance(handler, ClaudeSessionHandler)


class TestSessionManager(unittest.TestCase):
    """Tests for SessionManager"""

    def setUp(self):
        self.models_config = {
            "claude": {"command": "claude", "args": ["-p"], "timeout": 60},
            "gemini": {"command": "gemini", "args": [], "timeout": 60},
        }
        self.session_config = {
            "enabled": True,
            "mode": "auto-recreate",
            "query_format": "resend-chunk",
            "purpose_prompt": "Test document analysis",
            "max_retries": 1,
            "retry_delay_seconds": 0,
        }

    def test_init(self):
        """Test SessionManager initialization"""
        manager = SessionManager(self.models_config, self.session_config)

        self.assertEqual(manager.mode, "auto-recreate")
        self.assertEqual(manager.query_format, "resend-chunk")
        self.assertEqual(manager.max_retries, 1)
        self.assertEqual(len(manager.sessions), 0)

    @patch("session_manager.get_session_handler")
    def test_init_session(self, mock_get_handler):
        """Test single session initialization"""
        mock_handler = MagicMock()
        mock_handler.create_session.return_value = "session-123"
        mock_get_handler.return_value = mock_handler

        manager = SessionManager(self.models_config, self.session_config)
        session_id = manager.init_session("claude", "# Document", "Purpose")

        self.assertEqual(session_id, "session-123")
        self.assertEqual(manager.sessions["claude"], "session-123")
        mock_handler.create_session.assert_called_once_with("# Document", "Purpose")

    @patch("session_manager.get_session_handler")
    def test_init_session_failure(self, mock_get_handler):
        """Test session initialization failure"""
        mock_handler = MagicMock()
        mock_handler.create_session.side_effect = SessionCreationError("Failed")
        mock_get_handler.return_value = mock_handler

        manager = SessionManager(self.models_config, self.session_config)

        with self.assertRaises(SessionCreationError):
            manager.init_session("claude", "# Document", "Purpose")

    @patch("session_manager.get_session_handler")
    def test_query_in_session(self, mock_get_handler):
        """Test querying within session"""
        mock_handler = MagicMock()
        mock_handler.create_session.return_value = "session-123"
        mock_handler.query_session.return_value = {"result": "analysis"}
        mock_get_handler.return_value = mock_handler

        manager = SessionManager(self.models_config, self.session_config)
        manager.init_session("claude", "# Document", "Purpose")
        result = manager.query_in_session("claude", "Analyze this")

        self.assertEqual(result["result"], "analysis")
        mock_handler.query_session.assert_called_once_with("session-123", "Analyze this")

    @patch("session_manager.get_session_handler")
    def test_query_in_session_no_session(self, mock_get_handler):
        """Test querying without active session raises error"""
        manager = SessionManager(self.models_config, self.session_config)

        with self.assertRaises(SessionQueryError):
            manager.query_in_session("claude", "Analyze this")

    @patch("session_manager.get_session_handler")
    def test_auto_recreate_on_session_lost(self, mock_get_handler):
        """Test auto-recreate mode recreates session on SessionLostError"""
        mock_handler = MagicMock()
        mock_handler.create_session.side_effect = ["session-123", "session-456"]
        # First query fails with session lost, second succeeds
        mock_handler.query_session.side_effect = [
            SessionLostError("Session lost"),
            {"result": "success"},
        ]
        mock_get_handler.return_value = mock_handler

        manager = SessionManager(self.models_config, self.session_config)
        manager.init_session("claude", "# Document", "Purpose")
        result = manager.query_in_session("claude", "Analyze this")

        self.assertEqual(result["result"], "success")
        self.assertEqual(mock_handler.create_session.call_count, 2)

    @patch("session_manager.get_session_handler")
    def test_fail_fast_mode(self, mock_get_handler):
        """Test fail-fast mode raises on session lost"""
        mock_handler = MagicMock()
        mock_handler.create_session.return_value = "session-123"
        mock_handler.query_session.side_effect = SessionLostError("Session lost")
        mock_get_handler.return_value = mock_handler

        session_config = self.session_config.copy()
        session_config["mode"] = "fail-fast"

        manager = SessionManager(self.models_config, session_config)
        manager.init_session("claude", "# Document", "Purpose")

        with self.assertRaises(SessionLostError):
            manager.query_in_session("claude", "Analyze this")

    def test_has_session(self):
        """Test has_session check"""
        manager = SessionManager(self.models_config, self.session_config)
        manager.sessions["claude"] = "session-123"

        self.assertTrue(manager.has_session("claude"))
        self.assertFalse(manager.has_session("gemini"))

    def test_cleanup_sessions(self):
        """Test session cleanup"""
        manager = SessionManager(self.models_config, self.session_config)
        manager.sessions["claude"] = "session-123"
        manager.sessions["gemini"] = "session-456"
        manager._document = "# Document"

        manager.cleanup_sessions()

        self.assertEqual(len(manager.sessions), 0)
        self.assertIsNone(manager._document)

    def test_build_section_prompt_resend_chunk(self):
        """Test building section prompt with resend-chunk format"""
        manager = SessionManager(self.models_config, self.session_config)

        prompt = manager.build_section_prompt("Section content here", "What does this mean?")

        self.assertIn("Section content here", prompt)
        self.assertIn("What does this mean?", prompt)
        self.assertIn("---", prompt)

    def test_list_sessions(self):
        """Test listing active sessions"""
        manager = SessionManager(self.models_config, self.session_config)
        manager.sessions["claude"] = "session-123"
        manager.sessions["gemini"] = "session-456"

        sessions = manager.list_sessions()

        self.assertEqual(sessions["claude"], "session-123")
        self.assertEqual(sessions["gemini"], "session-456")


class TestSessionHandlerTimeout(unittest.TestCase):
    """Tests for session handler timeout handling"""

    @patch("session_handlers.subprocess.run")
    def test_timeout_raises_error(self, mock_run):
        """Test that timeout raises SessionQueryError"""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=60)

        handler = ClaudeSessionHandler({"command": "claude", "timeout": 60})

        with self.assertRaises(SessionQueryError) as context:
            handler.create_session("# Doc", "Purpose")

        self.assertIn("timed out", str(context.exception))


class TestSessionHandlerCommandNotFound(unittest.TestCase):
    """Tests for session handler command not found handling"""

    @patch("session_handlers.subprocess.run")
    def test_command_not_found_raises_error(self, mock_run):
        """Test that command not found raises SessionQueryError"""
        mock_run.side_effect = FileNotFoundError()

        handler = ClaudeSessionHandler({"command": "nonexistent", "timeout": 60})

        with self.assertRaises(SessionQueryError) as context:
            handler.create_session("# Doc", "Purpose")

        self.assertIn("not found", str(context.exception))


if __name__ == "__main__":
    unittest.main()
