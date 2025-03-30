from django.urls import include, path

from backend_app.views import hello_view

urlpatterns = [
    path("", hello_view, name="hello"),
    path("api/text/", include("backend_app.analyze_message.urls")),
]
