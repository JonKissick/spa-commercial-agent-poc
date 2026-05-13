from openai import OpenAI, OpenAIError
from pydantic import ValidationError

from app.prompts import STAGE_1_SYSTEM_PROMPT, build_stage_1_user_prompt
from app.schemas import CommercialEvaluationResponse


class MissingAPIKeyError(RuntimeError):
    pass


class AIClientError(RuntimeError):
    pass


class AISchemaError(AIClientError):
    pass


class AIClient:
    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def analyze_contract_text(self, contract_text: str) -> CommercialEvaluationResponse:
        if not self.api_key:
            raise MissingAPIKeyError("OPENAI_API_KEY is not configured.")

        client = OpenAI(api_key=self.api_key)

        try:
            response = client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": STAGE_1_SYSTEM_PROMPT},
                    {"role": "user", "content": build_stage_1_user_prompt(contract_text)},
                ],
                text_format=CommercialEvaluationResponse,
            )
        except OpenAIError as exc:
            raise AIClientError("OpenAI analysis request failed.") from exc
        except ValidationError as exc:
            raise AISchemaError("OpenAI response did not match the commercial evaluation schema.") from exc
        except Exception as exc:
            raise AIClientError("OpenAI analysis could not be completed.") from exc

        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise AISchemaError("OpenAI response did not include a parsed structured output.")
        if not isinstance(parsed, CommercialEvaluationResponse):
            try:
                parsed = CommercialEvaluationResponse.model_validate(parsed)
            except ValidationError as exc:
                raise AISchemaError("OpenAI response did not match the commercial evaluation schema.") from exc

        return parsed
