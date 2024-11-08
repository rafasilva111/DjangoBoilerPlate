from .consumers import LogConsumer

from django.urls import path

websocket_urlpatterns = [
    path('ws/task/<int:task_id>/', LogConsumer.as_asgi()),  # Path pattern with <int:task_id>
]