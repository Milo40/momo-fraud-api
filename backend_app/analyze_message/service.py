import json
import uuid
from django.conf import settings
from pydantic import BaseModel, StringConstraints
from google import genai
from google.genai.types import GenerateContentConfig, Part, SafetySetting
from typing import Annotated, Dict, Any, List, Optional
from django.core.cache import cache

from backend_app.services.logging.logging_service import LoggerService


logger = LoggerService.get_logger()


class AnalysisOutput(BaseModel):
    probability: int
    description: Annotated[str, StringConstraints(max_length=100)]
    tags: List[str]
    long_description: str


class ConversationManager:
    # Cache timeout in seconds (30 minutes)
    CACHE_TIMEOUT = 1800

    @staticmethod
    def generate_user_id() -> str:
        """Generate a unique user ID for conversation tracking"""
        return str(uuid.uuid4())

    @staticmethod
    def get_conversation_key(user_id: str) -> str:
        """Generate a unique cache key for a user's conversation"""
        return f"conversation:{user_id}"

    @staticmethod
    def store_conversation(user_id: str, conversation_data: Dict[str, Any]) -> None:
        """Store or update conversation data in cache"""
        key = ConversationManager.get_conversation_key(user_id)
        cache.set(key, conversation_data, ConversationManager.CACHE_TIMEOUT)
        logger.info(f"Stored conversation for user {user_id}")

    @staticmethod
    def get_conversation(user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve conversation data from cache"""
        key = ConversationManager.get_conversation_key(user_id)
        conversation = cache.get(key)
        if conversation:
            cache.touch(key, ConversationManager.CACHE_TIMEOUT)
        return conversation

    @staticmethod
    def add_message_to_history(user_id: str, role: str, content: str) -> None:
        """Add a new message to the conversation history"""
        conversation = ConversationManager.get_conversation(user_id) or {
            "history": [],
            "analysis_result": None,
        }

        conversation["history"].append({"role": role, "content": content})

        ConversationManager.store_conversation(user_id, conversation)

    @staticmethod
    def store_analysis_result(user_id: str, analysis_result: Dict[str, Any]) -> None:
        """Store the initial analysis result"""
        conversation = ConversationManager.get_conversation(user_id) or {
            "history": [],
            "analysis_result": None,
        }

        conversation["analysis_result"] = analysis_result
        ConversationManager.store_conversation(user_id, conversation)


def analyse_text_message(text: str, sender_name: str) -> Dict[str, Any]:
    """Analyze a text message and store the conversation start"""
    try:
        # Generate a unique user ID for this conversation
        user_id = ConversationManager.generate_user_id()

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

        ConversationManager.add_message_to_history(user_id, "user", text)

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
            response_dict["user_id"] = user_id  # Add user_id to the response

            ConversationManager.store_analysis_result(user_id, response_dict)

            ConversationManager.add_message_to_history(
                user_id,
                "model",
                f"Analysis: {response_dict.get('description', '')}. {response_dict.get('long_description', '')}",
            )

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


def discuss_text_message(follow_up_question: str, user_id: str) -> Dict[str, Any]:
    """Continue the discussion about a previously analyzed message"""
    try:

        conversation = ConversationManager.get_conversation(user_id)

        if not conversation:
            return {
                "answer": "No previous conversation found. Please analyze a message first.",
                "success": False,
            }

        ConversationManager.add_message_to_history(user_id, "user", follow_up_question)

        conversation_history = conversation["history"]
        analysis_result = conversation["analysis_result"]

        client = genai.Client(
            vertexai=True,
            project=settings.GOOGLE_PROJECT_ID,
            location=settings.GOOGLE_PROJECT_REGION,
        )

        context = f"""
        Previous message analysis:
        - Probability: {analysis_result.get('probability')}
        - Description: {analysis_result.get('description')}
        - Tags: {', '.join(analysis_result.get('tags', []))}
        - Long description: {analysis_result.get('long_description')}
        
        The user is now asking: {follow_up_question}
        
        Please respond to their follow-up question taking into account the previous analysis.
        """

        messages = []
        for msg in conversation_history:
            messages.append({"role": msg["role"], "parts": [{"text": msg["content"]}]})

        messages.insert(0, {"role": "model", "parts": [{"text": context}]})

        response = client.models.generate_content(
            model=settings.GOOGLE_VERTEX_AI_MODEL_ID,
            contents=messages,
            config=GenerateContentConfig(
                max_output_tokens=512,
                temperature=0.7,
                top_p=0.95,
                top_k=40,
            ),
        )

        response_text = response.text.strip()

        ConversationManager.add_message_to_history(user_id, "model", response_text)

        return {
            "answer": response_text,
            "success": True,
            "user_id": user_id,
        }

    except Exception as e:
        logger.error(f"Discussion operation failed. The issue was: {e}")
        return {
            "answer": "Failed to process your question. Please try again later.",
            "success": False,
        }
