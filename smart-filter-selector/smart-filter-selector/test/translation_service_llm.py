import logging
import re
import unicodedata
from typing import Dict

from langchain.llms.ollama import Ollama
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import PromptTemplate
from langdetect import DetectorFactory, detect

from app.config import config

DetectorFactory.seed = 0

logger = logging.getLogger(__name__)

class TranslationService:
    """Service for detecting and translating non-English queries to English."""

    def __init__(self):
        self.llm = Ollama(
            base_url=config.OLLAMA_URL,
            model=config.OLLAMA_LLM_MODEL,
            temperature=0.1,
            num_gpu=1
        )
        self.setup_chain()

    def setup_chain(self):
        """Setup LangChain prompt and output parser for translation."""

        response_schemas = [
            ResponseSchema(
                name="detectedLanguage",
                description="The detected language of the input query (e.g., 'French', 'Spanish', 'English')"
            ),
            ResponseSchema(
                name="translatedQuery",
                description="The query translated to English. If already English, return the original query."
            ),
            ResponseSchema(
                name="confidence",
                description="Confidence score (0-1) for the language detection"
            ),
            ResponseSchema(
                name="isTranslated",
                description="Boolean indicating if translation was performed (true/false)"
            ),
        ]

        self.output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = self.output_parser.get_format_instructions()

        template = """
        You are an expert language detection and translation system.

        User Query: "{query}"

        Your task:
        1. Detect the language of the query.
        2. If the query is NOT in English, translate it to English.
        3. If the query is already in English, return it as-is.
        4. Preserve technical terms, acronyms, and proper nouns (e.g., ERTMS, SCADE, MATLAB).
        5. Maintain the original meaning and context.

        Rules:
        - Preserve technical terms and acronyms exactly as written.
        - Translate only natural language parts.
        - If unsure, assume English and return the original.
        - Mixed-language queries → translate non-English parts only.

        {format_instructions}

        Return ONLY the JSON output.
        """

        self.prompt = PromptTemplate(
            template=template,
            input_variables=["query"],
            partial_variables={"format_instructions": format_instructions}
        )

        self.chain = self.prompt | self.llm | self.output_parser

    def detect_and_translate(self, query: str) -> Dict[str, any]:
        """
        Detect language and translate query to English if needed.
        """
        if self._is_likely_english(query):
            return {
                'detectedLanguage': 'English',
                'translatedQuery': query,
                'originalQuery': query,
                'confidence': 1.0,
                'isTranslated': False
            }

        try:
            result = self.chain.invoke({"query": query})
            result['originalQuery'] = query
            return result
        except Exception as e:
            logger.error(f"⚠️ Translation error: {e}")
            return {
                'detectedLanguage': 'Unknown',
                'translatedQuery': query,
                'originalQuery': query,
                'confidence': 0.0,
                'isTranslated': False
            }

    def _is_likely_english(self, query: str) -> bool:
        try:
            lang = detect(query)
            if lang == "en":
                return True
            else:
                return False
        except:
            return False
