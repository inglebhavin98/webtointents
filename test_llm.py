import logging
from llm_processor import LLMProcessor
from intent_generator import IntentGenerator
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_page_context():
    """Test the page context extraction functionality."""
    llm_processor = LLMProcessor()
    
    # Test sample content
    test_content = """
    Restaurant Inventory Management Software
    
    Efficiently manage your restaurant's inventory with our comprehensive software solution.
    Track stock levels, automate reordering, and reduce waste.
    
    Key Features:
    - Real-time inventory tracking
    - Automated purchase orders
    - Supplier management
    - Waste tracking and analysis
    - Cost optimization
    
    Benefits:
    - Reduce food waste by up to 30%
    - Save time on manual inventory counts
    - Optimize stock levels automatically
    - Get alerts for low stock items
    """
    
    logger.info("Testing page context extraction...")
    context = llm_processor.extract_page_context(test_content)
    
    assert context is not None, "Context extraction failed"
    assert 'page_type' in context, "Missing page type in context"
    assert 'content_structure' in context, "Missing content structure"
    assert 'user_context' in context, "Missing user context"
    assert 'topic_analysis' in context, "Missing topic analysis"
    
    logger.info("Context extraction test passed")
    logger.debug(f"Extracted context: {json.dumps(context, indent=2)}")
    return context

def test_content_analysis(context):
    """Test the comprehensive content analysis."""
    llm_processor = LLMProcessor()
    
    test_content = """
    Restaurant Inventory Management Software
    
    Efficiently manage your restaurant's inventory with our comprehensive software solution.
    Track stock levels, automate reordering, and reduce waste.
    
    Key Features:
    - Real-time inventory tracking
    - Automated purchase orders
    - Supplier management
    - Waste tracking and analysis
    - Cost optimization
    """
    
    logger.info("Testing content analysis...")
    analysis = llm_processor.analyze_content(test_content)
    
    assert analysis is not None, "Content analysis failed"
    assert isinstance(analysis.get('primary_intent'), dict), "Missing or invalid primary intent"
    assert isinstance(analysis.get('user_goals'), list), "Missing or invalid user goals"
    assert isinstance(analysis.get('questions_and_answers'), list), "Missing or invalid Q&A"
    assert isinstance(analysis.get('named_entities'), list), "Missing or invalid entities"
    
    logger.info("Content analysis test passed")
    logger.debug(f"Analysis results: {json.dumps(analysis, indent=2)}")
    return analysis

def test_intent_hierarchy():
    """Test intent hierarchy generation."""
    llm_processor = LLMProcessor()
    intent_generator = IntentGenerator(llm_processor)
    
    # Test data
    test_pages = [
        {
            'url': 'https://example.com/inventory',
            'content': "Restaurant inventory management software...",
            'metadata': {
                'title': 'Inventory Management',
                'description': 'Restaurant inventory software'
            }
        },
        {
            'url': 'https://example.com/pos',
            'content': "Point of sale system for restaurants...",
            'metadata': {
                'title': 'POS System',
                'description': 'Restaurant POS solution'
            }
        }
    ]
    
    logger.info("Testing intent hierarchy generation...")
    hierarchy = intent_generator.generate_intent_hierarchy(test_pages)
    
    assert hierarchy is not None, "Hierarchy generation failed"
    assert isinstance(hierarchy, dict), "Invalid hierarchy format"
    
    logger.info("Intent hierarchy test passed")
    logger.debug(f"Generated hierarchy: {json.dumps(hierarchy, indent=2)}")
    return hierarchy

def test_empty_input():
    """Test handling of empty input."""
    logger.info("Testing empty input handling...")
    llm_processor = LLMProcessor()
    intent_generator = IntentGenerator(llm_processor)
    
    # Test with empty list
    empty_result = intent_generator.generate_intent_hierarchy([])
    assert empty_result is not None, "Should return valid dict for empty input"
    assert 'metadata' in empty_result, "Should include metadata"
    assert empty_result['metadata']['status'] == 'empty', "Should have empty status"
    
    # Test with None
    none_result = intent_generator.generate_intent_hierarchy(None)
    assert none_result is not None, "Should return valid dict for None input"
    assert none_result['metadata']['status'] == 'empty', "Should have empty status"
    
    logger.info("Empty input test passed")
    return empty_result

def test_valid_input():
    """Test processing of valid input."""
    llm_processor = LLMProcessor()
    intent_generator = IntentGenerator(llm_processor)
    
    # Test data
    test_pages = [
        {
            'url': 'https://example.com/product/restaurant-pos',
            'metadata': {
                'title': 'Restaurant POS System',
                'description': 'Modern point of sale system for restaurants'
            },
            'content': [
                {
                    'text': """Complete Restaurant POS System
                    
                    Streamline your restaurant operations with our modern POS system.
                    Designed specifically for restaurants, cafes, and bars.
                    
                    Features:
                    - Order management
                    - Table management
                    - Kitchen display system
                    - Inventory tracking
                    - Staff management
                    - Sales reporting
                    
                    Benefits:
                    - Reduce order errors
                    - Speed up service
                    - Track sales in real-time
                    - Manage staff efficiently"""
                }
            ]
        }
    ]
    
    logger.info("Testing valid input processing...")
    result = intent_generator.generate_intent_hierarchy(test_pages)
    
    assert result is not None, "Should return valid result"
    assert 'intents' in result, "Should include intents"
    assert 'collisions' in result, "Should include collisions"
    assert isinstance(result['intents'], dict), "Intents should be a dictionary"
    
    # Check intent structure
    for category, intents in result['intents'].items():
        if isinstance(intents, list):
            for intent in intents:
                assert 'primary_intent' in intent, "Intent should have primary_intent"
                assert 'user_goals' in intent, "Intent should have user_goals"
                assert 'confidence_score' in intent, "Intent should have confidence_score"
    
    logger.info("Valid input test passed")
    return result

if __name__ == "__main__":
    try:
        logger.info("Starting enhanced test suite...")
        
        # Test empty input handling
        empty_result = test_empty_input()
        print("\nEmpty Input Test Results:")
        print(json.dumps(empty_result, indent=2))
        
        # Test valid input processing
        valid_result = test_valid_input()
        print("\nValid Input Test Results:")
        print(json.dumps(valid_result, indent=2))
        
        logger.info("All tests completed successfully")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise
