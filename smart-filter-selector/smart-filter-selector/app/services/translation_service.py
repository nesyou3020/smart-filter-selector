import logging
from typing import Dict

from deep_translator import GoogleTranslator
from langdetect import DetectorFactory, detect

from app.config import config

logger = logging.getLogger(__name__)

DetectorFactory.seed = 0

class TranslationService:
    """Service for detecting and translating non-English queries to English, without LLMs."""

    def __init__(self):
        self.translator = GoogleTranslator(source='auto', target='en')

    def detect_and_translate(self, query: str) -> Dict[str, any]:
        """Detect language and translate to English if needed."""
        try:
            lang = detect(query)
            is_translated = lang != 'en'

            translated_query = (
                self.translator.translate(query) if is_translated else query
            )

            return {
                "detectedLanguage": lang,
                "translatedQuery": translated_query,
                "originalQuery": query,
                "confidence": 1.0,  # langdetect doesn’t return confidence
                "isTranslated": is_translated
            }

        except Exception as e:
            logger.error(f"Translation error: {e}")
            return {
                "detectedLanguage": "Unknown",
                "translatedQuery": query,
                "originalQuery": query,
                "confidence": 0.0,
                "isTranslated": False
            }
