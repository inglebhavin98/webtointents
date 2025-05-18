import logging
import json
from typing import Dict, Any, Optional
from .base import BaseProcessor, ProcessingResult

logger = logging.getLogger(__name__)

class ResponseValidator(BaseProcessor):
    """Handles validation and cleaning of LLM responses."""
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data."""
        return 'response' in input_data and isinstance(input_data['response'], str)
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate the output data."""
        return isinstance(output_data, dict) and len(output_data) > 0
    
    def process(self, input_data: Dict[str, Any]) -> ProcessingResult:
        """Clean and validate the LLM response."""
        try:
            if not self.validate_input(input_data):
                return ProcessingResult(
                    success=False,
                    error="Invalid input data structure"
                )
            
            response = input_data['response']
            analysis_type = input_data.get('analysis_type', 'standard')
            
            # Clean the response
            cleaned_response = self._clean_json_response(response)
            
            try:
                # Parse the JSON
                parsed_data = json.loads(cleaned_response)
                
                # Validate based on analysis type
                if analysis_type == 'contact_center':
                    if not self._validate_contact_center_response(parsed_data):
                        return ProcessingResult(
                            success=False,
                            error="Invalid contact center response structure",
                            raw_response=cleaned_response
                        )
                elif analysis_type == 'standard':
                    if not self._validate_standard_response(parsed_data):
                        return ProcessingResult(
                            success=False,
                            error="Invalid standard response structure",
                            raw_response=cleaned_response
                        )
                
                return ProcessingResult(
                    success=True,
                    data=parsed_data,
                    metadata={"analysis_type": analysis_type}
                )
                
            except json.JSONDecodeError as e:
                return ProcessingResult(
                    success=False,
                    error=f"Error parsing JSON: {str(e)}",
                    raw_response=cleaned_response
                )
            
        except Exception as e:
            logger.error(f"Error validating response: {str(e)}")
            return ProcessingResult(
                success=False,
                error=str(e)
            )
    
    def _clean_json_response(self, response: str) -> str:
        """Clean and extract JSON from response."""
        response = response.strip()
        if not response.startswith('{'):
            start_idx = response.find('{')
            if start_idx != -1:
                response = response[start_idx:]
                end_idx = response.rfind('}')
                if end_idx != -1:
                    response = response[:end_idx + 1]
        return response
    
    def _validate_contact_center_response(self, data: Dict[str, Any]) -> bool:
        """Validate contact center intent analysis response."""
        required_keys = [
            'high_level_summary',
            'core_intents',
            'feature_intent_mapping',
            'sub_intents',
            'link_clusters'
        ]
        return all(key in data for key in required_keys)
    
    def _validate_standard_response(self, data: Dict[str, Any]) -> bool:
        """Validate standard intent analysis response."""
        required_keys = [
            'primary_intent',
            'user_goals',
            'questions_and_answers'
        ]
        return all(key in data for key in required_keys) 