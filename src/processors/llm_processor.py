import logging
import openai
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from .base import BaseProcessor, ProcessingResult
from .content_preparator import ContentPreparator
from .prompt_generator import PromptGenerator
from .response_validator import ResponseValidator

logger = logging.getLogger(__name__)

class LLMProcessor(BaseProcessor):
    """Main processor that orchestrates the LLM analysis pipeline."""
    
    def __init__(self):
        """Initialize the LLM processor with OpenRouter configuration."""
        try:
            load_dotenv()
            self.api_key = os.getenv('OPENROUTER_API_KEY')
            self.site_url = os.getenv('SITE_URL', 'http://localhost:8501')
            self.site_name = os.getenv('SITE_NAME', 'Intent Discovery Tool')
            self.model = "meta-llama/llama-3.3-8b-instruct:free"
            
            if not self.api_key:
                raise ValueError("OPENROUTER_API_KEY not found in environment variables")
            
            logger.info("Initializing OpenRouter client")
            openai.api_key = self.api_key
            openai.api_base = "https://openrouter.ai/api/v1"
            logger.info(f"OpenRouter client initialized successfully with model: {self.model}")
            
            # Initialize processors
            self.content_preparator = ContentPreparator()
            self.prompt_generator = PromptGenerator()
            self.response_validator = ResponseValidator()
            
        except Exception as e:
            logger.error(f"Error initializing LLM processor: {str(e)}")
            raise
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data."""
        required_keys = ['page_data', 'analysis_type']
        return all(key in input_data for key in required_keys)
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate the output data."""
        return isinstance(output_data, dict) and len(output_data) > 0
    
    def process(self, input_data: Dict[str, Any]) -> ProcessingResult:
        """Process the input data through the analysis pipeline."""
        try:
            if not self.validate_input(input_data):
                return ProcessingResult(
                    success=False,
                    error="Invalid input data structure"
                )
            
            # Step 1: Prepare content
            content_result = self.content_preparator.process(input_data['page_data'])
            if not content_result.success:
                return content_result
            
            # Step 2: Generate prompt
            prompt_input = {
                'content': content_result.data['content'],
                'analysis_type': input_data['analysis_type']
            }
            prompt_result = self.prompt_generator.process(prompt_input)
            if not prompt_result.success:
                return prompt_result
            
            # Step 3: Make LLM request
            llm_result = self._make_llm_request(
                prompt_result.data['prompt'],
                self._get_system_message(input_data['analysis_type'])
            )
            if not llm_result.success:
                return llm_result
            
            # Step 4: Validate response
            validation_input = {
                'response': llm_result.raw_response,
                'analysis_type': input_data['analysis_type']
            }
            validation_result = self.response_validator.process(validation_input)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error in processing pipeline: {str(e)}")
            return ProcessingResult(
                success=False,
                error=str(e)
            )
    
    def _make_llm_request(self, prompt: str, system_message: str) -> ProcessingResult:
        """Make a request to the LLM and handle the response."""
        try:
            completion = openai.ChatCompletion.create(
                headers={
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name,
                },
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            response = completion.choices[0].message.content
            return ProcessingResult(success=True, raw_response=response)
            
        except Exception as e:
            logger.error(f"Error making LLM request: {str(e)}")
            return ProcessingResult(success=False, error=str(e))
    
    def _get_system_message(self, analysis_type: str) -> str:
        """Get the appropriate system message for the analysis type."""
        if analysis_type == 'contact_center':
            return "You are an expert intent discovery analyst specializing in contact center transformation."
        else:
            return "You are an expert NLU analyst specializing in intent discovery." 