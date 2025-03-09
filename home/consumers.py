import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Message, BuyRequest
from datetime import datetime
import logging
from .utils import verify_chat_hash

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    @database_sync_to_async
    def get_buy_request_from_hash(self, chat_hash):
        # Try all active buy requests until we find a match
        buy_requests = BuyRequest.objects.select_related('buyer', 'listing__seller').all()
        for buy_request in buy_requests:
            if verify_chat_hash(chat_hash, buy_request.id):
                return buy_request
        return None

    async def connect(self):
        try:
            # Log the user information
            logger.info(f"Connection attempt from user: {self.scope.get('user', 'No user')}")
            logger.info(f"Authentication status: {self.scope['user'].is_authenticated if 'user' in self.scope else 'No user in scope'}")

            # Get the user from scope
            if not self.scope["user"].is_authenticated:
                logger.error("User not authenticated")
                await self.close(code=4001)
                return

            self.room_id = self.scope['url_route']['kwargs']['room_id']
            self.room_group_name = f'chat_{self.room_id}'
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            logger.info(f"Successfully connected to room: {self.room_group_name}")
            
        except Exception as e:
            logger.error(f"Error in connect: {str(e)}")
            await self.close(code=4000)
            return

    async def disconnect(self, close_code):
        try:
            # Check if room_group_name exists before trying to use it
            if hasattr(self, 'room_group_name'):
                # Leave room group
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
                logger.info(f"Disconnected from room: {self.room_group_name} with code {close_code}")
            else:
                logger.info(f"Disconnected before room_group_name was set. Code: {close_code}")
        except Exception as e:
            logger.error(f"Error in disconnect: {str(e)}")

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': self.scope["user"].username,
            }
        )

    async def chat_message(self, event):
        message = event['message']
        user = event['user']
        
        await self.send(text_data=json.dumps({
            'message': message,
            'user': user,
            'timestamp': datetime.now().isoformat()
        }))

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
        buy_request = BuyRequest.objects.get(id=self.room_id)
        
        Message.objects.create(
            sender=sender,
            receiver=receiver,
            buy_request=buy_request,
            content=content
        ) 