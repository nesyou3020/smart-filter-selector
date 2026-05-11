from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FilterResponse(BaseModel):
    originalQuery: str = Field(..., description="Original user query (in any language)")
    translatedQuery: Optional[str] = Field(default=None, description="Translated query in English (if translation was performed)")
    detectedLanguage: str = Field(..., description="Detected language of the query")
    isTranslated: bool = Field(..., description="Whether translation was performed")
    translationConfidence: float = Field(default=1.0, description="Confidence score for language detection")

    query: str = Field(..., description="Query used for processing (translated if needed)")
    reducedFilters: Dict[str, str] = Field(..., description="Reduced set of filters per category (keys: category, subcategory and score)")
    confidence: Dict[str, float] = Field(..., description="Confidence scores per category")
    reasoning: Dict[str, str] = Field(..., description="Reasoning for filter selections")

    detectedLevels: Dict[str, List[str]] = Field(default_factory=dict, description="Detected expertise/proficiency levels")
    levelConfidence: Dict[str, float] = Field(default_factory=dict, description="Confidence scores for detected levels")
    levelReasoning: Dict[str, str] = Field(default_factory=dict, description="Reasoning for level detection")

    processingTime: str = Field(..., description="Time taken to process the query")
    totalReduction: Optional[str] = Field(default=None, description="Percentage of filters reduced")

    stages: Optional[Dict[str, str]] = Field(default=None, description="Processing time per stage")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status")
    ollama_connected: bool = Field(..., description="Ollama connection status")
    embeddings_loaded: bool = Field(..., description="Embeddings loaded status")
