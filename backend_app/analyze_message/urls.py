from django.urls import path

from backend_app.analyze_message.views import text_message_analysis

urlpatterns = [
    path("message_analysis", text_message_analysis, name="text_message_analysis"),
]
