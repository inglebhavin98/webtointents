# Intent Discovery Tool - TODOs and Improvements

## Current State
- Moving from hybrid NLP+LLM to LLM-only approach
- Basic two-step analysis (context extraction + content analysis)
- Using OpenRouter API with qwen3-0.6b model

## Proposed Enhancements

### 1. Enhanced Context Extraction
- Expand page context analysis to include:
  - Content type & structure detection
  - User context understanding
  - Topic analysis
  - Intent signal detection
- Example structure:
```json
{
    "page_type": "support/product/faq/etc",
    "content_structure": {
        "main_sections": [],
        "content_hierarchy": "flat/nested/hierarchical"
    },
    "user_context": {
        "target_audience": "",
        "user_needs": [],
        "expertise_level": ""
    }
}
```

### 2. Comprehensive Content Analysis
- Enhance content analysis with:
  - Detailed intent analysis with confidence scores
  - Goal-oriented user journey mapping
  - Question generation with variations
  - Rich entity recognition with context
  - Topic hierarchy mapping
  - Smart response generation
- Example structure:
```json
{
    "primary_intent": {
        "name": "",
        "description": "",
        "confidence": 0.0
    },
    "user_goals": [
        {
            "goal": "",
            "steps": [],
            "blockers": []
        }
    ]
}
```

### 3. Learning Capabilities
- Store successful analyses for pattern learning
- Implement feedback loop for continuous improvement
- Add example-based prompting using past successful cases
- Potential features:
  - Store high-confidence analyses
  - Track common patterns
  - Build domain-specific knowledge

### 4. Infrastructure Improvements
- Remove NLPProcessor dependencies:
  - Delete nlp_processor.py
  - Remove spaCy and BERTopic dependencies
  - Update requirements.txt
- Update IntentGenerator to work with LLM-only approach
- Clean up unused configuration files

### 5. UI/UX Improvements
- Remove Intent Driver Management tab
- Add confidence score visualization
- Show analysis steps in real-time
- Add export functionality for analysis results

### 6. Error Handling & Logging
- Implement better error handling for LLM API calls
- Add retry mechanism for failed API calls
- Improve logging for debugging
- Add analysis quality metrics

### 7. Performance Optimization
- Implement batch processing for multiple pages
- Add caching for common analyses
- Optimize prompt length and token usage
- Consider parallel processing where possible

### 8. Testing & Validation
- Add unit tests for LLMProcessor
- Create test suite with sample pages
- Implement validation metrics
- Add automated testing workflow

### 9. Documentation
- Update API documentation
- Add example usage and patterns
- Document prompt engineering decisions
- Create troubleshooting guide

## Priority Order
1. Infrastructure Improvements (remove old dependencies)
2. Enhanced Context Extraction
3. Comprehensive Content Analysis
4. Error Handling & Logging
5. UI/UX Improvements
6. Learning Capabilities
7. Performance Optimization
8. Testing & Validation
9. Documentation

## Notes
- Current NLPProcessor functionality is being replaced by enhanced LLM prompts
- No need for separate ML models (spaCy, BERTopic)
- Focus on making the LLM do the heavy lifting
- Consider fine-tuning model if needed later
