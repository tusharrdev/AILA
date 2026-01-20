import base64
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Message, CustomUser
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.receiver_id = self.scope['url_route']['kwargs']['receiver_id']
        self.user = self.scope["user"]
        ids = sorted([self.user.id, int(self.receiver_id)])
        self.room_name = f"chat_{ids[0]}_{ids[1]}"
        self.room_group_name = self.room_name

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_text = data.get('message', '').strip()
        file_data = data.get('file')
        file_name = data.get('file_name')

        file_obj = None

        if file_data and file_name:
            try:
                format, imgstr = file_data.split(';base64,')
                file_ext = file_name.split('.')[-1]
                decoded_file = base64.b64decode(imgstr)
                file_obj = ContentFile(decoded_file, name=f"{self.user.id}_{file_name}")
            except Exception as e:
                await self.send(text_data=json.dumps({'error': 'Invalid file format'}))
                return

        receiver = await sync_to_async(CustomUser.objects.get)(id=self.receiver_id)

        message = await sync_to_async(Message.objects.create)(
            sender=self.user,
            receiver=receiver,
            content=message_text,
            file=file_obj
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message.content,
                'file_url': message.file.url if message.file else '',
                'sender_id': message.sender.id,
                'timestamp': message.timestamp.strftime("%b %d, %H:%M")
            }
        )

        
        await self.channel_layer.group_send(
            f"user_list_{receiver.id}",
            {
                'type': 'user_list_update',
                'data': {
                    'action': 'new_message',
                    'sender_id': self.user.id,
                    'sender_name': self.user.full_name,
                    'sender_email': self.user.email,
                    'last_message': message_text[:50] + '...' if len(message_text) > 50 else message_text,
                    'timestamp': message.timestamp.strftime("%H:%M"),
                    'has_file': bool(file_obj)
                }
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'file_url': event['file_url'],
            'timestamp': event['timestamp'],
            'is_self': self.user.id == event['sender_id']
        }))

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class SlotConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.lawyer_id = self.scope['url_route']['kwargs']['lawyer_id']
        self.slots_group_name = f'slots_{self.lawyer_id}'

        
        await self.channel_layer.group_add(
            self.slots_group_name,
            self.channel_name
        )

        await self.accept()
        print(f"WebSocket connected for lawyer {self.lawyer_id}")

    async def disconnect(self, close_code):
        
        await self.channel_layer.group_discard(
            self.slots_group_name,
            self.channel_name
        )
        print(f"WebSocket disconnected for lawyer {self.lawyer_id}")

    async def receive(self, text_data):
        pass

    async def slot_update(self, event):
        data = event['data']

        await self.send(text_data=json.dumps(data))
        print(f"Sent slot update: {data}")

class UserListConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f"user_list_{self.user_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def user_list_update(self, event):
        await self.send(text_data=json.dumps(event['data']))
