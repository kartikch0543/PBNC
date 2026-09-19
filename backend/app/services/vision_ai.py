import base64
import json
import logging
import re
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


VISION_EXTRACTION_PROMPT = """
You are an expert examination paper parser. Analyze the provided document page image or text and extract all questions into a strict JSON object.

Rules:
1. Extract question numbers exactly as shown (e.g. "1", "Q.2", "3(a)"). If a question has NO numbering, set "question_number": null. DO NOT invent or hallucinate question numbers.
2. Separate question stem ("question_text") from options.
3. For multiple-choice questions, extract each option with its key ("A", "B", "C", "D" or "(a)", "(b)", etc.) and text.
4. If an answer or solution is indicated directly on the question or page, extract it in "detected_answer". Otherwise set "detected_answer": null.
5. Classify "question_type" into: "MULTIPLE_CHOICE", "MULTI_SELECT", "TRUE_FALSE", "SHORT_ANSWER", "ESSAY", or "UNKNOWN".
6. Note whether a diagram or table is part of the question in "has_diagram" (true/false).
7. If an Answer Key section appears on this page, extract the answer key mapping in "answer_key": {"1": "A", "2": "C"}.

Return ONLY a valid JSON object with this exact structure:
{
  "questions": [
    {
      "question_number": "1",
      "question_text": "What is the capital of France?",
      "question_type": "MULTIPLE_CHOICE",
      "options": [
        {"key": "A", "text": "Berlin"},
        {"key": "B", "text": "Paris"},
        {"key": "C", "text": "Madrid"},
        {"key": "D", "text": "Rome"}
      ],
      "detected_answer": "B",
      "has_diagram": false
    }
  ],
  "answer_key": {}
}
"""


class VisionAIService:
    """Invokes Google Gemini Multimodal Vision API when configured."""

    @classmethod
    def is_available(cls) -> bool:
        return bool(settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5)

    @classmethod
    async def extract_from_image(cls, image_bytes: bytes) -> Optional[Dict[str, Any]]:
        """Sends page image to Gemini 2.0 / 1.5 Flash for multimodal parsing."""
        if not cls.is_available():
            return None

        try:
            b64_data = base64.b64encode(image_bytes).decode("utf-8")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"

            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": VISION_EXTRACTION_PROMPT},
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": b64_data,
                                }
                            },
                        ]
                    }
                ],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.1,
                },
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    logger.warning(f"Gemini Vision API error {response.status_code}: {response.text}")
                    return None

                data = response.json()
                text_content = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_content)

        except Exception as ex:
            logger.error(f"Failed to execute Gemini Vision extraction: {ex}")
            return None


vision_ai_service = VisionAIService()
