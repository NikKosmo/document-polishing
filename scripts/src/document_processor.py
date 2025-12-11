"""Document Processor - Extracts and analyzes sections from markdown documents"""

import re
from typing import List, Dict, Tuple
from pathlib import Path


class DocumentProcessor:
    """Processes markdown documents to extract testable sections"""
    
    # Keywords that indicate instruction sections
    INSTRUCTION_KEYWORDS = [
        'step', 'must', 'should', 'create', 'generate', 'validate',
        'process', 'execute', 'run', 'configure', 'setup', 'install',
        'build', 'deploy', 'test', 'check', 'verify', 'ensure'
    ]
    
    def __init__(self, document_path: str):
        self.path = Path(document_path)
        if not self.path.exists():
            raise FileNotFoundError(f"Document not found: {document_path}")
        
        self.content = self.path.read_text(encoding='utf-8')
        self.sections = []
    
    def extract_sections(self) -> List[Dict]:
        """Extract sections from the document"""
        sections = []
        lines = self.content.split('\n')
        
        current_section = {
            'header': '',
            'content': [],
            'start_line': 0,
            'level': 0
        }
        
        # Track code fence state to avoid treating headers inside fences as section breaks
        in_code_fence = False
        
        for i, line in enumerate(lines):
            # Check for code fence toggling (``` with optional language identifier)
            if re.match(r'^```', line.strip()):
                in_code_fence = not in_code_fence
            
            # Check if line is a header (only if not inside a code fence)
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line) if not in_code_fence else None
            
            if header_match:
                # Save previous section if it has content
                if current_section['content']:
                    section_text = '\n'.join(current_section['content'])
                    if self._is_instructional(section_text):
                        sections.append({
                            'header': current_section['header'],
                            'content': section_text,
                            'start_line': current_section['start_line'],
                            'end_line': i - 1,
                            'level': current_section['level'],
                            'type': 'instruction'
                        })
                
                # Start new section
                level = len(header_match.group(1))
                header = header_match.group(2).strip()
                current_section = {
                    'header': header,
                    'content': [],
                    'start_line': i,
                    'level': level
                }
            else:
                # Add to current section
                current_section['content'].append(line)
        
        # Don't forget the last section
        if current_section['content']:
            section_text = '\n'.join(current_section['content'])
            if self._is_instructional(section_text):
                sections.append({
                    'header': current_section['header'],
                    'content': section_text,
                    'start_line': current_section['start_line'],
                    'end_line': len(lines) - 1,
                    'level': current_section['level'],
                    'type': 'instruction'
                })
        
        self.sections = sections
        return sections
    
    def _is_instructional(self, text: str) -> bool:
        """Check if text contains instructional content"""
        text_lower = text.lower()
        
        # Must have some content
        if len(text.strip()) < 10:
            return False
        
        # Check for instruction keywords
        keyword_count = sum(1 for keyword in self.INSTRUCTION_KEYWORDS 
                          if keyword in text_lower)
        
        return keyword_count > 0
    
    def get_section_by_index(self, index: int) -> Dict:
        """Get a specific section by index"""
        if 0 <= index < len(self.sections):
            return self.sections[index]
        return None
    
    def get_full_content(self) -> str:
        """Get the full document content"""
        return self.content
    
    def count_sections(self) -> int:
        """Count testable sections"""
        return len(self.sections)
    
    def get_section_summary(self) -> List[str]:
        """Get a summary of all sections"""
        return [
            f"[{i}] {s['header']} (lines {s['start_line']}-{s['end_line']})"
            for i, s in enumerate(self.sections)
        ]


def extract_ambiguous_patterns(text: str) -> List[Dict]:
    """Detect potentially ambiguous patterns in text"""
    patterns = []
    
    # Pattern 1: Vague quantifiers
    vague_quantifiers = re.finditer(
        r'\b(N|several|some|many|all|each)\s+(\w+)',
        text,
        re.IGNORECASE
    )
    for match in vague_quantifiers:
        patterns.append({
            'type': 'vague_quantifier',
            'text': match.group(0),
            'position': match.start(),
            'severity': 'high' if match.group(1).upper() == 'N' else 'medium'
        })
    
    # Pattern 2: Implicit references (the, this, that without clear antecedent)
    implicit_refs = re.finditer(
        r'\b(the|this|that)\s+(process|output|result|value)\b',
        text,
        re.IGNORECASE
    )
    for match in implicit_refs:
        patterns.append({
            'type': 'implicit_reference',
            'text': match.group(0),
            'position': match.start(),
            'severity': 'medium'
        })
    
    # Pattern 3: Undefined "standard" or "required"
    undefined_terms = re.finditer(
        r'\b(standard|required|necessary|appropriate)\s+(\w+)',
        text,
        re.IGNORECASE
    )
    for match in undefined_terms:
        patterns.append({
            'type': 'undefined_term',
            'text': match.group(0),
            'position': match.start(),
            'severity': 'medium'
        })
    
    return patterns
