import json
import logging
from time import perf_counter
from typing import Any, Dict

from app.config import config
from app.services.embedding_service import EmbeddingService
from app.services.level_detector import LevelDetector
from app.services.llm_service import LLMService
from app.services.translation_service import TranslationService

logger = logging.getLogger(__name__)

class HybridFilterSelector:
    """Hybrid approach combining embeddings and LLM for filter selection."""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()
        self.level_detector = LevelDetector()
        self.translation_service = TranslationService()

    def is_ready(self) -> bool:
        """Check if service is ready to process queries."""
        return self.embedding_service.is_loaded()

    def select_filters(self, query: str, max_filters: int = None, min_confidence: float = None) -> Dict[str, Any]:
        """
        Select filters using hybrid approach.

        Stage 0: Language detection & translation

        Stage 1: Embedding-based initial filtering (fast)
        Stage 2: LLM-based refinement (intelligent)
        Stage 3: Level detection (detect expertise/proficiency levels)

        Args:
            query: User query
            max_filters: Maximum filters per category
            min_confidence: Minimum confidence threshold

        Returns:
            Filter selection with confidence and reasoning
        """
        start_time = perf_counter()

        max_filters = max_filters or config.TOP_K_SIMILARITY
        min_confidence = min_confidence or config.MIN_CONFIDENCE_THRESHOLD
        logger.info(f"🔍 Received query: '{query}'")

        # Stage 0: Language detection & translation
        logger.info("🌐 Stage 0: Detecting language and translating if needed...")
        stage0_start = perf_counter()
        translation_result = self.translation_service.detect_and_translate(query)
        stage0_time = perf_counter() - stage0_start

        translated_query = translation_result.get("translatedQuery", query)
        detected_language = translation_result.get("detectedLanguage", "Unknown")
        is_translated = translation_result.get("isTranslated", False)
        translation_conf = translation_result.get("confidence", 0.0)

        logger.info(
            f"✅ Detected: {detected_language} | Translated: {is_translated} | "
            f"Confidence: {float(translation_conf):.2f} | Time: {stage0_time:.2f}s"
        )

        # Stage 1: Embedding-based filtering (get top 30 candidates)
        logger.info(f"📊 Stage 1: Embedding similarity search (top {config.TOP_K_SIMILARITY} candidates)...")
        stage1_start = perf_counter()
        candidates = self.embedding_service.find_similar_filters(translated_query)
        stage1_time = perf_counter() - stage1_start
        logger.info(f"   ✅ Found {len(candidates)} candidates in {stage1_time:.2f}s")

        # with open('./candidates_debug.json', 'w', encoding='utf-8') as f:
        #     json.dump(candidates, f, ensure_ascii=False, indent=2)

        if not candidates:
            return {
                'query': query,
                'translatedQuery': translated_query,
                'detectedLanguage': detected_language,
                'translationConfidence': translation_conf,
                'isTranslated': is_translated,
                'reducedFilters': {},
                'confidence': {},
                'reasoning': {'error': 'No embeddings loaded. Run generate_embeddings.py first.'},
                'processingTime': f"{perf_counter() - start_time:.2f}s"
            }

        # Stage 2: LLM-based refinement
        logger.info(f"🤖 Stage 2: LLM refinement ...")
        stage2_start = perf_counter()
        filtered_result = self.llm_service.refine_filters(translated_query, candidates, max_filters)
        stage2_time = perf_counter() - stage2_start
        logger.info(f"   ✅ Refined in {stage2_time:.2f}s")

        # Stage 3: Level detection
        logger.info(f"🎯 Stage 3: Detecting expertise/proficiency/language levels...")
        stage3_start = perf_counter()
        level_result = self.level_detector.detect_levels(translated_query)
        stage3_time = perf_counter() - stage3_start
        logger.info(f"✅ Levels detected in {stage3_time:.2f}s")

        # Apply confidence threshold
        # filtered_result = self._apply_confidence_threshold(filtered_result, min_confidence)

        # Calculate metrics
        total_time = perf_counter() - start_time

        result = {
            'originalQuery': query,
            'translatedQuery': translated_query,
            'detectedLanguage': detected_language,
            'translationConfidence': translation_conf,
            'isTranslated': is_translated,

            'reducedFilters': filtered_result['reducedFilters'],
            'embedding_search_candidates': candidates,
            'confidence': filtered_result['confidence'],
            'reasoning': filtered_result['reasoning'],

            'detectedLevels': level_result.get('detectedLevels', {}),
            'levelConfidence': level_result.get('confidence', {}),
            'levelReasoning': level_result.get('reasoning', {}),

            'processingTime': f"{total_time:.2f}s",
            'stages': {
                'translation': f"{stage0_time:.2f}s",
                'embedding_search': f"{stage1_time:.2f}s",
                'llm_refinement': f"{stage2_time:.2f}s",
                'level_detection': f"{stage3_time:.2f}s"
            }
        }
        logger.info(f"✅ Total processing time: {total_time:.2f}s")

        return result

    def _apply_confidence_threshold(self, result: Dict[str, Any], min_confidence: float) -> Dict[str, Any]:
        """Filter out categories with low confidence."""
        try:
            filtered_filters = {}
            filtered_confidence = {}
            filtered_reasoning = {}

            reduced_filters = result.get('reducedFilters', {})
            confidence = result.get('confidence', {})
            reasoning = result.get('reasoning', {})

            for category in reduced_filters:
                cat_confidence = confidence.get(category, 0.0)

                # Handle nested dicts for hierarchical categories
                if isinstance(cat_confidence, dict):
                    sub_filtered = {}
                    sub_confidence = {}
                    sub_reasoning = {}
                    for subcat, subcat_conf in cat_confidence.items():
                        try:
                            conf_val = float(subcat_conf)
                        except Exception:
                            conf_val = 0.0
                        if conf_val >= float(min_confidence):
                            # Only add subcategory if it passes threshold
                            if category in reduced_filters and isinstance(reduced_filters[category], dict):
                                sub_filtered[subcat] = reduced_filters[category].get(subcat, {})
                            sub_confidence[subcat] = conf_val
                            if category in reasoning and isinstance(reasoning[category], dict):
                                sub_reasoning[subcat] = reasoning[category].get(subcat, '')
                        else:
                            logger.warning(f"   ⚠️  Filtered out '{category}:{subcat}' (confidence {conf_val:.2f} < {min_confidence})")
                    if sub_filtered:
                        filtered_filters[category] = sub_filtered
                        filtered_confidence[category] = sub_confidence
                        filtered_reasoning[category] = sub_reasoning
                else:
                    try:
                        conf_val = float(cat_confidence)
                    except Exception:
                        conf_val = 0.0
                    if conf_val >= float(min_confidence):
                        filtered_filters[category] = reduced_filters[category]
                        filtered_confidence[category] = conf_val
                        filtered_reasoning[category] = reasoning.get(category, '')
                    else:
                        logger.warning(f"   ⚠️  Filtered out '{category}' (confidence {conf_val:.2f} < {min_confidence})")

            return {
                'reducedFilters': filtered_filters,
                'confidence': filtered_confidence,
                'reasoning': filtered_reasoning
            }
        except Exception as e:
            logger.error(f"❌ Error applying confidence threshold: {e}")
            logger.info("   ⚠️  Returning unfiltered results due to error.")
            logger.info(min_confidence)
            logger.info(confidence)
