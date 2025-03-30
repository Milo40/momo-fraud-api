from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from backend_app.services.logging.logging_service import LoggerService
from rest_framework import status

logger = LoggerService.get_logger()


@csrf_exempt
def hello_view(request):
    logger.info("Open access endpoint accessed.")
    return JsonResponse(
        {
            "message": "Yello there !",
            "description": "Seems like you reached the 'MTNC MoMo Fraud Detection' API.",
        },
        status=status.HTTP_200_OK,
    )


def not_found_view(request):
    logger.info(f"A non existent route has been requested.")
    return JsonResponse(
        {
            "message": "Not Found",
            "description": "The requested resource was not found on this server",
        },
        status=status.HTTP_404_NOT_FOUND,
    )
