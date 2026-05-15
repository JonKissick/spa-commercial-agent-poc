import json
from typing import Any

from pydantic import ValidationError

from app.llm_providers.base import LLMProviderConfigurationError, LLMProviderError, LLMProviderSchemaError
from app.prompts import STAGE_1_SYSTEM_PROMPT, build_stage_1_user_prompt
from app.schemas import CommercialEvaluationResponse


class BedrockProvider:
    provider_name = "bedrock"

    def __init__(self, region_name: str | None, model_id: str | None) -> None:
        self.region_name = region_name
        self.model_id = model_id

    def analyze_contract(self, contract_text: str) -> CommercialEvaluationResponse:
        if not self.region_name:
            raise LLMProviderConfigurationError("AWS_REGION is not configured.")
        if not self.model_id:
            raise LLMProviderConfigurationError("BEDROCK_MODEL_ID is not configured.")

        try:
            import boto3
        except ImportError as exc:
            raise LLMProviderConfigurationError("boto3 is required for LLM_PROVIDER=bedrock.") from exc

        client = boto3.client("bedrock-runtime", region_name=self.region_name)
        prompt = self._build_json_prompt(contract_text)
        body = self._build_anthropic_body(prompt)

        try:
            response = client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            payload = json.loads(response["body"].read())
            content = self._extract_text(payload)
            return self._validate_payload(json.loads(content))
        except ValidationError as exc:
            raise LLMProviderSchemaError("Bedrock response did not match the commercial evaluation schema.") from exc
        except json.JSONDecodeError as exc:
            raise LLMProviderSchemaError("Bedrock response was not valid JSON.") from exc
        except Exception as exc:
            raise LLMProviderError("Bedrock analysis request failed.") from exc

    def _build_json_prompt(self, contract_text: str) -> str:
        schema = json.dumps(CommercialEvaluationResponse.model_json_schema(), indent=2)
        return (
            f"{STAGE_1_SYSTEM_PROMPT}\n\n"
            "Return only valid JSON matching this JSON schema. Do not wrap it in markdown.\n"
            f"JSON schema:\n{schema}\n\n"
            f"{build_stage_1_user_prompt(contract_text)}"
        )

    def _build_anthropic_body(self, prompt: str) -> dict[str, Any]:
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 12000,
            "temperature": 0,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        }

    def _extract_text(self, payload: dict[str, Any]) -> str:
        if "content" in payload and isinstance(payload["content"], list):
            parts = [part.get("text", "") for part in payload["content"] if isinstance(part, dict)]
            text = "".join(parts).strip()
            if text:
                return text
        if "output" in payload:
            return str(payload["output"])
        raise LLMProviderSchemaError("Bedrock response did not contain text content.")

    def _validate_payload(self, payload: Any) -> CommercialEvaluationResponse:
        if isinstance(payload, CommercialEvaluationResponse):
            return payload
        return CommercialEvaluationResponse.model_validate(payload)
