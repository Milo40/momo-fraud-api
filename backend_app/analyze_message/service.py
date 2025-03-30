import json
from django.conf import settings
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from google import genai
from google.genai.types import GenerateContentConfig, Part, SafetySetting
from typing import Annotated, List
from pydantic import BaseModel, StringConstraints

from backend_app.services.logging.logging_service import LoggerService

logger = LoggerService.get_logger()


class AnalysisOutput(BaseModel):
    probability: int
    description: Annotated[str, StringConstraints(max_length=100)]
    tags: List[str]


def analyse_text_message(text: str, sender_name: None):
    try:
        client = genai.Client(
            vertexai=True,
            project=settings.GOOGLE_PROJECT_ID,
            location=settings.GOOGLE_PROJECT_REGION,
        )

        prompt = (
            str(settings.GOOGLE_PROMPT_TEXT)
            .replace("SENDER_NAME", sender_name)
            .replace("TEXT_CONTENT", text)
        )

        response = client.models.generate_content(
            model=settings.GOOGLE_VERTEX_AI_MODEL_ID,
            contents=prompt,
            config=GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AnalysisOutput,
                max_output_tokens=256,
                temperature=0.7,
                top_p=1,
                top_k=20,
            ),
        )

        raw_response = response.text.strip()
        logger.info(f"Raw Gemini Response: {raw_response}")

        try:
            response_dict = json.loads(raw_response)
            response_dict["success"] = True

            return response_dict

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing response as JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Error parsing response as AnalysisOutput: {e}")
            raise

    except json.JSONDecodeError as e:
        logger.error(f"Error decoding response from Vertex AI as JSON: {e}")
        return {
            "probability": None,
            "reason": "Failed to evaluate the message due to an unexpected response format. Please try again later.",
            "success": False,
        }
    except Exception as e:
        logger.error(f"Analysis operation failed. The issue was: {e}")
        return {
            "probability": None,
            "reason": "Failed to evaluate the message. Please try again later.",
            "success": False,
        }
