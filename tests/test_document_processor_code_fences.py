"""Tests for DocumentProcessor code fence handling in extract_sections()."""

import sys
import tempfile
import textwrap
from pathlib import Path

# Make scripts/src importable
project_root = Path(__file__).resolve().parents[1]
scripts_src = project_root.joinpath("scripts", "src")
sys.path.insert(0, scripts_src.as_posix())

from document_processor import DocumentProcessor


class TestCodeFenceHandling:
    """Tests for code fence aware section extraction."""

    def test_header_inside_code_fence_not_treated_as_section_break(self):
        """Headers inside code fences should not create new sections."""
        content = textwrap.dedent("""\
            # Main Section

            Some content here.

            ```markdown
            ## This is inside a code fence

            Should not be a section break.
            ```

            More content after the fence.
        """)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            processor = DocumentProcessor(f.name)
            sections = processor.extract_sections()

        # Should have only 1 section (Main Section)
        assert len(sections) == 1
        assert sections[0]["header"] == "Main Section"
        # Content should include everything including the code fence
        assert "## This is inside a code fence" in sections[0]["content"]
        assert "More content after the fence" in sections[0]["content"]

    def test_header_after_code_fence_creates_new_section(self):
        """Headers after code fences should create new sections."""
        content = textwrap.dedent("""\
            # First Section

            You must run this code:

            ```python
            print("hello")
            ```

            # Second Section

            You should verify the output.
        """)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            processor = DocumentProcessor(f.name)
            sections = processor.extract_sections()

        # Should have 2 sections
        assert len(sections) == 2
        assert sections[0]["header"] == "First Section"
        assert sections[1]["header"] == "Second Section"

    def test_multiple_code_fences_with_headers(self):
        """Multiple code fences should be handled correctly."""
        content = textwrap.dedent("""\
            # Main Section

            You must create the first code block:

            ```markdown
            ## Header in first fence
            ```

            Some text between fences. You should verify this.

            ```markdown
            ### Header in second fence
            ```

            Final text that you must check.
        """)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            processor = DocumentProcessor(f.name)
            sections = processor.extract_sections()

        # Should have only 1 section
        assert len(sections) == 1
        assert sections[0]["header"] == "Main Section"
        assert "## Header in first fence" in sections[0]["content"]
        assert "### Header in second fence" in sections[0]["content"]
        assert "Final text" in sections[0]["content"]

    def test_code_fence_with_language_identifier(self):
        """Code fences with language identifiers should work correctly."""
        content = textwrap.dedent("""\
            # Test Section

            ```javascript
            // ## This looks like a header but isn't
            function test() {}
            ```

            Still in same section.
        """)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            processor = DocumentProcessor(f.name)
            sections = processor.extract_sections()

        assert len(sections) == 1
        assert sections[0]["header"] == "Test Section"

    def test_real_world_required_files_section(self):
        """Test the real-world scenario from document_structure.md."""
        content = textwrap.dedent("""\
            ### Required Files Section

            List all external file dependencies at the top. Model must verify access before proceeding.

            ```markdown
            ## Required Files

            | File | Purpose |
            |------|---------|
            | `CARD_CREATION_RULES.md` | Card formatting standards |
            | `schema/word_entry.json` | JSON schema for validation |
            | `word_tracking.md` | Source of truth for word list |

            ⚠️ **STOP** if any file above is not accessible. Report which file is missing.
            ```

            **Why upfront:**
            - Fail-fast - catch missing dependencies before work begins
            - Clear scope - reader knows all dependencies immediately
            - Maintenance - easy to update when dependencies change
        """)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            processor = DocumentProcessor(f.name)
            sections = processor.extract_sections()

        # Should have exactly 1 section with all content
        assert len(sections) == 1
        assert sections[0]["header"] == "Required Files Section"
        # The content inside the code fence should be preserved
        assert "## Required Files" in sections[0]["content"]
        assert "CARD_CREATION_RULES.md" in sections[0]["content"]
        # Content after the fence should also be included
        assert "Why upfront:" in sections[0]["content"]
        assert "Fail-fast" in sections[0]["content"]

    def test_unclosed_code_fence_treats_rest_as_code(self):
        """Unclosed code fence should treat rest of document as code."""
        content = textwrap.dedent("""\
            # First Section

            You must create the opening fence:

            ```markdown
            ## This is inside

            # This would be a header but fence is unclosed
        """)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            processor = DocumentProcessor(f.name)
            sections = processor.extract_sections()

        # Should have only 1 section since fence is never closed
        assert len(sections) == 1
        assert sections[0]["header"] == "First Section"

    def test_inline_backticks_dont_affect_fence_detection(self):
        """Inline code backticks should not affect fence detection."""
        content = textwrap.dedent("""\
            # Test Section

            You must use `code` inline and even ```triple``` inline.

            ## Second Section

            You should check more content with `inline code`.
        """)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            processor = DocumentProcessor(f.name)
            sections = processor.extract_sections()

        # Should have 2 sections - inline backticks don't create fences
        assert len(sections) == 2
        assert sections[0]["header"] == "Test Section"
        assert sections[1]["header"] == "Second Section"

    def test_nested_markdown_example(self):
        """Test nested markdown code example from Cross-Project TODOs."""
        content = textwrap.dedent("""\
            ## Cross-Project TODOs

            **Root `TODO.md`** should track:
            - Cross-project dependencies
            - Infrastructure/tooling improvements

            **Example:**
            ```markdown
            - [P1] [ ] Unify audio generation across German/English projects `2025-11-30` #infra #audio
            - [P2] [ ] Document common workflow patterns `2025-11-29` #docs #process
            ```

            ---
        """)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            processor = DocumentProcessor(f.name)
            sections = processor.extract_sections()

        assert len(sections) == 1
        assert sections[0]["header"] == "Cross-Project TODOs"
        assert "- [P1] [ ] Unify audio" in sections[0]["content"]
