import json
from typing import Any

from openai import OpenAI, OpenAIError
from pydantic import ValidationError

from app.llm_providers.base import LLMProviderConfigurationError, LLMProviderError, LLMProviderSchemaError
from app.prompts import STAGE_1_SYSTEM_PROMPT, build_stage_1_user_prompt
from app.schemas import CommercialEvaluationResponse


class OpenAIProvider:
    provider_name = "openai"

    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def analyze_contract(self, contract_text: str) -> CommercialEvaluationResponse:
        if not self.api_key:
            raise LLMProviderConfigurationError("OPENAI_API_KEY is not configured.")

        client = OpenAI(api_key=self.api_key)
        try:
            if hasattr(client.responses, "parse"):
                return self._analyze_with_responses_parse(client, contract_text)
            return self._analyze_with_chat_json_schema(client, contract_text)
        except OpenAIError as exc:
            raise LLMProviderError("OpenAI analysis request failed.") from exc
        except ValidationError as exc:
            raise LLMProviderSchemaError("OpenAI response did not match the commercial evaluation schema.") from exc
        except json.JSONDecodeError as exc:
            raise LLMProviderSchemaError("OpenAI response was not valid JSON.") from exc

    def _analyze_with_responses_parse(self, client: OpenAI, contract_text: str) -> CommercialEvaluationResponse:
        response = client.responses.parse(
            model=self.model,
            input=[
                {"role": "system", "content": STAGE_1_SYSTEM_PROMPT},
                {"role": "user", "content": build_stage_1_user_prompt(contract_text)},
            ],
            text_format=CommercialEvaluationResponse,
        )
        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise LLMProviderSchemaError("OpenAI response did not include a parsed structured output.")
        return self._validate_payload(parsed)

    def _analyze_with_chat_json_schema(self, client: OpenAI, contract_text: str) -> CommercialEvaluationResponse:
        schema = CommercialEvaluationResponse.model_json_schema()
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": STAGE_1_SYSTEM_PROMPT},
                {"role": "user", "content": build_stage_1_user_prompt(contract_text)},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "commercial_evaluation_response",
                    "schema": schema,
                    "strict": False,
                },
            },
        )
        content = response.choices[0].message.content
        if not content:
            raise LLMProviderSchemaError("OpenAI response was empty.")
        return self._validate_payload(json.loads(content))

    def _validate_payload(self, payload: Any) -> CommercialEvaluationResponse:
        if isinstance(payload, CommercialEvaluationResponse):
            return payload
        return CommercialEvaluationResponse.model_validate(payload)
