import json
import logging
import os
from typing import Any, Dict, List
import re

from langchain.llms.ollama import Ollama
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import PromptTemplate

from app.config import config
from app.utils.token_count import count_tokens

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LevelDetector:
    """Service for detecting expertise/proficiency levels from query."""

    def __init__(self):
        self.levels_data = self._load_levels()
        self.llm = Ollama(
            base_url=config.OLLAMA_URL,
            model=config.OLLAMA_LLM_MODEL,
            temperature=0.15,
            num_gpu=1
        )
        self.setup_chain()

    def _load_levels(self) -> Dict[str, List[str]]:
        """Load levels configuration."""
        levels_path = os.path.join('data', 'levels.json')
        try:
            with open(levels_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.info(f"⚠️  Could not load levels.json: {e}")
            return {
                "language-level": ["A1", "A2", "B1", "B2", "C1", "C2", "native"],
                "experience": ["Experts", "Seniors", "Confirmed", "Medium", "Juniors"],
                "tool-expertise": ["basic", "limited", "intermediate", "advanced", "expert"]
            }

    def setup_chain(self):
        """Setup LangChain prompt and output parser for level detection."""
        response_schemas = [
            ResponseSchema(
                name="detectedLevels",
                description=(
                    "A JSON object mapping each relevant category to one or more detected levels. "
                    "Categories include: 'experience', 'tool-expertise', and 'language-level'.\n"
                    "- 'experience' refers to overall professional seniority (e.g., Juniors, Confirmed, Seniors, Experts).\n"
                    "- 'tool-expertise' refers to mastery of tools, frameworks, or technologies "
                    "(e.g., basic, intermediate, advanced, expert).\n"
                    "- 'language-level' refers to linguistic fluency based on CEFR levels or equivalents\n"
                    "Each category value should be a list of the most probable level(s), even if only one is detected."
                )
            ),
            ResponseSchema(
                name="confidence",
                description=(
                    "A JSON object containing numeric confidence scores between 0.0 and 1.0 for each category detected "
                    "(same keys as in 'detectedLevels').\n"
                    "- Confidence reflects how certain the model is about its inference.\n"
                    "- Scores closer to 1.0 mean strong evidence; closer to 0.0 mean low certainty.\n"
                    "Only include scores for categories that appear in 'detectedLevels'."
                )
            ),
            ResponseSchema(
                name="reasoning",
                description=(
                    "A concise explanation (1–3 sentences) describing how the detected levels were inferred from the query.\n"
                    "Explain both explicit and implicit clues:\n"
                    "- Mention key words, phrases, or contextual hints that influenced the decision.\n"
                    "- If confidence is low, briefly explain the ambiguity or uncertainty.\n"
                    "Avoid generic statements; focus on reasoning grounded in the query content."
                )
            )
        ]

        self.output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
        format_instructions = self.output_parser.get_format_instructions()

        template = """
You are an advanced language model specialized in analyzing user job or task queries to infer their expertise and proficiency levels.

User Query:
"{query}"

Available Level Categories and Their Descriptions:
{levels}
---

### Your Task:
Analyze the query and determine the most likely levels for the following categories:
- **experience**: overall seniority or years of experience implied
- **tool-expertise**: mastery of specific tools, frameworks, or technologies
- **language-level**: linguistic fluency or proficiency (only if languages are explicitly mentioned)

For each relevant category:
1. Identify explicit or implicit indicators of skill level or experience.
2. Select the most appropriate level(s) based on semantic meaning and context.
3. Assign a confidence score between **0.0 and 1.0**, reflecting how certain your detection is.
4. Explain your reasoning briefly and logically.

---
### Detection Guidelines

When analyzing the query, do not rely only on keywords — reason about meaning and intent.
Use the following as **illustrative hints**, not strict rules.

- **Experience indicators (overall professional seniority):**
    Consider job titles, years of experience, and self-descriptions. For example:
    - Terms suggesting autonomy, leadership, or high specialization → higher levels (Confirmed, Senior, or Expert)
    - Words showing early-career or learning stages → lower levels (Junior or Medium)
    - If the query describes responsibilities or achievements requiring experience, infer a higher level even if not stated.

- **Tool expertise indicators (specific technical proficiency):**
    - Evaluate how confidently the user discusses tools or technologies.
    - Expressions of mastery, optimization, or customization suggest advanced or expert levels.
    - Routine or limited experience indicates intermediate.
    - Unfamiliarity or simple exposure implies basic or limited skill.

- **Language proficiency indicators:**
    - Only assign a language-level when a language is explicitly referenced.
    - Look for cues like “fluent”, “native”, “basic knowledge”, or standardized CEFR mentions (A1–C2).
    - Avoid assuming a language level unless the user clearly mentions it.

- **Inference rules:**
    - If explicit level clues are absent, infer logically from the role or context (e.g., “team lead” → Senior/Expert, “intern” → Junior).
    - Prioritize reasoning and contextual understanding over keyword similarity.
    - Do not assign a level if the evidence is ambiguous or insufficient.
---

### Output Format

Return **STRICTLY VALID JSON**, following this schema:

{format_instructions}

Important:
- Output must be a **single valid JSON object**.
- Do **not** include markdown, explanations, or extra text.
- Do **not** wrap the JSON in code blocks.
- Ensure all keys and strings use double quotes `"`.
- Ensure commas between all fields."""

        self.prompt = PromptTemplate(
            template=template,
            input_variables=["query", "levels"],
            partial_variables={"format_instructions": format_instructions}
        )

        self.chain = self.prompt | self.llm | self.output_parser

    def detect_levels(self, query: str) -> Dict[str, Any]:
        """
            Detect levels from user query.

            Args:
                query: User query

            Returns:
                Dictionary with detected levels, confidence, and reasoning
        """
        try:
            levels_str = json.dumps(self.levels_data, indent=2)
            rendered_prompt = self.prompt.format(
                query=query,
                levels=levels_str
            )
            logger.info(f"📝 LLM Prompt Tokens:{count_tokens(rendered_prompt)}")

            result = self.chain.invoke({
                "query": query,
                "levels": levels_str
            })

            return result

        except Exception as e:
            logger.info(f"⚠️  Level detection error: {e}")
            return {
                "detectedLevels": {},
                "confidence": {},
                "reasoning": {}
            }
