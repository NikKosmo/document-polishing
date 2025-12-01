"""Prompt Generator - Creates prompts for testing documentation sections"""

from typing import Dict, List


class PromptGenerator:
    """Generates prompts for testing documentation with AI models"""
    
    @staticmethod
    def create_interpretation_prompt(section: Dict) -> str:
        """Create a prompt to test how a model interprets instructions"""
        header = section.get('header', 'Section')
        content = section.get('content', '')
        
        prompt = f"""You are testing documentation for clarity. Read the following section and provide your interpretation.

SECTION: {header}

CONTENT:
{content}

Please respond with a JSON object containing:
1. "interpretation": Your understanding of what should be done
2. "steps": List of specific steps you would take
3. "assumptions": Any assumptions you needed to make
4. "ambiguities": Any unclear or ambiguous parts you noticed

Respond ONLY with valid JSON in this format:
{{
  "interpretation": "your interpretation here",
  "steps": ["step 1", "step 2", "..."],
  "assumptions": ["assumption 1", "assumption 2", "..."],
  "ambiguities": ["ambiguity 1", "ambiguity 2", "..."]
}}
"""
        return prompt
    
    @staticmethod
    def create_implementation_prompt(section: Dict) -> str:
        """Create a prompt asking the model to implement the instructions"""
        header = section.get('header', 'Section')
        content = section.get('content', '')
        
        prompt = f"""You are implementing the following documentation section.

SECTION: {header}

INSTRUCTIONS:
{content}

Describe exactly what you would implement. Respond with JSON:
{{
  "implementation": "detailed description of what you would create",
  "key_decisions": ["decision 1", "decision 2", "..."],
  "unclear_points": ["unclear point 1", "unclear point 2", "..."]
}}
"""
        return prompt
    
    @staticmethod
    def create_qa_prompt(section: Dict) -> str:
        """Create a prompt with questions about the section"""
        content = section.get('content', '')
        
        prompt = f"""Read these instructions and answer the questions:

INSTRUCTIONS:
{content}

Questions:
1. What exactly needs to be created?
2. How many items should be created?
3. What format should the output be in?
4. Are there any edge cases to consider?

Respond with JSON:
{{
  "what": "answer to question 1",
  "how_many": "answer to question 2",
  "format": "answer to question 3",
  "edge_cases": ["case 1", "case 2", "..."]
}}
"""
        return prompt
    
    @staticmethod
    def create_simple_prompt(section: Dict) -> str:
        """Create a simple prompt for basic interpretation testing"""
        content = section.get('content', '')
        
        prompt = f"""Read these instructions and explain what you would do:

{content}

Respond with a brief explanation of your interpretation.
"""
        return prompt


class PromptTemplates:
    """Collection of prompt templates"""
    
    INTERPRETATION = """You are testing documentation for clarity.

SECTION: {header}
{content}

Provide your interpretation as JSON:
{{
  "interpretation": "what you understand",
  "steps": ["step 1", "step 2"],
  "assumptions": ["assumption 1"],
  "ambiguities": ["unclear point 1"]
}}
"""
    
    COMPARISON = """Compare these two interpretations of the same documentation:

INTERPRETATION A:
{interp_a}

INTERPRETATION B:
{interp_b}

Are they describing the same thing? Respond with JSON:
{{
  "same": true/false,
  "differences": ["difference 1", "difference 2"],
  "severity": "low/medium/high"
}}
"""
    
    FIX_SUGGESTION = """This documentation section has been interpreted differently by different readers:

ORIGINAL:
{original}

INTERPRETATION 1:
{interp_1}

INTERPRETATION 2:
{interp_2}

Suggest a clearer version that eliminates the ambiguity. Respond with JSON:
{{
  "improved_text": "your improved version",
  "changes_made": ["change 1", "change 2"],
  "reasoning": "why this is clearer"
}}
"""
