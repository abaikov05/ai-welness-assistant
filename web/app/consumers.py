import json

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'You are connected!'
        }))
        

    # async def disconnect(self):
    #     # Handle WebSocket disconnection logic here
    #     await self.disconnect()
    #     pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        user_message = text_data_json['message']
        
        await self.send(text_data=json.dumps({
            'type':'user_message',
            'user_message': user_message
        }))
