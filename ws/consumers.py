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
        print("in connect")
        # Join room group
        print("joining")
        await self.channel_layer.group_add('notifications',self.channel_name)
        print("accepting")
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        print("wtf")
        await self.channel_layer.group_discard(
            self.group,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        try:
            j = json.loads(text_data)
            print("FIRE")
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