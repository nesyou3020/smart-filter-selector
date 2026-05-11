import json
import logging
from typing import Any, Dict

from langchain.llms.ollama import Ollama
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import PromptTemplate

from app.config import config
from app.utils.token_count import count_tokens

logger = logging.getLogger(__name__)

class LLMService:
    """Service for LLM-based filter refinement using LangChain."""

    def __init__(self):
        self.llm = Ollama(
            base_url=config.OLLAMA_URL,
            model=config.OLLAMA_LLM_MODEL,
            temperature=0.15,
            num_gpu=1
        )
        self.setup_chain()

    def setup_chain(self):
        """Setup LangChain prompt and output parser."""
        response_schemas = [
            ResponseSchema(
                name="reducedFilters",
                description=(
                    "A list of dictionaries representing selected filters.\n"
                    "Structure:\n"
                    "[\n"
                    "  {\n"
                    "    \"name\": \"<filter name>\",\n"
                    "    \"category\": \"<category name>\",\n"
                    "    \"subcategory\": \"<subcategory name or empty string>\",\n"
                    "    \"score\": \"<score (0-1)>\",\n"
                    "  }, ...\n"
                    "]\n\n"
                    "Each dictionary contains the filter name, category, and subcategory.\n"
                    "For hierarchical categories (e.g., domain → speciality → tool), the subcategory field is populated accordingly."
                )
            ),
            ResponseSchema(
                name="confidence",
                description=(
                    "A dictionary mapping each category to an overall confidence score (0–1).\n"
                    "Structure:\n"
                    "{\n"
                    "  \"<category>\": <confidence score>,\n"
                    "  ...\n"
                    "}\n\n"
                    "The confidence score represents the LLM’s certainty about its chosen filters in that category."
                )
            ),
            ResponseSchema(
                name="reasoning",
                description=(
                    "A dictionary providing short, human-readable explanations for the LLM’s filter selections per category.\n"
                    "Structure:\n"
                    "{\n"
                    "  \"<category>\": \"<reasoning text>\",\n"
                    "  ...\n"
                    "}\n\n"
                    "This helps clarify why specific filters or subcategories were chosen."
                )
            )
        ]
        self.output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = self.output_parser.get_format_instructions()

        # Define prompt template
        template = """
You are an expert filter recommendation system for a Knowledge Management System.

User Query: "{query}"
Available filter candidates (top similar filters from embedding search):
{candidates}

Your task:
1. Analyze the user query and understand the intent.
2. From the candidates provided, select the MOST RELEVANT filters per category.
3. Provide confidence scores (0-1) for each category.
4. Explain your reasoning for each category.

STRICT RULES:
- {format_instructions}
- Return ONLY the JSON output, no extra text.
- You MUST NOT invent new categories or filters; Use only the exact filter names, categories that appear in the "Available filter candidates" list.
- Do not translate, rephrase, or rename candidate filters.
- Do not infer new categories unless they explicitly appear in the candidates.

IMPORTANT: 
- If a category is not listed under "Available filter candidates", do NOT include it in your output. 
- If no candidates are relevant, return an empty List for reducedFilters."""

        self.prompt = PromptTemplate(
            template=template,
            input_variables=["query", "candidates"],
            partial_variables={"format_instructions": format_instructions}
        )

        self.chain = self.prompt | self.llm | self.output_parser

    def refine_filters(self, query: str, candidates: Dict[str, Any], max_per_category: int) -> Dict[str, Any]:
        """
            Refine filter candidates using LLM.

            Args:
                query: User query
                candidates: Candidate filters from embedding search
                max_per_category: Maximum filters to return per category

            Returns:
                Refined filter selection with confidence and reasoning
        """
        # Format candidates for the prompt
        candidates_str = self._format_candidates(candidates, max_per_category)

        try:
            rendered_prompt = self.prompt.format(
                query=query,
                candidates=candidates_str
            )
            logger.info(f"📝 LLM Prompt Tokens:{count_tokens(rendered_prompt)}")
            # with open("./debug_prompt.txt", "w", encoding="utf-8") as f:
            #     f.write(rendered_prompt)

            # Run the chain
            result = self.chain.invoke({
                "query": query,
                "candidates": candidates_str
            })
            return result

        except Exception as e:
            logger.error(f"❌ LLM refinement error: {e}")
            return {
                'reducedFilters': [],
                'confidence': [],
                'reasoning': []
            }

    def _format_candidates(self, candidates: list[Dict[str, str]], max_per_category: int) -> str:
        """Format candidates for prompt."""
        return json.dumps(
            list(
                dict(
                    name=candidate['name'],
                    category=candidate['category'],
                    subcategory=candidate['subcategory']
                )
                for candidate in candidates
            ),
            indent=2, ensure_ascii=False
        )
