import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from .base import ProcessingResult
from .llm_processor import LLMProcessor
from .data_cleaner import DataCleaner
import time
from .content_preparator import ContentPreparator
from .prompt_generator import PromptGenerator
from .response_validator import ResponseValidator

logger = logging.getLogger(__name__)

class PipelineStage(Enum):
    """Enum for different pipeline stages."""
    CONTENT_PREPARATION = "content_preparation"
    PROMPT_GENERATION = "prompt_generation"
    LLM_ANALYSIS = "llm_analysis"
    RESPONSE_VALIDATION = "response_validation"
    DATA_CLEANING = "data_cleaning"

@dataclass
class PipelineResult:
    """Result of the entire pipeline execution."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    stage_results: Dict[str, ProcessingResult] = None
    metadata: Optional[Dict[str, Any]] = None
    stage: Optional[PipelineStage] = None

class AnalysisPipeline:
    """Pipeline for processing and analyzing content."""
    
    def __init__(self, llm_processor: LLMProcessor, progress_callback: Optional[Callable[[str, float], None]] = None):
        self.llm_processor = llm_processor
        self.content_preparator = ContentPreparator()
        self.prompt_generator = PromptGenerator()
        self.response_validator = ResponseValidator()
        self.data_cleaner = DataCleaner()
        self.current_stage = None
        self.stage_results = {}
        self._progress_callback = progress_callback
        self._total_stages = len(PipelineStage)
    
    def _update_progress(self, stage: str, current_stage: int):
        """Update progress through the pipeline."""
        if self._progress_callback:
            progress = current_stage / self._total_stages
            self._progress_callback(stage, progress)
    
    async def run(self, input_data: Dict[str, Any]) -> PipelineResult:
        """Run the analysis pipeline."""
        try:
            logger.info("Starting analysis pipeline")
            start_time = time.time()
            current_stage = 0
            
            # Stage 1: Data Cleaning
            logger.info("Stage 1: Data Cleaning")
            self.current_stage = PipelineStage.DATA_CLEANING
            self._update_progress("Data Cleaning", current_stage)
            cleaning_result = self.data_cleaner.process(input_data)
            if not cleaning_result.success:
                return PipelineResult(
                    success=False,
                    error=f"Data cleaning failed: {cleaning_result.error}",
                    stage=self.current_stage,
                    stage_results={self.current_stage: cleaning_result}
                )
            self.stage_results[PipelineStage.DATA_CLEANING] = cleaning_result
            logger.info(f"Data cleaning completed with {len(cleaning_result.data)} fields")
            current_stage += 1
            
            # Stage 2: Content Preparation
            logger.info("Stage 2: Content Preparation")
            self.current_stage = PipelineStage.CONTENT_PREPARATION
            self._update_progress("Content Preparation", current_stage)
            prep_result = self.content_preparator.process(cleaning_result.data)
            if not prep_result.success:
                return PipelineResult(
                    success=False,
                    error=f"Content preparation failed: {prep_result.error}",
                    stage=self.current_stage,
                    stage_results={self.current_stage: prep_result}
                )
            self.stage_results[PipelineStage.CONTENT_PREPARATION] = prep_result
            logger.info("Content preparation completed")
            current_stage += 1
            
            # Stage 3: Prompt Generation
            logger.info("Stage 3: Prompt Generation")
            self.current_stage = PipelineStage.PROMPT_GENERATION
            self._update_progress("Prompt Generation", current_stage)
            prompt_result = self.prompt_generator.process(prep_result.data)
            if not prompt_result.success:
                return PipelineResult(
                    success=False,
                    error=f"Prompt generation failed: {prompt_result.error}",
                    stage=self.current_stage,
                    stage_results={self.current_stage: prompt_result}
                )
            self.stage_results[PipelineStage.PROMPT_GENERATION] = prompt_result
            logger.info("Prompt generation completed")
            current_stage += 1
            
            # Stage 4: LLM Analysis
            logger.info("Stage 4: LLM Analysis")
            self.current_stage = PipelineStage.LLM_ANALYSIS
            self._update_progress("LLM Analysis", current_stage)
            analysis_result = await self.llm_processor.analyze_contact_center_intents(prompt_result.data)
            if not analysis_result.success:
                return PipelineResult(
                    success=False,
                    error=f"LLM analysis failed: {analysis_result.error}",
                    stage=self.current_stage,
                    stage_results={self.current_stage: analysis_result}
                )
            self.stage_results[PipelineStage.LLM_ANALYSIS] = analysis_result
            logger.info("LLM analysis completed")
            current_stage += 1
            
            # Stage 5: Response Validation
            logger.info("Stage 5: Response Validation")
            self.current_stage = PipelineStage.RESPONSE_VALIDATION
            self._update_progress("Response Validation", current_stage)
            validation_result = self.response_validator.process(analysis_result.data)
            if not validation_result.success:
                return PipelineResult(
                    success=False,
                    error=f"Response validation failed: {validation_result.error}",
                    stage=self.current_stage,
                    stage_results={self.current_stage: validation_result}
                )
            self.stage_results[PipelineStage.RESPONSE_VALIDATION] = validation_result
            logger.info("Response validation completed")
            current_stage += 1
            
            # Pipeline completed
            self._update_progress("Complete", 1.0)
            
            end_time = time.time()
            duration = end_time - start_time
            
            return PipelineResult(
                success=True,
                data=validation_result.data,
                metadata={
                    "duration": duration,
                    "stage_results": self.stage_results
                },
                stage_results=self.stage_results
            )
            
        except Exception as e:
            logger.error(f"Pipeline failed at stage {self.current_stage}: {str(e)}")
            return PipelineResult(
                success=False,
                error=str(e),
                stage=self.current_stage,
                stage_results=self.stage_results
            )
    
    def get_stage_result(self, stage: PipelineStage) -> Optional[ProcessingResult]:
        """Get the result of a specific pipeline stage."""
        return self.stage_results.get(stage)
    
    def get_all_stage_results(self) -> Dict[str, ProcessingResult]:
        """Get results from all pipeline stages."""
        return self.stage_results.copy() 