import logging
from typing import Dict, Any, List
from .base import BaseProcessor, ProcessingResult

logger = logging.getLogger(__name__)

class ContentPreparator(BaseProcessor):
    """Handles content preparation and formatting for analysis."""
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data."""
        # Accept either the old structure or the new structure
        has_old_structure = all(key in input_data for key in ['metadata', 'content'])
        has_new_structure = all(key in input_data for key in ['url', 'domain'])
        return has_old_structure or has_new_structure
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate the output data."""
        return isinstance(output_data, dict) and 'content' in output_data and len(output_data['content']) > 0
    
    def process(self, input_data: Dict[str, Any]) -> ProcessingResult:
        """Prepare structured content from page data for analysis."""
        try:
            if not self.validate_input(input_data):
                return ProcessingResult(
                    success=False,
                    error="Invalid input data structure"
                )
            
            sections = []
            
            # Add URL and domain information
            sections.append(f"== Page Information ==")
            sections.append(f"URL: {input_data.get('url', '')}")
            sections.append(f"Domain: {input_data.get('domain', '')}")
            
            # Add metadata if present
            metadata = input_data.get('metadata', {})
            if metadata:
                sections.append("\n== Page Metadata ==")
                for key, value in metadata.items():
                    if isinstance(value, str):
                        sections.append(f"{key}: {value}")
            
            # Add structure content
            if 'structure' in input_data:
                sections.append("\n== Page Structure ==")
                structure = input_data['structure']
                if isinstance(structure, dict):
                    for key, value in structure.items():
                        if isinstance(value, str):
                            sections.append(f"{key}: {value}")
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict) and 'text' in item:
                                    sections.append(f"- {item['text']}")
            
            # Add navigation content
            if 'navigation' in input_data:
                sections.append("\n== Navigation ==")
                navigation = input_data['navigation']
                if isinstance(navigation, dict):
                    for key, value in navigation.items():
                        if isinstance(value, list):
                            sections.append(f"{key}:")
                            for item in value:
                                if isinstance(item, dict) and 'text' in item:
                                    sections.append(f"- {item['text']}")
            
            # Add any content from the content list
            if 'content' in input_data and isinstance(input_data['content'], list):
                sections.append("\n== Main Content ==")
                for item in input_data['content']:
                    if isinstance(item, str):
                        sections.append(item)
                    elif isinstance(item, dict) and 'text' in item:
                        sections.append(item['text'])
            
            prepared_content = "\n".join(sections)
            
            if not prepared_content.strip():
                return ProcessingResult(
                    success=False,
                    error="No content could be extracted from the page"
                )
            
            return ProcessingResult(
                success=True,
                data={"content": prepared_content},
                metadata={"sections": len(sections)}
            )
            
        except Exception as e:
            logger.error(f"Error preparing content: {str(e)}")
            return ProcessingResult(
                success=False,
                error=str(e)
            ) 