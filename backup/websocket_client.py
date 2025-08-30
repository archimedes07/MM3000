import json
import websockets
from protogenerated.PushDataV3ApiWrapper_pb2 import PushDataV3ApiWrapper

class WebSocketClient:
    def __init__(self, symbol):
        self.symbol = symbol
        self.websocket = None

    async def connect(self):
        url = "wss://wbs-api.mexc.com/ws"
        try:
            self.websocket = await websockets.connect(url, ssl=True)
            print("Connection established")
            return True
        except Exception as e:
            print("Failed to connect:", e)
            self.websocket = None
            return False

    async def send_subscription(self):
        if not self.websocket:
            print("Subscription failed: No active websocket connection")
            return

        sub_msg = {
            "method": "SUBSCRIPTION",
            "params": [f"spot@public.aggre.depth.v3.api.pb@10ms@{self.symbol}"]
        }
        msg = json.dumps(sub_msg)

        try:
            await self.websocket.send(msg)
            print("Subscribed:", msg)
        except Exception as e:
            print("Failed to send subscription:", e)

    async def listen(self):
        if not self.websocket:
            print("No websocket to listen on")
            return
        try:
            async for msg in self.websocket:
                print("Received:", msg)
        except websockets.exceptions.ConnectionClosedOK:
            print("WebSocket closed normally")
        except websockets.exceptions.ConnectionClosedError as e:
            print("WebSocket closed with error:", e)
        except Exception as e:
            print("Error in listen loop:", e)
        finally:
            if self.websocket:
                await self.websocket.close()
