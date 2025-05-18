import logging
from typing import Dict, Any
from .base import BaseProcessor, ProcessingResult

logger = logging.getLogger(__name__)

class PromptGenerator(BaseProcessor):
    """Handles generation of prompts for different analysis types."""
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data."""
        required_keys = ['content', 'analysis_type']
        return all(key in input_data for key in required_keys)
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate the output data."""
        return isinstance(output_data, str) and len(output_data) > 0
    
    def process(self, input_data: Dict[str, Any]) -> ProcessingResult:
        """Generate a prompt based on the analysis type and content."""
        try:
            if not self.validate_input(input_data):
                return ProcessingResult(
                    success=False,
                    error="Invalid input data structure"
                )
            
            content = input_data['content']
            analysis_type = input_data['analysis_type']
            
            if analysis_type == 'contact_center':
                prompt = self._get_contact_center_prompt(content)
            elif analysis_type == 'standard':
                prompt = self._get_standard_prompt(content)
            else:
                return ProcessingResult(
                    success=False,
                    error=f"Unsupported analysis type: {analysis_type}"
                )
            
            if not self.validate_output(prompt):
                return ProcessingResult(
                    success=False,
                    error="Failed to generate valid prompt"
                )
            
            return ProcessingResult(
                success=True,
                data={"prompt": prompt},
                metadata={"analysis_type": analysis_type}
            )
            
        except Exception as e:
            logger.error(f"Error generating prompt: {str(e)}")
            return ProcessingResult(
                success=False,
                error=str(e)
            )
    
    def _get_contact_center_prompt(self, content: str) -> str:
        """Generate prompt for contact center intent analysis."""
        return f"""You are an Intent Discovery Expert helping a contact center transformation team.

Given the following structured website content, analyze and return a comprehensive intent map.

Content to analyze:
{content}

Return your analysis in this JSON structure:

{{
    "high_level_summary": {{
        "offering": "2-3 sentence description of company offering",
        "target_audience": "description of target users"
    }},
    "core_intents": [
        {{
            "intent_name": "what the user wants to do",
            "signals": [
                {{
                    "type": "header/paragraph/testimonial/link",
                    "content": "the specific content supporting this intent",
                    "confidence": 0.0 to 1.0
                }}
            ],
            "priority": "high/medium/low"
        }}
    ],
    "feature_intent_mapping": [
        {{
            "feature": "specific feature name",
            "intent": "associated user intent",
            "value_proposition": "why this matters to user"
        }}
    ],
    "sub_intents": [
        {{
            "parent_intent": "name of major intent",
            "children": [
                {{
                    "name": "sub-intent name",
                    "motivation": "user motivation",
                    "signals": ["supporting evidence"]
                }}
            ]
        }}
    ],
    "link_clusters": [
        {{
            "cluster_name": "Lead Generation/Content Marketing/Support/Trust Building",
            "urls": ["list of URLs in this cluster"],
            "pattern": "why these links are grouped together"
        }}
    ]
}}

Important:
1. Only use information present in the provided content
2. Do not make assumptions or add information not in the source
3. Provide confidence scores where relevant
4. Link all insights to specific content signals"""

    def _get_standard_prompt(self, content: str) -> str:
        """Generate prompt for standard intent analysis."""
        return f"""Analyze the following content and identify user intents and goals.

Content:
{content}

Return your analysis in this JSON structure:
{{
    "primary_intent": {{
        "name": "main intent name",
        "description": "detailed description",
        "confidence": 0.0 to 1.0
    }},
    "user_goals": [
        {{
            "goal": "specific user goal",
            "steps": ["steps to achieve goal"],
            "blockers": ["potential obstacles"]
        }}
    ],
    "questions_and_answers": [
        {{
            "question": "natural user question",
            "answer": "derived answer from content",
            "variations": ["question paraphrases"]
        }}
    ]
}}""" 