import asyncio
import json

import google.generativeai as genai

from shared import get_logger

from app.schemas.analyze import AnalyzeRequest, DecisionPayload
from app.utils.config import OrchestrationSettings


class GeminiDecisionService:
    def __init__(self, settings: OrchestrationSettings) -> None:
        self.settings = settings
        self.logger = get_logger(settings.service_name, "gemini")

    async def decide_action(
        self,
        request: AnalyzeRequest,
        analysis: dict,
        portfolio: dict,
        fallback: dict,
    ) -> dict:
        if not self.settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")

        prompt = self._build_prompt(request=request, analysis=analysis, portfolio=portfolio, fallback=fallback)
        response_text = await asyncio.to_thread(self._generate_response, prompt)
        decision = DecisionPayload.model_validate(self._parse_json(response_text))
        return {
            **decision.model_dump(),
            "decision_source": self.settings.gemini_model,
            "fallback_used": False,
        }

    def _generate_response(self, prompt: str) -> str:
        genai.configure(api_key=self.settings.gemini_api_key)
        model = genai.GenerativeModel(self.settings.gemini_model)
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.1,
                "response_mime_type": "application/json",
            },
        )
        return response.text

    def _build_prompt(self, request: AnalyzeRequest, analysis: dict, portfolio: dict, fallback: dict) -> str:
        return f"""
You are the decision engine for ForesightX.

Rules:
- Use only the signals provided below.
- Do not invent tools, data, market events, or portfolio facts.
- Return valid JSON only.
- Allowed actions: BUY, SELL, HOLD.
- If evidence is mixed or insufficient, choose HOLD.
- Reasons must be concise factual statements.

Input event:
{json.dumps(request.model_dump(), default=str)}

Signals:
{json.dumps(analysis, default=str)}

Portfolio:
{json.dumps(portfolio, default=str)}

Deterministic fallback suggestion:
{json.dumps(fallback, default=str)}

Required JSON schema:
{{
  "action": "BUY | SELL | HOLD",
  "confidence": 0.0,
  "reason": ["string", "string"]
}}
""".strip()

    @staticmethod
    def _parse_json(raw_text: str) -> dict:
        cleaned = raw_text.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(cleaned)
