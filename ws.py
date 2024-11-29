import json
from fastapi import WebSocket
from android import AndroidDeviceHandler
from session import AppiumSessionHandler

appium_handler = AppiumSessionHandler()
appium_handler.start_session()

class WebSocketHandler:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.device_handler = AndroidDeviceHandler()
        self.appium_handler = appium_handler

    async def connect(self):
        await self.websocket.accept()

    async def disconnect(self):
        try:
            await self.websocket.close()
        except Exception as e:
            return None

    async def receive_message(self):
        try:
            data = await self.websocket.receive_text()
            return data
        except Exception as e:
            return None

    async def send_message(self, message: dict):
        try:
            await self.websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Error sending message: {e}")

    async def handle_message(self, message: str):
        json_message = json.loads(message)
        type = json_message['type']
        info = dict(type='code', code='')
        if type == 'resolution':
            info['type'] = 'resolution'
            info['resolution'] = await self.handle_resolution()
        elif type == 'back':
            info['code'] = await self.handle_back()
        elif type == 'clear':
            info['code'] = await self.handle_clear(json_message['x'], json_message['y'])
        elif type == 'hideKeyboard':
            info['code'] = await self.handle_hide_keyboard()
        elif type == 'lock':
            info['code'] = await self.handle_lock()
        elif type == 'unlock':
            info['code'] = await self.handle_unlock()
        elif type == 'background':
            info['code'] = await self.handle_background()
        elif type == 'notification':
            info['code'] = await self.handle_notification()
        elif type == 'click':
            info['code'] = self.appium_handler.click(x=json_message['x'], y=json_message['y'], prompt=json_message['prompt'])
        elif type == 'type':
            info['code'] = self.appium_handler.type(json_message['text'])
        elif type == 'assert':
            print("assert", json_message)
            self.appium_handler.handle_assert(prompt=json_message['prompt'], assert_result=json_message['assert_result'])
        else:
            return None
        
        await self.send_message(info)

    async def handle_resolution(self):
        resolution = self.device_handler.get_resolution()
        await self.send_message({ 'type': 'code', 'code': self.appium_handler.get_base_code() })
        return resolution

    async def handle_back(self):
        return self.appium_handler.go_back()

    async def handle_clear(self, x: int, y: int):
        return self.appium_handler.clear(x, y)

    async def handle_hide_keyboard(self):
        return self.appium_handler.hide_keyboard()

    async def handle_lock(self):
        return self.appium_handler.lock()

    async def handle_unlock(self):
        return self.appium_handler.unlock()

    async def handle_background(self):
        return self.appium_handler.background_app()

    async def handle_notification(self):
        return self.appium_handler.open_notifications()

