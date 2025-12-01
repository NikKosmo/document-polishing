#!/usr/bin/env python3
"""
Documentation Polishing System - Main Entry Point

Usage:
    python polish.py <document.md> [options]
    python polish.py --list-models
    python polish.py --version
"""

import sys
import argparse
import yaml
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from model_interface import ModelManager
from document_processor import DocumentProcessor
from prompt_generator import PromptGenerator


__version__ = "0.1.0"


class DocumentPolisher:
    """Main polishing orchestrator"""
    
    def __init__(self, document_path: str, config_path: str = "config.yaml"):
        self.document_path = Path(document_path)
        self.config_path = Path(config_path)
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize components
        self.model_manager = ModelManager(self.config['models'])
        self.processor = DocumentProcessor(str(self.document_path))
        self.prompt_gen = PromptGenerator()
        
        # Setup workspace
        self.session_id = f"polish_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.workspace = Path(self.config['settings']['workspace_dir']) / self.session_id
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        print(f"Session ID: {self.session_id}")
        print(f"Workspace: {self.workspace}")
    
    def _load_config(self) -> dict:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            print(f"Config file not found: {self.config_path}")
            print("Using default configuration")
            return self._default_config()
        
        with open(self.config_path) as f:
            return yaml.safe_load(f)
    
    def _default_config(self) -> dict:
        """Return default configuration"""
        return {
            'models': {
                'claude': {'type': 'cli', 'command': 'claude', 'enabled': True},
                'gemini': {'type': 'cli', 'command': 'gemini', 'enabled': True},
            },
            'profiles': {
                'standard': {'models': ['claude', 'gemini'], 'iterations': 1}
            },
            'settings': {
                'default_profile': 'standard',
                'workspace_dir': 'workspace',
                'output_dir': 'output'
            }
        }
    
    def polish(self, models: list = None, profile: str = None):
        """Run the polishing process"""
        print(f"\n{'='*60}")
        print(f"Starting Documentation Polish")
        print(f"Document: {self.document_path}")
        print(f"{'='*60}\n")
        
        # Determine which models to use
        if models is None:
            if profile:
                models = self.config['profiles'][profile]['models']
            else:
                default_profile = self.config['settings']['default_profile']
                models = self.config['profiles'][default_profile]['models']
        
        print(f"Using models: {', '.join(models)}\n")
        
        # Step 1: Extract sections
        print("Step 1: Extracting testable sections...")
        sections = self.processor.extract_sections()
        print(f"  Found {len(sections)} sections")
        for i, summary in enumerate(self.processor.get_section_summary()):
            print(f"  {summary}")
        
        if len(sections) == 0:
            print("\n⚠️  No testable sections found in document")
            return
        
        # Step 2: Test sections with models
        print(f"\nStep 2: Testing sections with models...")
        test_results = {}
        
        for i, section in enumerate(sections):
            print(f"\n  Testing section [{i}]: {section['header']}")
            prompt = self.prompt_gen.create_interpretation_prompt(section)
            
            # Query all models
            results = self.model_manager.query_all(prompt, models)
            test_results[f"section_{i}"] = {
                'section': section,
                'results': results
            }
        
        # Save test results
        results_file = self.workspace / "test_results.json"
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        print(f"\n  Test results saved to: {results_file}")
        
        # Step 3: Detect ambiguities
        print(f"\nStep 3: Detecting ambiguities...")
        ambiguities = self._detect_ambiguities(test_results)
        print(f"  Found {len(ambiguities)} potential ambiguities")
        
        # Step 4: Generate report
        print(f"\nStep 4: Generating report...")
        report = self._generate_report(test_results, ambiguities)
        
        report_file = self.workspace / "report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"  Report saved to: {report_file}")
        
        # Step 5: Create polished version (if ambiguities found)
        if ambiguities:
            print(f"\nStep 5: Creating polished version...")
            polished_content = self._create_polished_version(ambiguities)
            
            polished_file = self.workspace / f"{self.document_path.stem}_polished.md"
            with open(polished_file, 'w') as f:
                f.write(polished_content)
            print(f"  Polished document saved to: {polished_file}")
        else:
            print(f"\n✓ No ambiguities found - document is clear!")
            polished_file = None
        
        # Summary
        print(f"\n{'='*60}")
        print(f"Polish Complete!")
        print(f"{'='*60}")
        print(f"Workspace: {self.workspace}")
        print(f"Report: {report_file}")
        if polished_file:
            print(f"Polished: {polished_file}")
        print()
        
        return {
            'workspace': str(self.workspace),
            'report': str(report_file),
            'polished': str(polished_file) if polished_file else None,
            'ambiguities_found': len(ambiguities)
        }
    
    def _detect_ambiguities(self, test_results: dict) -> list:
        """Detect ambiguities by comparing model responses"""
        ambiguities = []
        
        for section_id, data in test_results.items():
            section = data['section']
            results = data['results']
            
            # Extract interpretations from each model
            interpretations = {}
            assumptions = {}
            
            for model_name, response in results.items():
                if response.get('error'):
                    continue
                
                # Try to extract interpretation
                if isinstance(response, dict):
                    if 'raw_response' in response:
                        # Parse raw response
                        text = response['raw_response']
                        interpretations[model_name] = text[:200]  # First 200 chars
                    elif 'interpretation' in response:
                        interpretations[model_name] = response['interpretation']
                    
                    if 'assumptions' in response and response['assumptions']:
                        assumptions[model_name] = response['assumptions']
            
            # Check if interpretations differ significantly
            if len(interpretations) >= 2:
                unique_interps = set(interpretations.values())
                
                if len(unique_interps) > 1:
                    ambiguities.append({
                        'section_id': section_id,
                        'section_header': section['header'],
                        'section_content': section['content'],
                        'interpretations': interpretations,
                        'assumptions': assumptions,
                        'severity': 'high' if len(unique_interps) == len(interpretations) else 'medium'
                    })
                elif assumptions:
                    # Models agree but made assumptions
                    ambiguities.append({
                        'section_id': section_id,
                        'section_header': section['header'],
                        'section_content': section['content'],
                        'interpretations': interpretations,
                        'assumptions': assumptions,
                        'severity': 'low'
                    })
        
        return ambiguities
    
    def _generate_report(self, test_results: dict, ambiguities: list) -> str:
        """Generate markdown report"""
        report = f"""# Documentation Polish Report

**Session ID:** {self.session_id}
**Document:** {self.document_path}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Sections Tested:** {len(test_results)}
- **Ambiguities Found:** {len(ambiguities)}
- **Models Used:** {', '.join(self.model_manager.list_available())}

## Ambiguities Detected

"""
        
        if not ambiguities:
            report += "*No ambiguities detected. The documentation appears clear.*\n"
        else:
            for i, amb in enumerate(ambiguities, 1):
                report += f"### {i}. {amb['section_header']} ({amb['severity']} severity)\n\n"
                report += f"**Original Text:**\n```\n{amb['section_content']}\n```\n\n"
                
                report += "**Different Interpretations:**\n"
                for model, interp in amb['interpretations'].items():
                    report += f"- **{model}:** {interp}\n"
                report += "\n"
                
                if amb.get('assumptions'):
                    report += "**Assumptions Made:**\n"
                    for model, assum in amb['assumptions'].items():
                        report += f"- **{model}:** {', '.join(assum) if isinstance(assum, list) else assum}\n"
                    report += "\n"
        
        report += "\n## Detailed Test Results\n\n"
        
        for section_id, data in test_results.items():
            section = data['section']
            report += f"### {section['header']}\n\n"
            
            for model, response in data['results'].items():
                report += f"**{model}:**\n"
                if response.get('error'):
                    report += f"- Error: {response.get('message', 'Unknown error')}\n"
                else:
                    report += f"```json\n{json.dumps(response, indent=2)}\n```\n"
                report += "\n"
        
        return report
    
    def _create_polished_version(self, ambiguities: list) -> str:
        """Create polished version with clarifications"""
        content = self.processor.get_full_content()
        
        # For now, add clarification notes after ambiguous sections
        # (Full fix generation will be in Increment 3)
        
        for amb in ambiguities:
            original = amb['section_content']
            
            # Create clarification note
            clarification = f"\n\n**⚠️ CLARIFICATION NEEDED:**\n"
            clarification += "Different interpretations were found:\n"
            for model, interp in amb['interpretations'].items():
                clarification += f"- {model}: {interp}\n"
            
            # Simple replacement (will be improved in Increment 3)
            if original in content:
                content = content.replace(original, original + clarification, 1)
        
        return content


def main():
    parser = argparse.ArgumentParser(
        description='Documentation Polishing System',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('document', nargs='?', help='Path to markdown document')
    parser.add_argument('--models', help='Comma-separated list of models to use')
    parser.add_argument('--profile', help='Profile to use (quick, standard, thorough)')
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    parser.add_argument('--list-models', action='store_true', help='List available models')
    parser.add_argument('--version', action='store_true', help='Show version')
    
    args = parser.parse_args()
    
    if args.version:
        print(f"Documentation Polishing System v{__version__}")
        return
    
    if args.list_models:
        config_path = Path(args.config)
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
            print("Available models:")
            for name, cfg in config['models'].items():
                status = "✓" if cfg.get('enabled', True) else "✗"
                print(f"  {status} {name} ({cfg.get('type', 'unknown')})")
        else:
            print("Config file not found")
        return
    
    if not args.document:
        parser.print_help()
        return
    
    # Parse models if provided
    models = None
    if args.models:
        models = [m.strip() for m in args.models.split(',')]
    
    # Run polishing
    polisher = DocumentPolisher(args.document, args.config)
    result = polisher.polish(models=models, profile=args.profile)


if __name__ == "__main__":
    main()
