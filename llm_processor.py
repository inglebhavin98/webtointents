import logging
import openai
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
import json
import uuid

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class LLMProcessor:
    def __init__(self):
        """Initialize the LLM processor with OpenRouter configuration."""
        try:
            load_dotenv()
            self.api_key = os.getenv('OPENROUTER_API_KEY')
            self.site_url = os.getenv('SITE_URL', 'http://localhost:8501')
            self.site_name = os.getenv('SITE_NAME', 'Intent Discovery Tool')
            self.model = "qwen/qwen3-0.6b-04-28:free"
            
            if not self.api_key:
                raise ValueError("OPENROUTER_API_KEY not found in environment variables")
            
            logger.info("Initializing OpenRouter client")
            openai.api_key = self.api_key
            openai.api_base = "https://openrouter.ai/api/v1"
            logger.info(f"OpenRouter client initialized successfully with model: {self.model}")
            
        except Exception as e:
            logger.error(f"Error initializing LLM processor: {str(e)}")
            raise

    def extract_page_context(self, text: str) -> Dict[str, Any]:
        """Step 1: Deep content understanding and classification."""
        try:
            if not text or not isinstance(text, str):
                logger.error("Invalid input text for context extraction")
                return None

            # Enhanced prompt for better content understanding
            prompt_1 = f"""You are an expert content and intent analyst.

Analysis Task:
Analyze this webpage content for a complete contextual understanding.

Points to analyze:
1. Content Type & Structure
   - What type of page is this? (product, support, FAQ, etc.)
   - How is the content structured?
   - Are there distinct sections?

2. User Context
   - Who is the target audience?
   - What problem or need brings users here?
   - What's their likely expertise level?

3. Topic Analysis
   - What's the main topic or theme?
   - Are there subtopics?
   - How technical is the content?

4. Intent Signals
   - What actions can users take?
   - What questions does it answer?
   - What goals does it help achieve?

Return your analysis in this JSON format:
{{
    "page_type": "support/product/faq/etc",
    "content_structure": {{
        "main_sections": ["list of main sections"],
        "content_hierarchy": "flat/nested/hierarchical"
    }},
    "user_context": {{
        "target_audience": "description of users",
        "user_needs": ["list of user needs"],
        "expertise_level": "beginner/intermediate/expert"
    }},
    "topic_analysis": {{
        "main_theme": "primary topic",
        "subtopics": ["list of subtopics"],
        "technical_level": "low/medium/high"
    }},
    "intent_signals": {{
        "actions": ["possible user actions"],
        "questions_addressed": ["key questions answered"],
        "user_goals": ["achievable goals"]
    }}
}}

Raw Content:
{text}"""

            logger.debug("Sending enhanced prompt for context extraction:")
            logger.debug(f"System: 'You are an expert content and intent analyst.'")
            logger.debug(f"User prompt: {prompt_1}")

            completion = openai.ChatCompletion.create(
                headers={
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name,
                },
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert content and intent analyst."},
                    {"role": "user", "content": prompt_1}
                ],
                temperature=0.3
            )
            response = completion.choices[0].message.content
            logger.info("Received enhanced context analysis")
            logger.debug(f"Context analysis: {response}")
            try:
                context = json.loads(response)
                return context
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing context JSON: {str(e)}")
                return None
        except Exception as e:
            logger.error(f"Error extracting page context: {str(e)}")
            return None

    def analyze_content(self, text: str) -> Dict[str, Any]:
        """Step 2: Comprehensive intent and entity analysis."""
        try:
            logger.info("Starting enhanced content analysis...")
            if not text or not isinstance(text, str):
                logger.error("Invalid input text")
                return None

            # Get rich context first
            logger.info("Calling enhanced extract_page_context...")
            page_context = self.extract_page_context(text)
            logger.info(f"extract_page_context returned: {page_context is not None}")
            
            if not page_context:
                logger.error("Failed to extract page context")
                return None

            step1_output = json.dumps(page_context, ensure_ascii=False)
            logger.info("Rich page context extracted successfully")

            # Enhanced prompt for comprehensive analysis
            prompt_2 = f"""Based on the rich page context below, perform a comprehensive content analysis.

Page Context:
{step1_output}

Content:
{text}

Analyze and extract all insights using this structure:
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
    ],
    "named_entities": [
        {{
            "type": "PERSON/ORG/PRODUCT/etc",
            "value": "entity text",
            "context": "how it's used in content"
        }}
    ],
    "topic_hierarchy": {{
        "main_topic": "primary topic",
        "subtopics": ["related subtopics"],
        "keywords": ["important terms"]
    }},
    "suggested_responses": [
        {{
            "trigger": "when to use this response",
            "response": "suggested response text",
            "followup_questions": ["potential follow-ups"]
        }}
    ],
    "intent_relationships": {{
        "parent_intent": "broader category",
        "related_intents": ["similar intents"],
        "child_intents": ["more specific intents"]
    }},
    "metadata": {{
        "content_quality_score": 0.0 to 1.0,
        "technical_complexity": "low/medium/high",
        "action_orientation": "informative/transactional/both"
    }}
}}"""

            logger.info("About to make OpenRouter API call for enhanced analysis...")
            completion = openai.ChatCompletion.create(
                headers={
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name,
                },
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert NLU analyst specializing in deep content understanding and intent discovery."},
                    {"role": "user", "content": prompt_2}
                ],
                temperature=0.3
            )
            response = completion.choices[0].message.content
            logger.info("Received comprehensive analysis")
            logger.debug(f"Analysis response: {response}")
            try:
                analysis = json.loads(response)
                return analysis
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON response: {str(e)}")
                return None
        except Exception as e:
            logger.error(f"Error in enhanced content analysis: {str(e)}")
            return None

    def process_page_for_intents(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a page's content to generate intents and insights using only LLM (NLPProcessor temporarily disabled)."""
        try:
            logger.info("Starting page processing for intents (LLM only, NLP disabled)")
            # Extract main content
            logger.info("Extracting main content from page data...")
            main_text = ""
            if isinstance(page_data, dict):
                logger.debug(f"Page data keys: {list(page_data.keys())}")
                if 'structure' in page_data and 'main_content' in page_data['structure']:
                    logger.info("Found main_content in structure")
                    main_content = page_data['structure']['main_content']
                    if isinstance(main_content, list):
                        main_text = ' '.join([item.get('text', '') for item in main_content if isinstance(item, dict)])
                    elif isinstance(main_content, str):
                        main_text = main_content
                elif 'content' in page_data:
                    logger.info("Using content field")
                    main_text = page_data['content']
                elif 'text' in page_data:
                    logger.info("Using text field")
                    main_text = page_data['text']
            
            if not main_text:
                logger.warning("No text content found in page data")
                return None
                
            logger.info(f"Extracted text length: {len(main_text)} characters")
            logger.debug(f"First 200 characters of extracted text: {main_text[:200]}")
            
            # Only use LLM for analysis
            logger.info("Calling analyze_content...")
            analysis = self.analyze_content(main_text)
            logger.info(f"analyze_content returned: {analysis is not None}")
            
            if analysis:
                logger.info("Creating processed data from analysis...")
                processed_data = {
                    'intent_id': f"intent_{uuid.uuid4().hex[:8]}",
                    'context_understanding': analysis.get('context_understanding', ''),
                    'primary_intent': analysis.get('primary_intent', ''),
                    'user_goals': analysis.get('user_goals', []),
                    'natural_questions': analysis.get('natural_questions', []),
                    'named_entities': analysis.get('named_entities', []),
                    'bot_response': analysis.get('bot_response', ''),
                    'related_intents': analysis.get('related_intents', []),
                    'confidence_score': analysis.get('confidence_score', 0.0)
                }
                logger.info("Successfully processed page for intents (LLM only)")
                return processed_data
            
            logger.warning("Analysis returned None")
            return None
            
        except Exception as e:
            logger.error(f"Error processing page for intents (LLM only): {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error traceback:", exc_info=True)  # This will log the full traceback
            return None

    def generate_intent(self, text):
        """Generate intent from text using DeepSeek model."""
        try:
            if not text or not isinstance(text, str):
                logger.error("Invalid input text")
                return None

            logger.info("Generating intent from text")
            logger.debug(f"Input text: {text[:100]}...")  # Log first 100 chars

            prompt = f"""Analyze the following text and identify the main user intent or purpose. 
            Return a JSON object with the following structure:
            {{
                "primary_intent": "main purpose or goal",
                "secondary_intents": ["related or supporting intents"],
                "confidence": 0.95
            }}

            Text to analyze: {text}"""

            # Log the prompt being sent
            logger.debug("Sending prompt to LLM for intent generation:")
            logger.debug(f"User prompt: {prompt}")

            logger.info("Sending request to OpenRouter")
            completion = openai.ChatCompletion.create(
                headers={
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name,
                },
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7  # Added temperature for better response variety
            )

            response = completion.choices[0].message.content
            logger.info("Received response from OpenRouter")
            logger.debug(f"Response: {response}")

            return response

        except Exception as e:
            logger.error(f"Error generating intent: {str(e)}")
            return None

    def generate_intent_hierarchy(self, texts):
        """Generate a hierarchical structure of intents from multiple texts."""
        try:
            if not texts or not isinstance(texts, list):
                logger.error("Invalid input texts")
                return None

            logger.info("Generating intent hierarchy")
            logger.debug(f"Number of texts to process: {len(texts)}")

            prompt = f"""Analyze the following texts and create a hierarchical structure of user intents.
            Return a JSON object with the following structure:
            {{
                "primary_intent": "main purpose or goal",
                "sub_intents": [
                    {{
                        "intent": "specific intent",
                        "confidence": 0.95,
                        "supporting_text": "relevant text snippet"
                    }}
                ],
                "confidence": 0.95
            }}

            Texts to analyze: {texts}"""

            # Log the prompt being sent
            logger.debug("Sending prompt to LLM for intent hierarchy generation:")
            logger.debug(f"User prompt: {prompt}")

            logger.info("Sending request to OpenRouter")
            completion = openai.ChatCompletion.create(
                headers={
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name,
                },
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7  # Added temperature for better response variety
            )

            response = completion.choices[0].message.content
            logger.info("Received response from OpenRouter")
            logger.debug(f"Response: {response}")

            return response

        except Exception as e:
            logger.error(f"Error generating intent hierarchy: {str(e)}")
            return None

    def generate_questions(self, content: str, num_questions: int = 5) -> List[str]:
        """Generate questions from content using DeepSeek model."""
        if not content.strip():
            logger.warning("Empty content provided to generate_questions")
            return []
            
        prompt = f"""Based on the following content, generate {num_questions} natural questions that users might ask.
        Make the questions diverse and cover different aspects of the content.
        Format the response as a JSON array of strings.

        Content:
        {content}

        Questions:"""

        # Log the prompt being sent
        logger.debug("Sending prompt to LLM for question generation:")
        logger.debug(f"System: 'You are a helpful assistant that generates natural user questions from content.'")
        logger.debug(f"User prompt: {prompt}")

        try:
            logger.debug(f"Making API call to OpenRouter with model: {self.model}")
            logger.debug(f"Content length: {len(content)} characters")
            
            completion = openai.ChatCompletion.create(
                headers={
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name,
                },
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates natural user questions from content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            logger.debug("Successfully received response from OpenRouter")
            # Parse the response to get questions
            questions = json.loads(completion.choices[0].message.content)
            logger.info(f"Generated {len(questions)} questions")
            return questions
            
        except Exception as e:
            logger.error(f"Unexpected error in generate_questions: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            return []
    
    def generate_responses(self, question: str, context: str) -> str:
        """Generate a response to a question using the provided context."""
        if not question.strip() or not context.strip():
            logger.warning("Empty question or context provided to generate_responses")
            return ""
            
        prompt = f"""Given the following context, provide a helpful and accurate response to the user's question.
        Keep the response concise and focused on the information provided in the context.

        Context:
        {context}

        Question: {question}

        Response:"""

        # Log the prompt being sent
        logger.debug("Sending prompt to LLM for response generation:")
        logger.debug(f"System: 'You are a helpful assistant that provides accurate responses based on given context.'")
        logger.debug(f"User prompt: {prompt}")

        try:
            logger.debug(f"Making API call to generate response for question: {question[:50]}...")
            completion = openai.ChatCompletion.create(
                headers={
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name,
                },
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides accurate responses based on given context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            logger.debug("Successfully generated response")
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            return ""
    
    def generate_paraphrases(self, text: str, num_variations: int = 3) -> List[str]:
        """Generate paraphrased variations of a text."""
        if not text.strip():
            logger.warning("Empty text provided to generate_paraphrases")
            return []
            
        prompt = f"""Generate {num_variations} different ways to ask the following question or express the following statement.
        Make each variation sound natural and conversational while maintaining the same meaning.
        Format the response as a JSON array of strings.

        Text: {text}

        Variations:"""

        # Log the prompt being sent
        logger.debug("Sending prompt to LLM for paraphrase generation:")
        logger.debug(f"System: 'You are a helpful assistant that generates natural paraphrases.'")
        logger.debug(f"User prompt: {prompt}")

        try:
            logger.debug(f"Making API call to generate paraphrases for text: {text[:50]}...")
            completion = openai.ChatCompletion.create(
                headers={
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name,
                },
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates natural paraphrases."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            logger.debug("Successfully generated paraphrases")
            variations = json.loads(completion.choices[0].message.content)
            logger.info(f"Generated {len(variations)} paraphrases")
            return variations
            
        except Exception as e:
            logger.error(f"Error generating paraphrases: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            return []

    def generate_intent_hierarchy(self, hierarchy_input: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a hierarchical structure of intents using the input data."""
        try:
            if not hierarchy_input or not isinstance(hierarchy_input, dict):
                logger.error("Invalid hierarchy input")
                return None

            intents = hierarchy_input.get('intents', [])
            if not intents:
                logger.error("No intents provided in hierarchy input")
                return None

            url_structure = hierarchy_input.get('url_structure', {})
            collisions = hierarchy_input.get('collisions', [])

            prompt = f"""Analyze the following intent data and create a hierarchical structure.
            
            URL Structure:
            {json.dumps(url_structure, indent=2)}
            
            Intents:
            {json.dumps(intents, indent=2)}
            
            Collisions:
            {json.dumps(collisions, indent=2)}

            Return a JSON object with this structure:
            {{
                "intents": {{
                    "category_name": [
                        {{
                            "primary_intent": "...",
                            "user_goals": ["..."],
                            "confidence_score": 0.95,
                            "page_title": "...",
                            "source_url": "..."
                        }}
                    ]
                }},
                "collisions": [
                    {{
                        "intent1": "...",
                        "intent2": "...",
                        "similarity": 0.95
                    }}
                ],
                "metadata": {{
                    "status": "success",
                    "message": "Successfully generated hierarchy"
                }}
            }}"""

            logger.info("Sending request to OpenRouter for hierarchy generation")
            completion = openai.ChatCompletion.create(
                headers={
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name,
                },
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at organizing and structuring content hierarchies."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            response = completion.choices[0].message.content
            logger.info("Received hierarchy generation response")
            
            try:
                hierarchy = json.loads(response)
                return hierarchy
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing hierarchy JSON: {str(e)}")
                return None

        except Exception as e:
            logger.error(f"Error generating intent hierarchy: {str(e)}")
            return None

    def analyze_contact_center_intents(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Advanced intent analysis for contact center transformation."""
        try:
            if not page_data:
                logger.error("Invalid page data for intent analysis")
                return None

            # Construct content from page data
            content = self._prepare_content_for_analysis(page_data)
            
            prompt = f"""You are an Intent Discovery Expert helping a contact center transformation team.

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

            logger.info("Sending request to OpenRouter for contact center intent analysis")
            completion = openai.ChatCompletion.create(
                headers={
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name,
                },
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert intent discovery analyst specializing in contact center transformation."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            response = completion.choices[0].message.content
            logger.info("Received contact center intent analysis")

            try:
                analysis = json.loads(response)
                return analysis
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing intent analysis JSON: {str(e)}")
                return None

        except Exception as e:
            logger.error(f"Error in contact center intent analysis: {str(e)}")
            return None

    def analyze_contact_center_intents(self, html_content: str) -> dict:
        """
        Specialized analysis for contact center transformation: returns a structured Intent Map
        following the user's detailed prompt.
        """
        try:
            if not html_content or not isinstance(html_content, str):
                logger.error("Invalid HTML content for contact center intent analysis")
                return None

            prompt = f"""
You are an Intent Discovery Expert helping a contact center transformation team.

You are given structured HTML content from a product website, including headers, paragraphs, titles, testimonials, and internal/external links.

Your goal is to analyze this content and return a structured \"Intent Map\" that captures what a user visiting this website may want to do.

**IMPORTANT: Your output must include a markdown table with the following columns:**
| Intent Name | User Goal | Sample Phrases | Source Context |

- For each intent, fill out all columns:
    - **Intent Name**: What the user wants to do (short phrase)
    - **User Goal**: A 1-sentence description of the user's goal for this intent
    - **Sample Phrases**: 2-3 example user utterances (in quotes, comma-separated)
    - **Source Context**: The section, header, or page context where this intent is found (e.g., "Pharmacy > Refills")

**Example:**
| Intent Name | User Goal | Sample Phrases | Source Context |
|-------------|----------|---------------|---------------|

**Rules:**
- Do **not** make up any information.
- Only use what is present in the content.
- If unsure, leave a cell blank.
- Respond only with the markdown table and any additional notes if needed.
- **Do NOT use or copy any information from the example table above. Only use information found in the Content section below.**

**Content:**
{html_content}
"""
            logger.info("Sending specialized contact center intent prompt to LLM...")
            logger.debug(f"Prompt sent to LLM:\n{prompt}")
            completion = openai.ChatCompletion.create(
                headers={
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.site_name,
                },
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an Intent Discovery Expert for contact center transformation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            response = completion.choices[0].message.content
            logger.info("Received Intent Map from LLM")
            return {"intent_map": response, "llm_prompt": prompt}
        except Exception as e:
            logger.error(f"Error in analyze_contact_center_intents: {str(e)}")
            return None

    def _prepare_content_for_analysis(self, page_data: Dict[str, Any]) -> str:
        """Prepare structured content for intent analysis."""
        try:
            sections = []
            
            # Add metadata
            metadata = page_data.get('metadata', {})
            if metadata:
                sections.append("== Page Metadata ==")
                sections.append(f"Title: {metadata.get('title', '')}")
                sections.append(f"Description: {metadata.get('description', '')}")
            
            # Add main content sections
            content = page_data.get('content', [])
            if content:
                sections.append("\n== Main Content ==")
                for item in content:
                    if isinstance(item, dict):
                        section_type = item.get('type', 'text')
                        text = item.get('text', '')
                        sections.append(f"[{section_type}] {text}")
            
            # Add navigation links
            navigation = page_data.get('navigation', {})
            if navigation:
                sections.append("\n== Navigation ==")
                if internal_links := navigation.get('internal_links', []):
                    sections.append("Internal Links:")
                    for link in internal_links:
                        sections.append(f"- {link}")
                if external_links := navigation.get('external_links', []):
                    sections.append("\nExternal Links:")
                    for link in external_links:
                        sections.append(f"- {link}")
            
            # Add any FAQs
            if faqs := page_data.get('faqs', []):
                sections.append("\n== FAQs ==")
                for faq in faqs:
                    sections.append(f"Q: {faq.get('question', '')}")
                    sections.append(f"A: {faq.get('answer', '')}\n")
            
            return "\n".join(sections)
            
        except Exception as e:
            logger.error(f"Error preparing content for analysis: {str(e)}")
            return ""
