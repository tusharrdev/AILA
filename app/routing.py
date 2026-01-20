from django.urls import re_path
from . import consumers

# Add this line to your existing websocket_urlpatterns
websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<receiver_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/slots/(?P<lawyer_id>\d+)/$', consumers.SlotConsumer.as_asgi()),
    re_path(r'ws/user_list/(?P<user_id>\w+)/$', consumers.UserListConsumer.as_asgi())
]