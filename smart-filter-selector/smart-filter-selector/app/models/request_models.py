from typing import Optional

from pydantic import BaseModel, Field

from app.config import config


class FilterQueryOptions(BaseModel):
    maxFiltersPerCategory: Optional[int] = Field(
        default=config.TOP_K_SIMILARITY,
        description="Maximum number of filters to return per category"
    )
    minConfidence: Optional[float] = Field(
        default=config.MIN_CONFIDENCE_THRESHOLD,
        description="Minimum confidence threshold for filter selection"
    )

class FilterQueryRequest(BaseModel):
    query: str = Field(..., description="User's natural language query")
    options: Optional[FilterQueryOptions] = Field(
        default_factory=FilterQueryOptions,
        description="Query options"
    )