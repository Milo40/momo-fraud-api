from django.urls import path

from backend_app.analyze_message.views import (
    text_message_analysis,
    discuss_text_message_view,
)

urlpatterns = [
    path("message_analysis", text_message_analysis, name="text_message_analysis"),
    path("discuss", discuss_text_message_view, name="discuss_text"),
]
