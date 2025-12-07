"""
Ambiguity Detector - Detects disagreements between model interpretations

Supports multiple comparison strategies:
- simple: Basic string/keyword comparison (no dependencies)
- llm_judge: Ask an LLM to compare interpretations
- embeddings: Semantic similarity via sentence embeddings (requires sentence-transformers)
"""

import json
import re
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

# Logger for judge responses
judge_logger = logging.getLogger('judge_responses')


class Severity(Enum):
    """Ambiguity severity levels"""
    CRITICAL = "critical"  # Completely different interpretations
    HIGH = "high"          # Significant disagreement
    MEDIUM = "medium"      # Partial disagreement or assumptions made
    LOW = "low"            # Minor variations


@dataclass
class Interpretation:
    """Parsed interpretation from a model response"""
    model_name: str
    raw_response: str
    interpretation: str = ""
    steps: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    ambiguities: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @classmethod
    def from_response(cls, model_name: str, response: Dict[str, Any]) -> 'Interpretation':
        """Create Interpretation from model response dict (already parsed format)"""
        # Handle error responses
        if response.get('error'):
            return cls(
                model_name=model_name,
                raw_response=str(response),
                error=response.get('message', response.get('stderr', 'Unknown error'))
            )

        # Accept parsed format directly (from test_results.json)
        return cls(
            model_name=model_name,
            raw_response=str(response),
            interpretation=response.get('interpretation', ''),
            steps=response.get('steps', []),
            assumptions=response.get('assumptions', []),
            ambiguities=response.get('ambiguities', [])
        )

    @staticmethod
    def _try_parse_json(text: str) -> Dict[str, Any]:
        """Try to extract and parse JSON from text"""
        if not text:
            return {}

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON block in markdown
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON object
        json_match = re.search(r'\{[^{}]*"interpretation"[^{}]*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return {}


@dataclass
class Ambiguity:
    """Detected ambiguity in a documentation section"""
    section_id: str
    section_header: str
    section_content: str
    severity: Severity
    interpretations: Dict[str, Interpretation]
    comparison_details: Dict[str, Any] = field(default_factory=dict)
    suggested_fix: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'section_id': self.section_id,
            'section_header': self.section_header,
            'section_content': self.section_content,
            'severity': self.severity.value,
            'interpretations': {
                name: {
                    'interpretation': interp.interpretation,
                    'steps': interp.steps,
                    'assumptions': interp.assumptions,
                    'ambiguities': interp.ambiguities
                }
                for name, interp in self.interpretations.items()
            },
            'comparison_details': self.comparison_details
        }


class ComparisonStrategy:
    """Base class for comparison strategies"""

    def compare(self, interpretations: List[Interpretation]) -> Dict[str, Any]:
        """
Compare interpretations and return comparison result.

Returns:
{
'agree': bool,
'similarity': float (0-1),
'details': str,
'groups': [[model_names], [model_names]]  # grouped by similar interpretation
}
        """
        raise NotImplementedError


class SimpleComparisonStrategy(ComparisonStrategy):
    """
Simple keyword and structure-based comparison.
No external dependencies required.
"""

    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold

    def compare(self, interpretations: List[Interpretation]) -> Dict[str, Any]:
        if len(interpretations) < 2:
            return {'agree': True, 'similarity': 1.0, 'details': 'Only one interpretation', 'groups': []}

        # Extract key elements for comparison
        elements = []
        for interp in interpretations:
            elements.append({
                'model': interp.model_name,
                'keywords': self._extract_keywords(interp.interpretation),
                'step_count': len(interp.steps),
                'has_assumptions': len(interp.assumptions) > 0,
                'noted_ambiguities': len(interp.ambiguities) > 0
            })

        # Compare pairwise
        similarities = []
        for i in range(len(elements)):
            for j in range(i + 1, len(elements)):
                sim = self._calculate_similarity(elements[i], elements[j])
                similarities.append({
                    'pair': (elements[i]['model'], elements[j]['model']),
                    'similarity': sim
                })

        avg_similarity = sum(s['similarity'] for s in similarities) / len(similarities) if similarities else 1.0
        agree = avg_similarity >= self.similarity_threshold

        # Group by similarity
        groups = self._group_by_similarity(interpretations, elements)

        # Build details
        details_parts = []
        if not agree:
            details_parts.append(f"Average similarity: {avg_similarity:.2f}")
            for s in similarities:
                if s['similarity'] < self.similarity_threshold:
                    details_parts.append(f"{s['pair'][0]} vs {s['pair'][1]}: {s['similarity']:.2f}")

        # Check for assumptions (even if interpretations agree, assumptions indicate ambiguity)
        models_with_assumptions = [e['model'] for e in elements if e['has_assumptions']]
        if models_with_assumptions:
            details_parts.append(f"Models made assumptions: {', '.join(models_with_assumptions)}")

        # Check if models noted ambiguities
        models_noting_ambiguity = [e['model'] for e in elements if e['noted_ambiguities']]
        if models_noting_ambiguity:
            details_parts.append(f"Models noted ambiguities: {', '.join(models_noting_ambiguity)}")

        return {
            'agree': agree and not models_with_assumptions,
            'similarity': avg_similarity,
            'details': '; '.join(details_parts) if details_parts else 'Interpretations agree',
            'groups': groups,
            'assumptions_made': models_with_assumptions,
            'ambiguities_noted': models_noting_ambiguity
        }

    def _extract_keywords(self, text: str) -> set:
        """Extract significant keywords from text"""
        if not text:
            return set()

        # Normalize
        text = text.lower()

        # Remove common words
        stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'to', 'of',
            'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
            'and', 'or', 'but', 'if', 'then', 'else', 'when', 'where', 'which',
            'that', 'this', 'these', 'those', 'it', 'its', 'i', 'you', 'we', 'they'
        }

        # Extract words
        words = re.findall(r'\b[a-z]{3,}\b', text)
        keywords = set(words) - stopwords

        # Also extract numbers (important for quantities)
        numbers = re.findall(r'\b\d+\b', text)
        keywords.update(numbers)

        return keywords

    def _calculate_similarity(self, elem1: Dict, elem2: Dict) -> float:
        """Calculate similarity between two element sets"""
        kw1, kw2 = elem1['keywords'], elem2['keywords']

        if not kw1 and not kw2:
            return 1.0
        if not kw1 or not kw2:
            return 0.0

        # Jaccard similarity for keywords
        intersection = len(kw1 & kw2)
        union = len(kw1 | kw2)
        keyword_sim = intersection / union if union > 0 else 0

        # Step count similarity (normalized difference)
        max_steps = max(elem1['step_count'], elem2['step_count'], 1)
        step_diff = abs(elem1['step_count'] - elem2['step_count'])
        step_sim = 1 - (step_diff / max_steps)

        # Weighted combination
        return 0.7 * keyword_sim + 0.3 * step_sim

    def _group_by_similarity(self, interpretations: List[Interpretation], elements: List[Dict]) -> List[List[str]]:
        """Group models by similar interpretations"""
        if len(interpretations) <= 1:
            return [[interp.model_name for interp in interpretations]]

        # Simple grouping: if all similar, one group; otherwise separate groups
        groups = []
        used = set()

        for i, elem in enumerate(elements):
            if elem['model'] in used:
                continue

            group = [elem['model']]
            used.add(elem['model'])

            for j, other_elem in enumerate(elements[i+1:], i+1):
                if other_elem['model'] in used:
                    continue
                if self._calculate_similarity(elem, other_elem) >= self.similarity_threshold:
                    group.append(other_elem['model'])
                    used.add(other_elem['model'])

            groups.append(group)

        return groups


class LLMJudgeStrategy(ComparisonStrategy):
    """
Use an LLM to judge if interpretations agree.
Requires a model query function to be provided.
"""

    def __init__(self, query_func: Callable[[str], Dict[str, Any]]):
        """
Args:
query_func: Function that takes a prompt string and returns model response dict
        """
        self.query_func = query_func

    def compare(self, interpretations: List[Interpretation]) -> Dict[str, Any]:
        if len(interpretations) < 2:
            return {'agree': True, 'similarity': 1.0, 'details': 'Only one interpretation', 'groups': []}

        # Build comparison prompt
        prompt = self._build_comparison_prompt(interpretations)

        # Query the judge model
        response = self.query_func(prompt)

        # Parse response
        return self._parse_judge_response(response, interpretations)

    def _build_comparison_prompt(self, interpretations: List[Interpretation]) -> str:
        interp_text = ""
        for i, interp in enumerate(interpretations, 1):
            interp_text += f"\n**Interpretation {i} ({interp.model_name}):**\n"
            interp_text += f"Understanding: {interp.interpretation}\n"
            if interp.steps:
                interp_text += f"Steps: {', '.join(interp.steps[:5])}\n"
            if interp.assumptions:
                interp_text += f"Assumptions made: {', '.join(interp.assumptions)}\n"

        prompt = f"""Compare these interpretations of the same documentation section.

            {interp_text}

Do these interpretations describe the same understanding?

Respond with JSON only:
{{
"agree": true/false,
"similarity": 0.0-1.0,
"explanation": "brief explanation of agreement or differences",
"key_differences": ["difference 1", "difference 2"] or []
}}
            """
        return prompt

    def _parse_judge_response(self, response: Dict[str, Any], interpretations: List[Interpretation]) -> Dict[str, Any]:
        """Parse the judge model's response (already parsed JSON format)"""
        default = {
            'agree': False,
            'similarity': 0.5,
            'details': 'Could not parse judge response',
            'groups': [[i.model_name] for i in interpretations]
        }

        if response.get('error'):
            default['details'] = f"Judge error: {response.get('message', 'Unknown')}"
            return default

        # Response is already parsed JSON (has 'agree', 'similarity', etc. keys directly)
        if 'agree' not in response:
            default['details'] = f"Judge response missing 'agree' field. Keys: {list(response.keys())}"
            return default

        agree = response.get('agree', False)

        # Group models based on agreement
        if agree:
            groups = [[i.model_name for i in interpretations]]
        else:
            groups = [[i.model_name] for i in interpretations]

        return {
            'agree': agree,
            'similarity': float(response.get('similarity', 0.5)),
            'details': response.get('explanation', ''),
            'groups': groups,
            'key_differences': response.get('key_differences', [])
        }


class AmbiguityDetector:
    """
Main ambiguity detection class.

Usage:
detector = AmbiguityDetector(strategy='simple')
ambiguities = detector.detect(test_results)
"""

    def __init__(self,
                 strategy: str = 'simple',
                 similarity_threshold: float = 0.7,
                 llm_query_func: Optional[Callable] = None):
        """
Args:
strategy: 'simple' or 'llm_judge'
similarity_threshold: Threshold for simple strategy (0-1)
llm_query_func: Required if strategy='llm_judge'
        """
        self.strategy_name = strategy

        if strategy == 'simple':
            self.strategy = SimpleComparisonStrategy(similarity_threshold)
        elif strategy == 'llm_judge':
            if llm_query_func is None:
                raise ValueError("llm_query_func required for llm_judge strategy")
            self.strategy = LLMJudgeStrategy(llm_query_func)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def detect(self, test_results: Dict[str, Dict]) -> List[Ambiguity]:
        """
Detect ambiguities in test results.

Args:
test_results: Dict mapping section_id to {
'section': {'header': str, 'content': str, ...},
'results': {model_name: response_dict, ...}
}

Returns:
List of detected Ambiguity objects
        """
        ambiguities = []

        for section_id, data in test_results.items():
            section = data.get('section', {})
            results = data.get('results', {})

            # Parse interpretations
            interpretations = {}
            for model_name, response in results.items():
                interp = Interpretation.from_response(model_name, response)
                if not interp.error:
                    interpretations[model_name] = interp

            # Need at least 2 valid interpretations to compare
            if len(interpretations) < 2:
                continue

            # Compare interpretations
            comparison = self.strategy.compare(list(interpretations.values()))

            # Log judge response
            judge_logger.info(json.dumps({
                'section_id': section_id,
                'section_header': section.get('header', 'Unknown'),
                'models_compared': list(interpretations.keys()),
                'judge_response': comparison
            }, indent=2))

            # Determine if this is an ambiguity
            if not comparison['agree']:
                severity = self._determine_severity(comparison)

                ambiguities.append(Ambiguity(
                                       section_id=section_id,
                                       section_header=section.get('header', 'Unknown'),
                                       section_content=section.get('content', ''),
                                       severity=severity,
                                       interpretations=interpretations,
                                       comparison_details=comparison
                                   ))

            # Also flag sections where models made assumptions (even if they agree)
            elif comparison.get('assumptions_made'):
                ambiguities.append(Ambiguity(
                                       section_id=section_id,
                                       section_header=section.get('header', 'Unknown'),
                                       section_content=section.get('content', ''),
                                       severity=Severity.LOW,
                                       interpretations=interpretations,
                                       comparison_details={
                                           **comparison,
                                           'reason': 'Models agreed but made assumptions'
                                       }
                                   ))

        # Sort by severity
        severity_order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3}
        ambiguities.sort(key=lambda a: severity_order[a.severity])

        return ambiguities

    def _determine_severity(self, comparison: Dict[str, Any]) -> Severity:
        """Determine ambiguity severity based on comparison results"""
        similarity = comparison.get('similarity', 0.5)
        groups = comparison.get('groups', [])

        # All models disagree (each in own group)
        if len(groups) >= 3:
            return Severity.CRITICAL

        # Very low similarity
        if similarity < 0.3:
            return Severity.CRITICAL
        elif similarity < 0.5:
            return Severity.HIGH
        elif similarity < 0.7:
            return Severity.MEDIUM
        else:
            return Severity.LOW


def detect_ambiguities_simple(test_results: Dict[str, Dict], threshold: float = 0.7) -> List[Dict]:
    """
Convenience function for simple ambiguity detection.

Returns list of dicts (JSON-serializable) instead of Ambiguity objects.
    """
    detector = AmbiguityDetector(strategy='simple', similarity_threshold=threshold)
    ambiguities = detector.detect(test_results)
    return [a.to_dict() for a in ambiguities]


# For testing the module directly
if __name__ == "__main__":
    # Test with mock data
    test_data = {
        "section_0": {
            "section": {
                "header": "Step 2: Generate Output",
                "content": "Create N cards per word with the required information."
            },
            "results": {
                "claude": {
                    "raw_response": '{"interpretation": "Create 3 separate JSON entries for each word", "steps": ["Parse word", "Create entry 1", "Create entry 2", "Create entry 3"], "assumptions": [], "ambiguities": []}'
                },
                "gemini": {
                    "raw_response": '{"interpretation": "Create a single entry per word that will be expanded to N cards", "steps": ["Parse word", "Create combined entry"], "assumptions": ["N will be determined by word type"], "ambiguities": ["Unclear what N means"]}'
                }
            }
        }
    }

    print("Testing SimpleComparisonStrategy...")
    detector = AmbiguityDetector(strategy='simple', similarity_threshold=0.7)
    ambiguities = detector.detect(test_data)

    print(f"\nFound {len(ambiguities)} ambiguities:")
    for amb in ambiguities:
        print(f"\n  Section: {amb.section_header}")
        print(f"  Severity: {amb.severity.value}")
        print(f"  Details: {amb.comparison_details.get('details', 'N/A')}")
        for model, interp in amb.interpretations.items():
            print(f"    {model}: {interp.interpretation[:80]}...")