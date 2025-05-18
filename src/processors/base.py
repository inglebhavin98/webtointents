from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ProcessingResult:
    """Base class for all processing results."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    raw_response: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseProcessor(ABC):
    """Base class for all processors."""
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> ProcessingResult:
        """Process the input data and return a result."""
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data."""
        pass
    
    @abstractmethod
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate the output data."""
        pass 