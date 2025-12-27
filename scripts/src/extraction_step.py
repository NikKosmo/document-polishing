"""
Extraction Step - Extract testable sections from markdown documents

This module provides a clean interface for Step 1 of the document polishing pipeline.
It wraps the DocumentProcessor to extract sections and provides serialization for the results.
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict
from pathlib import Path

from document_processor import DocumentProcessor


@dataclass
class ExtractionResult:
    """
    Result of extracting sections from a document.

    Contains all extracted sections, summary information, full document content,
    and the original document path. Can be saved to/loaded from JSON.
    """
    sections: List[Dict] = field(default_factory=list)
    summary: List[str] = field(default_factory=list)
    document_content: str = ""
    document_path: str = ""

    def save(self, output_path: str):
        """
        Save extraction result to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'sections': self.sections,
            'summary': self.summary,
            'document_content': self.document_content,
            'document_path': self.document_path
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, input_path: str) -> 'ExtractionResult':
        """
        Load extraction result from JSON file.

        Args:
            input_path: Path to input JSON file

        Returns:
            ExtractionResult instance

        Raises:
            FileNotFoundError: If input file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        input_file = Path(input_path)
        if not input_file.exists():
            raise FileNotFoundError(f"Extraction result not found: {input_path}")

        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return cls(
            sections=data.get('sections', []),
            summary=data.get('summary', []),
            document_content=data.get('document_content', ''),
            document_path=data.get('document_path', '')
        )


class ExtractionStep:
    """
    Step 1: Extract testable sections from markdown document.

    This class wraps DocumentProcessor to provide a clean interface for
    extracting sections and returning a serializable result.

    Usage:
        step = ExtractionStep('document.md')
        result = step.extract()
        result.save('sections.json')
    """

    def __init__(self, document_path: str):
        """
        Initialize extraction step.

        Args:
            document_path: Path to markdown document to process

        Raises:
            FileNotFoundError: If document doesn't exist
        """
        self.document_path = str(Path(document_path).absolute())
        self.processor = DocumentProcessor(document_path)

    def extract(self) -> ExtractionResult:
        """
        Extract sections from the document.

        Returns:
            ExtractionResult containing:
                - sections: List of extracted section dicts
                - summary: List of section summary strings
                - document_content: Full document text
                - document_path: Absolute path to document
        """
        # Extract sections using DocumentProcessor
        sections = self.processor.extract_sections()

        # Get additional metadata
        summary = self.processor.get_section_summary()
        document_content = self.processor.get_full_content()

        # Build and return result
        return ExtractionResult(
            sections=sections,
            summary=summary,
            document_content=document_content,
            document_path=self.document_path
        )


# Convenience function for simple usage
def extract_sections_from_document(document_path: str) -> ExtractionResult:
    """
    Extract sections from a document (convenience function).

    Args:
        document_path: Path to markdown document

    Returns:
        ExtractionResult with sections and metadata
    """
    step = ExtractionStep(document_path)
    return step.extract()


# For testing the module directly
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python extraction_step.py <document.md> [output.json]")
        sys.exit(1)

    document_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else 'sections.json'

    print(f"Extracting sections from: {document_path}")
    step = ExtractionStep(document_path)
    result = step.extract()

    print(f"\nExtracted {len(result.sections)} sections:")
    for summary_line in result.summary:
        print(f"  {summary_line}")

    result.save(output_path)
    print(f"\nSaved to: {output_path}")
