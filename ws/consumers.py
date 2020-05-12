import json
import traceback

from channels.generic.websocket import AsyncWebsocketConsumer


def catch_exception(f):
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except StopConsumer:
            raise
        except Exception as e:
            print(traceback.format_exc().strip('\n'), '<--- from consumer')
            raise
    return wrapper



class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join room group
        await self.channel_layer.group_add('notifications',self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.group,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        try:
            j = json.loads(text_data)
            await self.channel_layer.group_send('mytest', j)
        except json.JSONDecodeError:
            print("Error JSON")


    async def notification(self, payload):
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        await self.send(text_data=payload)

    async def default_handler(self, payload):
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        await self.send(text_data=payload)

    async def new_match_stream(self, payload):
        return await self.default_handler(payload)

    async def stream_start(self, payload):
        return await self.default_handler(payload)

    async def stream_stop(self, payload):
        return await self.default_handler(payload)

    async def user_update(self, payload):
        return await self.default_handler(payload)