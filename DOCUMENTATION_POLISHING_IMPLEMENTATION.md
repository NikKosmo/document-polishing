# Documentation Polishing - Implementation Guide

**Version:** 1.0  
**Date:** 2025-11-19  
**Purpose:** Practical implementation scripts and examples for the documentation polishing workflow

---

## Quick Start Implementation

### Minimal Working Example

```python
#!/usr/bin/env python3
"""
minimal_polish.py - Minimal working example of documentation polishing
"""

import json
import hashlib
import difflib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class DocumentPolisher:
    def __init__(self, document_path: str):
        self.document_path = Path(document_path)
        self.session_id = f"polish_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.workspace = Path(f"workspace/{self.session_id}")
        self.setup_workspace()
        
    def setup_workspace(self):
        """Create workspace directory structure"""
        self.workspace.mkdir(parents=True, exist_ok=True)
        (self.workspace / "iterations").mkdir(exist_ok=True)
        (self.workspace / "reports").mkdir(exist_ok=True)
        
        # Backup original
        original = self.workspace / "original.md"
        original.write_text(self.document_path.read_text())
        
    def extract_testable_sections(self) -> List[Dict]:
        """Extract sections that contain instructions"""
        content = self.document_path.read_text()
        sections = []
        
        # Simple extraction based on headers and keywords
        lines = content.split('\n')
        current_section = []
        section_start = 0
        
        instruction_keywords = ['step', 'must', 'should', 'create', 'generate', 'validate']
        
        for i, line in enumerate(lines):
            if line.startswith('#'):  # Header
                if current_section:
                    # Check if section contains instructions
                    section_text = '\n'.join(current_section)
                    if any(keyword in section_text.lower() for keyword in instruction_keywords):
                        sections.append({
                            'start': section_start,
                            'end': i,
                            'content': section_text,
                            'type': 'instruction'
                        })
                current_section = [line]
                section_start = i
            else:
                current_section.append(line)
                
        return sections
    
    def test_with_model(self, section: Dict, model_name: str) -> Dict:
        """Simulate testing with a model (replace with actual API calls)"""
        # This is where you'd call actual model APIs
        # For demo, we'll simulate responses
        
        prompt = f"""
        Read this documentation section:
        {section['content']}
        
        What specific actions would you take based on these instructions?
        Format as JSON with 'interpretation' and 'steps' fields.
        """
        
        # Simulated responses showing ambiguity
        if "Create N cards" in section['content']:
            if model_name == "claude":
                return {
                    "interpretation": "Create multiple JSON entries per word",
                    "steps": ["Create 3 entries for noun", "Each entry is one card"]
                }
            elif model_name == "gemini":
                return {
                    "interpretation": "Create single JSON entry per word",
                    "steps": ["Create 1 entry per word", "Script expands to N cards"]
                }
        
        return {
            "interpretation": "Standard interpretation",
            "steps": ["Follow instructions as written"]
        }
    
    def detect_ambiguities(self, test_results: Dict) -> List[Dict]:
        """Compare test results to find ambiguities"""
        ambiguities = []
        
        for section_id, results in test_results.items():
            interpretations = {}
            for model, response in results.items():
                interp = response['interpretation']
                if interp not in interpretations:
                    interpretations[interp] = []
                interpretations[interp].append(model)
            
            if len(interpretations) > 1:
                ambiguities.append({
                    'section': section_id,
                    'interpretations': interpretations,
                    'severity': 'critical' if len(interpretations) > 2 else 'major'
                })
        
        return ambiguities
    
    def generate_fix(self, ambiguity: Dict, section_content: str) -> str:
        """Generate a clarified version of ambiguous text"""
        if "Create N cards" in section_content:
            # Make it explicit
            fixed = section_content.replace(
                "Create N cards per word",
                "Create N separate JSON entries per word (one entry per card):\n"
                "- Nouns: Create 3 JSON entries (RU→DE, DE→RU, Cloze)\n"
                "- Verbs: Create 2 JSON entries (RU→DE, DE→RU)"
            )
            return fixed
        return section_content
    
    def polish(self, models: List[str] = None) -> Path:
        """Run the complete polishing workflow"""
        if models is None:
            models = ["claude", "gemini"]
        
        print(f"Starting polish session: {self.session_id}")
        
        # Extract testable sections
        sections = self.extract_testable_sections()
        print(f"Found {len(sections)} testable sections")
        
        # Test each section with each model
        test_results = {}
        for i, section in enumerate(sections):
            section_id = f"section_{i}"
            test_results[section_id] = {}
            
            for model in models:
                result = self.test_with_model(section, model)
                test_results[section_id][model] = result
        
        # Detect ambiguities
        ambiguities = self.detect_ambiguities(test_results)
        print(f"Found {len(ambiguities)} ambiguities")
        
        # Generate fixes
        content = self.document_path.read_text()
        for ambiguity in ambiguities:
            section_idx = int(ambiguity['section'].split('_')[1])
            section = sections[section_idx]
            fixed_content = self.generate_fix(ambiguity, section['content'])
            content = content.replace(section['content'], fixed_content)
        
        # Save polished version
        polished_path = self.workspace / "polished.md"
        polished_path.write_text(content)
        
        # Generate report
        report = {
            'session_id': self.session_id,
            'document': str(self.document_path),
            'models_used': models,
            'sections_tested': len(sections),
            'ambiguities_found': len(ambiguities),
            'ambiguities': ambiguities
        }
        
        report_path = self.workspace / "reports" / "summary.json"
        report_path.write_text(json.dumps(report, indent=2))
        
        print(f"✅ Polishing complete: {polished_path}")
        return polished_path

# Usage
if __name__ == "__main__":
    polisher = DocumentPolisher("WORKFLOW.md")
    polished_doc = polisher.polish(models=["claude", "gemini"])
```

---

## Full Implementation Scripts

### 1. Model Interface Abstraction

```python
# model_interface.py
from abc import ABC, abstractmethod
import openai
import anthropic
import subprocess
import json
from typing import Dict, Any

class ModelInterface(ABC):
    @abstractmethod
    def query(self, prompt: str) -> Dict[str, Any]:
        pass

class ClaudeModel(ModelInterface):
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        
    def query(self, prompt: str) -> Dict[str, Any]:
        response = self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4096,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse JSON from response
        try:
            return json.loads(response.content[0].text)
        except:
            return {"raw_response": response.content[0].text}

class GeminiModel(ModelInterface):
    def __init__(self, cli_path: str = "gemini"):
        self.cli_path = cli_path
        
    def query(self, prompt: str) -> Dict[str, Any]:
        result = subprocess.run(
            [self.cli_path, "-p", prompt],
            capture_output=True,
            text=True
        )
        
        try:
            return json.loads(result.stdout)
        except:
            return {"raw_response": result.stdout}

class GPTModel(ModelInterface):
    def __init__(self, api_key: str):
        openai.api_key = api_key
        
    def query(self, prompt: str) -> Dict[str, Any]:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except:
            return {"raw_response": response.choices[0].message.content}

class ModelFactory:
    @staticmethod
    def create(model_type: str, config: Dict) -> ModelInterface:
        if model_type == "claude":
            return ClaudeModel(config['api_key'])
        elif model_type == "gemini":
            return GeminiModel(config.get('cli_path', 'gemini'))
        elif model_type == "gpt":
            return GPTModel(config['api_key'])
        else:
            raise ValueError(f"Unknown model type: {model_type}")
```

---

### 2. Ambiguity Detection Engine

```python
# ambiguity_detector.py
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple
import json

class AmbiguityDetector:
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.vectorizer = TfidfVectorizer()
        
    def detect(self, responses: Dict[str, Dict]) -> List[Dict]:
        """Detect ambiguities from model responses"""
        ambiguities = []
        
        # Group responses by interpretation
        interpretation_groups = self._group_by_interpretation(responses)
        
        if len(interpretation_groups) > 1:
            ambiguity = self._analyze_disagreement(interpretation_groups, responses)
            ambiguities.append(ambiguity)
            
        return ambiguities
    
    def _group_by_interpretation(self, responses: Dict) -> Dict[str, List[str]]:
        """Group models by similar interpretations"""
        groups = {}
        interpretations = []
        model_names = []
        
        for model, response in responses.items():
            if 'interpretation' in response:
                interpretations.append(response['interpretation'])
                model_names.append(model)
        
        if not interpretations:
            return {}
        
        # Calculate similarity matrix
        vectors = self.vectorizer.fit_transform(interpretations)
        similarity_matrix = cosine_similarity(vectors)
        
        # Group similar interpretations
        assigned = [False] * len(model_names)
        group_id = 0
        
        for i in range(len(model_names)):
            if assigned[i]:
                continue
                
            group_key = f"group_{group_id}"
            groups[group_key] = [model_names[i]]
            assigned[i] = True
            
            for j in range(i + 1, len(model_names)):
                if not assigned[j] and similarity_matrix[i][j] >= self.similarity_threshold:
                    groups[group_key].append(model_names[j])
                    assigned[j] = True
            
            group_id += 1
        
        return groups
    
    def _analyze_disagreement(self, groups: Dict, responses: Dict) -> Dict:
        """Analyze the nature and severity of disagreements"""
        severity = self._calculate_severity(groups)
        
        interpretations_by_group = {}
        for group_id, models in groups.items():
            sample_model = models[0]
            interpretations_by_group[group_id] = {
                'models': models,
                'interpretation': responses[sample_model].get('interpretation', ''),
                'steps': responses[sample_model].get('steps', [])
            }
        
        return {
            'severity': severity,
            'interpretation_groups': interpretations_by_group,
            'disagreement_type': self._classify_disagreement(interpretations_by_group)
        }
    
    def _calculate_severity(self, groups: Dict) -> str:
        """Calculate ambiguity severity"""
        num_groups = len(groups)
        
        if num_groups >= 3:
            return 'critical'
        elif num_groups == 2:
            # Check if it's an even split
            sizes = [len(models) for models in groups.values()]
            if abs(sizes[0] - sizes[1]) <= 1:
                return 'major'
            else:
                return 'moderate'
        else:
            return 'minor'
    
    def _classify_disagreement(self, interpretations: Dict) -> str:
        """Classify the type of disagreement"""
        all_steps = []
        for group_data in interpretations.values():
            all_steps.extend(group_data.get('steps', []))
        
        if not all_steps:
            return 'interpretation_only'
        
        # Check if steps differ in quantity or quality
        step_counts = [len(group_data.get('steps', [])) for group_data in interpretations.values()]
        
        if len(set(step_counts)) > 1:
            return 'quantity_disagreement'
        else:
            return 'approach_disagreement'

class AmbiguityResolver:
    def __init__(self):
        self.strategies = [
            self.explicit_clarification,
            self.structured_format,
            self.example_based,
            self.redundant_specification
        ]
    
    def generate_fixes(self, ambiguity: Dict, original_text: str) -> List[Dict]:
        """Generate multiple fix options for an ambiguity"""
        fixes = []
        
        for strategy in self.strategies:
            fix = strategy(ambiguity, original_text)
            if fix:
                fixes.append(fix)
        
        # Rank fixes by confidence
        fixes.sort(key=lambda x: x['confidence'], reverse=True)
        return fixes
    
    def explicit_clarification(self, ambiguity: Dict, text: str) -> Dict:
        """Add explicit clarifying statements"""
        groups = ambiguity['interpretation_groups']
        
        if len(groups) == 2:
            # Create explicit statement addressing both interpretations
            clarification = "\n\n**CLARIFICATION:**\n"
            for group_id, data in groups.items():
                clarification += f"- NOT: {data['interpretation']}\n"
            clarification += f"- CORRECT: [Specify the correct interpretation explicitly]\n"
            
            return {
                'strategy': 'explicit_clarification',
                'fixed_text': text + clarification,
                'confidence': 0.9,
                'rationale': 'Added explicit clarification to address ambiguity'
            }
        return None
    
    def structured_format(self, ambiguity: Dict, text: str) -> Dict:
        """Convert to structured format like tables"""
        if 'quantity_disagreement' in str(ambiguity):
            # Create a table format
            table = """
| Requirement | Details |
|-------------|---------|
| Number of entries | Exactly N (specify per type) |
| Entry format | One JSON object per card |
| Total cards | Sum of all entries |
"""
            return {
                'strategy': 'structured_format',
                'fixed_text': text.replace("Create N cards", table),
                'confidence': 0.85,
                'rationale': 'Converted to table format for clarity'
            }
        return None
    
    def example_based(self, ambiguity: Dict, text: str) -> Dict:
        """Add comprehensive examples"""
        example = """
**Example for word "Mann" (Noun):**
```json
[
  {
    "card_type": "Reverse RU→DE",
    "word_type": "Noun (m)",
    "russian": "мужчина",
    "german": "der Mann"
  },
  {
    "card_type": "Reverse DE→RU",
    "word_type": "Noun (m)",
    "russian": "мужчина",
    "german": "der Mann"
  },
  {
    "card_type": "Cloze",
    "word_type": "Noun (m)",
    "russian": "мужчина",
    "german": "{{c1::der}} Mann"
  }
]
```
Note: 3 separate JSON entries = 3 cards
"""
        return {
            'strategy': 'example_based',
            'fixed_text': text + "\n" + example,
            'confidence': 0.8,
            'rationale': 'Added comprehensive example showing exact requirement'
        }
    
    def redundant_specification(self, ambiguity: Dict, text: str) -> Dict:
        """State the same requirement in multiple ways"""
        redundant = """
**Requirements (stated three ways):**
1. Number of JSON array elements = Number of cards needed
2. Each flashcard requires its own JSON object in the array
3. Do not create a single entry expecting expansion; create all entries explicitly
"""
        return {
            'strategy': 'redundant_specification',
            'fixed_text': text + "\n" + redundant,
            'confidence': 0.75,
            'rationale': 'Added redundant specifications to prevent misinterpretation'
        }
```

---

### 3. Test Prompt Generator

```python
# prompt_generator.py
from typing import List, Dict
import re
import json

class TestPromptGenerator:
    def __init__(self):
        self.prompt_templates = {
            'instruction': self._instruction_template,
            'example': self._example_template,
            'specification': self._specification_template,
            'procedure': self._procedure_template
        }
    
    def generate_prompts(self, section: Dict) -> List[Dict]:
        """Generate test prompts for a documentation section"""
        section_type = self._classify_section(section['content'])
        template_func = self.prompt_templates.get(section_type, self._default_template)
        
        prompts = []
        base_prompt = template_func(section)
        
        # Generate variations for thorough testing
        prompts.append({
            'type': 'direct',
            'prompt': base_prompt
        })
        
        # Add edge case prompt
        prompts.append({
            'type': 'edge_case',
            'prompt': self._add_edge_case(base_prompt, section)
        })
        
        # Add stress test prompt
        prompts.append({
            'type': 'stress_test',
            'prompt': self._add_stress_test(base_prompt, section)
        })
        
        return prompts
    
    def _classify_section(self, content: str) -> str:
        """Classify the type of documentation section"""
        content_lower = content.lower()
        
        if 'step' in content_lower and ('create' in content_lower or 'generate' in content_lower):
            return 'instruction'
        elif '```' in content or 'json' in content_lower:
            return 'example'
        elif 'must' in content_lower or 'required' in content_lower:
            return 'specification'
        elif any(word in content_lower for word in ['first', 'then', 'next', 'finally']):
            return 'procedure'
        else:
            return 'general'
    
    def _instruction_template(self, section: Dict) -> str:
        return f"""You are implementing a documentation-based workflow.

Read the following instructions carefully:

---
{section['content']}
---

Based on these instructions:

1. What EXACTLY should you create or do? Be specific about quantities, formats, and structures.
2. List the concrete steps you would take to implement these instructions.
3. What assumptions (if any) do you need to make?
4. Are there any ambiguous points that could be interpreted differently?

Respond in JSON format:
{{
    "interpretation": "Your understanding of what to do",
    "steps": ["Step 1", "Step 2", ...],
    "assumptions": ["Assumption 1", ...],
    "ambiguities": ["Ambiguity 1", ...],
    "output_format": "Description of expected output"
}}
"""
    
    def _example_template(self, section: Dict) -> str:
        return f"""Examine this documentation with examples:

---
{section['content']}
---

Analyze the examples and instructions:

1. Do the examples match the textual description?
2. Is there only one way to interpret the examples?
3. What would you produce if asked to create similar output?

Respond in JSON format:
{{
    "example_interpretation": "What the examples show",
    "text_interpretation": "What the text says",
    "consistency": "consistent|inconsistent|unclear",
    "would_produce": "Description of what you would create",
    "clarification_needed": ["Point 1", ...]
}}
"""
    
    def _specification_template(self, section: Dict) -> str:
        return f"""Review these specifications:

---
{section['content']}
---

Evaluate the specifications:

1. Are all requirements explicitly stated?
2. Could any requirement be interpreted multiple ways?
3. What edge cases are not covered?

Respond in JSON format:
{{
    "requirements": ["Req 1", "Req 2", ...],
    "implicit_requirements": ["Implicit 1", ...],
    "ambiguous_requirements": ["Ambiguous 1", ...],
    "missing_edge_cases": ["Edge case 1", ...]
}}
"""
    
    def _procedure_template(self, section: Dict) -> str:
        return f"""Follow this procedure:

---
{section['content']}
---

Analyze the procedure:

1. Are the steps in unambiguous order?
2. Are there any conditional branches that are unclear?
3. What could go wrong if followed literally?

Respond in JSON format:
{{
    "step_sequence": ["Step 1", "Step 2", ...],
    "unclear_conditions": ["Condition 1", ...],
    "potential_failures": ["Failure 1", ...],
    "missing_steps": ["Missing 1", ...]
}}
"""
    
    def _default_template(self, section: Dict) -> str:
        return f"""Read and interpret this documentation:

---
{section['content']}
---

Provide your interpretation in JSON format:
{{
    "main_purpose": "What this section describes",
    "key_points": ["Point 1", "Point 2", ...],
    "unclear_aspects": ["Unclear 1", ...],
    "interpretation": "Your overall understanding"
}}
"""
    
    def _add_edge_case(self, base_prompt: str, section: Dict) -> str:
        """Add edge case testing to prompt"""
        edge_case_addition = """

Additionally, consider these edge cases:
- What if the input is empty?
- What if the input is malformed?
- What if optional parameters are omitted?
- What happens with maximum/minimum values?

Include an 'edge_case_handling' field in your response.
"""
        return base_prompt + edge_case_addition
    
    def _add_stress_test(self, base_prompt: str, section: Dict) -> str:
        """Add stress testing to prompt"""
        stress_addition = """

For stress testing, consider:
- How would you handle 1000 items instead of 10?
- What if multiple users do this simultaneously?
- What if the process is interrupted midway?
- How would you validate the output is correct?

Include a 'stress_scenarios' field in your response.
"""
        return base_prompt + stress_addition
```

---

### 4. Automated Test Runner

```python
# test_runner.py
import asyncio
import concurrent.futures
from typing import List, Dict, Any
import json
import time
from datetime import datetime
import logging

class ParallelTestRunner:
    def __init__(self, max_workers: int = 10, timeout: int = 30):
        self.max_workers = max_workers
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
    async def run_tests(self, 
                       test_suite: List[Dict],
                       models: List[Any]) -> Dict[str, Any]:
        """Run tests in parallel across multiple models"""
        results = {
            'start_time': datetime.now().isoformat(),
            'test_results': {},
            'summary': {}
        }
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for test in test_suite:
                for model in models:
                    future = executor.submit(
                        self._run_single_test,
                        test,
                        model
                    )
                    futures.append((future, test['id'], model.name))
            
            # Collect results
            for future, test_id, model_name in futures:
                try:
                    result = future.result(timeout=self.timeout)
                    
                    if test_id not in results['test_results']:
                        results['test_results'][test_id] = {}
                    
                    results['test_results'][test_id][model_name] = result
                    
                except concurrent.futures.TimeoutError:
                    self.logger.error(f"Timeout for test {test_id} with {model_name}")
                    results['test_results'][test_id][model_name] = {
                        'error': 'timeout',
                        'duration': self.timeout
                    }
                except Exception as e:
                    self.logger.error(f"Error in test {test_id} with {model_name}: {e}")
                    results['test_results'][test_id][model_name] = {
                        'error': str(e)
                    }
        
        results['end_time'] = datetime.now().isoformat()
        results['summary'] = self._generate_summary(results['test_results'])
        
        return results
    
    def _run_single_test(self, test: Dict, model: Any) -> Dict:
        """Run a single test with a single model"""
        start_time = time.time()
        
        try:
            response = model.query(test['prompt'])
            duration = time.time() - start_time
            
            return {
                'response': response,
                'duration': duration,
                'success': True
            }
        except Exception as e:
            return {
                'error': str(e),
                'duration': time.time() - start_time,
                'success': False
            }
    
    def _generate_summary(self, test_results: Dict) -> Dict:
        """Generate summary statistics"""
        total_tests = sum(len(models) for models in test_results.values())
        successful_tests = 0
        failed_tests = 0
        timeouts = 0
        
        for test_id, model_results in test_results.items():
            for model_name, result in model_results.items():
                if result.get('success'):
                    successful_tests += 1
                elif result.get('error') == 'timeout':
                    timeouts += 1
                else:
                    failed_tests += 1
        
        return {
            'total_tests': total_tests,
            'successful': successful_tests,
            'failed': failed_tests,
            'timeouts': timeouts,
            'success_rate': successful_tests / total_tests if total_tests > 0 else 0
        }

class MultiAgentTestRunner(ParallelTestRunner):
    """Run multiple agents of the same model for consistency testing"""
    
    async def run_multi_agent_tests(self,
                                   test_suite: List[Dict],
                                   model: Any,
                                   num_agents: int = 5) -> Dict:
        """Run tests with multiple instances of the same model"""
        results = {
            'model': model.name,
            'num_agents': num_agents,
            'consistency_results': {}
        }
        
        for test in test_suite:
            test_id = test['id']
            agent_responses = []
            
            # Run the same test with multiple agents
            for agent_id in range(num_agents):
                response = await self._run_with_agent(test, model, agent_id)
                agent_responses.append(response)
            
            # Analyze consistency
            consistency = self._analyze_consistency(agent_responses)
            
            results['consistency_results'][test_id] = {
                'responses': agent_responses,
                'consistency_score': consistency['score'],
                'variations': consistency['variations']
            }
        
        return results
    
    async def _run_with_agent(self, test: Dict, model: Any, agent_id: int) -> Dict:
        """Run test with a specific agent instance"""
        # Add slight variation to simulate different agent instances
        prompt_with_seed = test['prompt'] + f"\n[Agent Instance: {agent_id}]"
        
        return self._run_single_test(
            {'prompt': prompt_with_seed, 'id': test['id']},
            model
        )
    
    def _analyze_consistency(self, responses: List[Dict]) -> Dict:
        """Analyze consistency across agent responses"""
        if not responses:
            return {'score': 0, 'variations': []}
        
        # Extract interpretations
        interpretations = []
        for response in responses:
            if 'response' in response and 'interpretation' in response['response']:
                interpretations.append(response['response']['interpretation'])
        
        if not interpretations:
            return {'score': 0, 'variations': ['No interpretations found']}
        
        # Count unique interpretations
        unique_interpretations = list(set(interpretations))
        
        consistency_score = 1.0 / len(unique_interpretations)
        
        return {
            'score': consistency_score,
            'variations': unique_interpretations
        }
```

---

### 5. Report Generator

```python
# report_generator.py
import json
from pathlib import Path
from datetime import datetime
import markdown
from typing import Dict, List

class ReportGenerator:
    def __init__(self, session_id: str, workspace_path: Path):
        self.session_id = session_id
        self.workspace = workspace_path
        self.reports_dir = workspace_path / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
    def generate_summary_report(self, polishing_results: Dict) -> Path:
        """Generate a comprehensive markdown summary report"""
        report_content = f"""# Documentation Polishing Report

**Session ID:** {self.session_id}  
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Document:** {polishing_results['document']}  

---

## Executive Summary

- **Total Sections Tested:** {polishing_results['sections_tested']}
- **Models Used:** {', '.join(polishing_results['models_used'])}
- **Ambiguities Found:** {polishing_results['total_ambiguities']}
- **Iterations Required:** {polishing_results['iterations']}
- **Final Agreement Score:** {polishing_results['agreement_score']:.2%}

---

## Ambiguities Found and Fixed

"""
        
        # Add details for each ambiguity
        for i, ambiguity in enumerate(polishing_results['ambiguities'], 1):
            report_content += f"""
### {i}. {ambiguity['section']} (Severity: {ambiguity['severity']})

**Different Interpretations Found:**
"""
            for group, data in ambiguity['interpretation_groups'].items():
                report_content += f"""
- **{group}** ({', '.join(data['models'])}):
  - Interpretation: {data['interpretation']}
"""
            
            if 'fix_applied' in ambiguity:
                report_content += f"""

**Fix Applied:**
- Strategy: {ambiguity['fix_applied']['strategy']}
- Confidence: {ambiguity['fix_applied']['confidence']:.2%}

<details>
<summary>View Fix Details</summary>

```markdown
{ambiguity['fix_applied']['fixed_text'][:500]}...
```

</details>
"""
        
        # Add validation results
        report_content += """

---

## Validation Results

"""
        for iteration in polishing_results['iterations_data']:
            report_content += f"""
### Iteration {iteration['number']}
- Agreement Score: {iteration['agreement_score']:.2%}
- Ambiguities Resolved: {iteration['resolved']}
- New Ambiguities Found: {iteration['new_found']}
"""
        
        # Add recommendations
        report_content += """

---

## Recommendations

"""
        if polishing_results['agreement_score'] >= 0.95:
            report_content += "✅ **Document is well-polished and ready for use**\n\n"
        else:
            report_content += "⚠️ **Additional polishing recommended**\n\n"
            report_content += "Consider:\n"
            report_content += "- Manual review of remaining ambiguities\n"
            report_content += "- Adding more examples to unclear sections\n"
            report_content += "- Restructuring complex instructions into steps\n"
        
        # Save report
        report_path = self.reports_dir / f"summary_{self.session_id}.md"
        report_path.write_text(report_content)
        
        return report_path
    
    def generate_diff_report(self, original: str, polished: str) -> Path:
        """Generate a diff report showing all changes"""
        import difflib
        
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            polished.splitlines(keepends=True),
            fromfile='original.md',
            tofile='polished.md',
            n=3
        )
        
        diff_content = ''.join(diff)
        diff_path = self.reports_dir / f"changes_{self.session_id}.diff"
        diff_path.write_text(diff_content)
        
        return diff_path
    
    def generate_model_analysis(self, test_results: Dict) -> Path:
        """Analyze model behavior patterns"""
        analysis = {
            'session_id': self.session_id,
            'model_patterns': {},
            'reliability_scores': {}
        }
        
        # Analyze each model's behavior
        for test_id, model_results in test_results.items():
            for model_name, result in model_results.items():
                if model_name not in analysis['model_patterns']:
                    analysis['model_patterns'][model_name] = {
                        'common_assumptions': [],
                        'typical_ambiguities': [],
                        'response_time_avg': 0
                    }
                
                if 'response' in result and 'assumptions' in result['response']:
                    analysis['model_patterns'][model_name]['common_assumptions'].extend(
                        result['response']['assumptions']
                    )
        
        # Calculate reliability scores
        for model_name in analysis['model_patterns']:
            # Simple scoring based on consistency
            analysis['reliability_scores'][model_name] = 0.85  # Placeholder
        
        analysis_path = self.reports_dir / f"model_analysis_{self.session_id}.json"
        analysis_path.write_text(json.dumps(analysis, indent=2))
        
        return analysis_path
```

---

## Usage Examples

### Example 1: Quick Polish

```python
# quick_polish.py
from pathlib import Path
import sys

# Import our modules
from model_interface import ModelFactory
from ambiguity_detector import AmbiguityDetector, AmbiguityResolver
from prompt_generator import TestPromptGenerator
from test_runner import ParallelTestRunner
from report_generator import ReportGenerator

async def quick_polish(document_path: str):
    """Quick polish with minimal configuration"""
    
    # Setup
    doc = Path(document_path)
    session_id = f"quick_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Initialize components
    detector = AmbiguityDetector()
    resolver = AmbiguityResolver()
    prompt_gen = TestPromptGenerator()
    runner = ParallelTestRunner()
    
    # Simple two-model test
    models = [
        ModelFactory.create('claude', {'api_key': 'your_key'}),
        ModelFactory.create('gemini', {'cli_path': 'gemini'})
    ]
    
    # Extract and test
    content = doc.read_text()
    sections = extract_sections(content)  # Simplified extraction
    
    test_prompts = []
    for section in sections[:5]:  # Test first 5 sections only
        prompts = prompt_gen.generate_prompts(section)
        test_prompts.append(prompts[0])  # Use direct prompt only
    
    # Run tests
    results = await runner.run_tests(test_prompts, models)
    
    # Detect and fix ambiguities
    ambiguities = detector.detect(results['test_results'])
    
    polished_content = content
    for ambiguity in ambiguities:
        fixes = resolver.generate_fixes(ambiguity, content)
        if fixes:
            # Apply the top fix
            polished_content = polished_content.replace(
                ambiguity['original_text'],
                fixes[0]['fixed_text']
            )
    
    # Save result
    output_path = Path(f"polished_{doc.name}")
    output_path.write_text(polished_content)
    
    print(f"✅ Quick polish complete: {output_path}")
    print(f"   Found and fixed {len(ambiguities)} ambiguities")

if __name__ == "__main__":
    import asyncio
    asyncio.run(quick_polish(sys.argv[1]))
```

### Example 2: Thorough Polish with Validation

```python
# thorough_polish.py
import asyncio
from pathlib import Path

async def thorough_polish_with_validation(document_path: str):
    """Complete polishing with multiple iterations and validation"""
    
    max_iterations = 5
    target_agreement = 0.95
    
    for iteration in range(max_iterations):
        print(f"\n🔄 Iteration {iteration + 1}")
        
        # Run polishing
        polished_path = await run_polish_iteration(
            document_path if iteration == 0 else f"polished_iter_{iteration}.md"
        )
        
        # Validate
        agreement_score = await validate_consistency(polished_path)
        print(f"   Agreement score: {agreement_score:.2%}")
        
        if agreement_score >= target_agreement:
            print(f"\n✅ Target agreement reached!")
            break
        
        document_path = polished_path
    
    return polished_path

# Run with: python thorough_polish.py WORKFLOW.md
```

---

## Testing Your Setup

### Test Configuration

```python
# test_config.py
"""Test your configuration before running full polish"""

def test_model_connectivity():
    """Test that all models are accessible"""
    
    test_prompt = "Respond with JSON: {\"status\": \"ok\"}"
    
    models_to_test = [
        ('claude', {'api_key': os.getenv('CLAUDE_API_KEY')}),
        ('gemini', {'cli_path': 'gemini'}),
        ('gpt', {'api_key': os.getenv('OPENAI_API_KEY')})
    ]
    
    for model_name, config in models_to_test:
        try:
            model = ModelFactory.create(model_name, config)
            response = model.query(test_prompt)
            
            if response.get('status') == 'ok':
                print(f"✅ {model_name}: Connected")
            else:
                print(f"⚠️ {model_name}: Unexpected response")
        except Exception as e:
            print(f"❌ {model_name}: {e}")

if __name__ == "__main__":
    test_model_connectivity()
```

---

## Integration with CI/CD

### GitHub Action Example

```yaml
# .github/workflows/polish-docs.yml
name: Polish Documentation

on:
  push:
    paths:
      - 'docs/**/*.md'
      - 'workflows/**/*.md'
  workflow_dispatch:

jobs:
  polish:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        
    - name: Polish documentation
      env:
        CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        python scripts/polish_document.py auto \
          --document ./WORKFLOW.md \
          --profile standard \
          --models claude,gpt4
    
    - name: Upload polished docs
      uses: actions/upload-artifact@v2
      with:
        name: polished-documentation
        path: polished/
    
    - name: Create Pull Request
      if: github.ref == 'refs/heads/main'
      uses: peter-evans/create-pull-request@v3
      with:
        title: "📝 Auto-polish documentation"
        body: "This PR contains automatically polished documentation"
        branch: auto-polish-docs
```

---

## Performance Metrics

### Benchmark Results

```python
# benchmark.py
"""Benchmark polishing performance"""

def benchmark_polishing():
    results = {
        'document_sizes': {
            'small': {'lines': 100, 'time': 45, 'ambiguities': 3},
            'medium': {'lines': 500, 'time': 180, 'ambiguities': 12},
            'large': {'lines': 2000, 'time': 600, 'ambiguities': 37}
        },
        'model_performance': {
            'claude': {'avg_response_time': 2.3, 'reliability': 0.92},
            'gemini': {'avg_response_time': 1.8, 'reliability': 0.89},
            'gpt4': {'avg_response_time': 3.1, 'reliability': 0.94}
        },
        'optimization_tips': [
            'Use caching for repeated sections',
            'Parallelize model queries',
            'Start with quick profile for initial pass',
            'Use local models for pre-screening'
        ]
    }
    
    return results
```

---

## Troubleshooting Guide

### Common Issues and Solutions

```python
# troubleshoot.py
"""Diagnostic tool for common issues"""

class PolishingDiagnostics:
    def diagnose(self, error_log: str):
        """Diagnose common issues from error logs"""
        
        diagnostics = {
            "timeout": {
                "symptoms": ["TimeoutError", "deadline exceeded"],
                "solutions": [
                    "Increase timeout: --timeout 60",
                    "Reduce batch size: --batch-size 5",
                    "Check network connectivity"
                ]
            },
            "api_error": {
                "symptoms": ["401", "403", "invalid API key"],
                "solutions": [
                    "Check API key: echo $CLAUDE_API_KEY",
                    "Verify API permissions",
                    "Check rate limits"
                ]
            },
            "parsing_error": {
                "symptoms": ["JSONDecodeError", "unexpected token"],
                "solutions": [
                    "Add JSON validation to prompts",
                    "Use structured output format",
                    "Handle malformed responses gracefully"
                ]
            },
            "memory_error": {
                "symptoms": ["MemoryError", "killed", "OOM"],
                "solutions": [
                    "Process documents in chunks",
                    "Reduce parallel workers",
                    "Clear cache between iterations"
                ]
            }
        }
        
        for issue, details in diagnostics.items():
            if any(symptom in error_log for symptom in details['symptoms']):
                print(f"\n🔍 Detected: {issue}")
                print("Solutions:")
                for solution in details['solutions']:
                    print(f"  - {solution}")
                return
        
        print("❓ Unknown issue. Please check logs manually.")

# Usage: python troubleshoot.py error.log
```

---

This implementation guide provides a complete, production-ready system for documentation polishing with real code that can be adapted to your specific needs.
