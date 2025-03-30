import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status

from backend_app.services.logging.logging_service import LoggerService
from backend_app.analyze_message.service import analyse_text_message

logger = LoggerService.get_logger()


@csrf_exempt
def text_message_analysis(request):

    if request.method != "POST":
        return JsonResponse(
            {"message": "Invalid Method"}, status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    try:
        body = json.loads(request.body)
        message = body.get("message")
        sender_name = body.get("from")

        if not message or not sender_name:
            logger.warning("Missing or empty data provided for analysis")
            return JsonResponse(
                {"message": "Invalid data provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(f"Starting AI analysis of the provided text message...")
        result = analyse_text_message(text=message, sender_name=sender_name)

        if not result.get("success", False):
            logger.warning(f"Failed to analyse the text message !")
            return JsonResponse(
                {"message": "Server error. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        logger.info(f"Text message successfully evaluated.")
        return JsonResponse(
            {"message": "Analysis successful", "result": result},
            status=status.HTTP_200_OK,
        )

    except json.JSONDecodeError:
        logger.error("Invalid JSON payload received for analysis")
        return JsonResponse(
            {"message": "Invalid request format"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.exception(f"Unexpected error during analysis")
        return JsonResponse(
            {"message": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
