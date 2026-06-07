import json
import logging
from typing import Any

from asgiref.sync import async_to_sync

from documents.models import Document

from chat.services.llm.service import LLMService
from chat.services.llm.builders.prompt_builder import PromptBuilder

from .constants import (
    DEFAULT_MODEL_NAME,
    MAX_DOCUMENT_TEXT_LENGTH,
)

from .exceptions import DocumentAnalysisError

from .prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


class DocumentAnalysisService:
    """
    Domain service responsible only for AI analysis.

    Responsibilities:
    - Extract document text
    - Generate summary + tags
    - Return structured result

    Does NOT:
    - Fetch documents
    - Update DB state
    - Manage processing lifecycle
    """

    def __init__(self):
        self.llm_service = LLMService()
        self.prompt_builder = PromptBuilder()

    def analyze(
        self,
        document: Document,
    ) -> dict[str, Any]:
        """
        Analyze a document and return structured metadata.

        Raises:
            DocumentAnalysisError
        """

        try:
            document_text = self._extract_text(document)

            if not document_text:
                raise DocumentAnalysisError("Document extracted text is empty.")

            llm_response = self._generate_analysis(document_text=document_text)

            parsed_response = self._parse_response(llm_response)

            summary = parsed_response.get("summary", "").strip()

            tags = self._normalize_tags(parsed_response.get("tags", []))

            return {
                "summary": summary,
                "tags": tags,
            }

        except Exception as e:

            logger.exception(
                "document_analysis_failed",
                extra={
                    "document_id": str(document.id),
                },
            )

            raise DocumentAnalysisError(str(e)) from e

    def _extract_text(
        self,
        document: Document,
    ) -> str:

        extracted_text = document.extracted_text or {}

        text = extracted_text.get("text", "")

        return text.strip()

    def _generate_analysis(
        self,
        document_text: str,
    ):

        truncated_text = document_text[:MAX_DOCUMENT_TEXT_LENGTH]

        user_prompt = USER_PROMPT_TEMPLATE.format(document_text=truncated_text)

        messages = self.prompt_builder.build(
            system_prompt=SYSTEM_PROMPT,
            history=[],
            user_message=user_prompt,
        )

        return async_to_sync(self.llm_service.generate)(
            model_name=DEFAULT_MODEL_NAME,
            messages=messages,
        )

    def _parse_response(
        self,
        response,
    ) -> dict:

        try:

            content = response.content

            if isinstance(content, dict):
                return content

            if not isinstance(content, str):
                raise DocumentAnalysisError("LLM response content is invalid.")

            return json.loads(content)

        except json.JSONDecodeError as e:

            raise DocumentAnalysisError("Invalid JSON returned from LLM.") from e

    def _normalize_tags(
        self,
        tags: list,
    ) -> list[str]:

        if not isinstance(tags, list):
            return []

        normalized_tags = []

        for tag in tags:

            if not isinstance(tag, str):
                continue

            cleaned = tag.strip().lower()

            if not cleaned:
                continue

            if cleaned not in normalized_tags:
                normalized_tags.append(cleaned)

        return normalized_tags[:15]
