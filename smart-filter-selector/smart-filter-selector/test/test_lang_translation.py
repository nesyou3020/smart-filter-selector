import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.translation_service import TranslationService
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("lang-translation-test")

query_examples = [
    "Find tools for railway signaling experts.",          # English (Project-related)
    "Quels outils sont recommandés pour les projets ferroviaires?", # French (Project-related)
    "Find advanced-level tools for energy systems.",      # English (Project-related)
    "Quais são os melhores softwares para gestão de energia?" # Portuguese (Project-related)
]


trans_service = TranslationService()
for query in query_examples:
    result = trans_service.detect_and_translate(query)
    logger.info("\n" + "="*60)
    logger.info(f"🌐 Original Query: {result['originalQuery']}")
    logger.info(f"🌐 Detected Language: {result['detectedLanguage']}")
    logger.info(f"🌐 Translated Query: {result['translatedQuery']}")
    logger.info(f"🌐 Confidence: {result['confidence']}")
    logger.info(f"🌐 Is Translated: {result['isTranslated']}")