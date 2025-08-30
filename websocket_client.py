import json
import aiohttp
import websockets
import asyncio
from protogenerated.PushDataV3ApiWrapper_pb2 import PushDataV3ApiWrapper

class DeltaVersionStatus:
    Valid = 0
    Outdated = 1
    GapDetected = 2
    NotSequential = 3

class WebSocketClient:
    def __init__(self, symbol):
        self.symbol = symbol
        self.websocket = None
        self.current_version = 0
        self.needs_resync = False
        self.on_orderbook_update = None
        self.on_orderbook_snapshot = None

    async def connect(self):
        url = "wss://wbs-api.mexc.com/ws"
        self.websocket = await websockets.connect(url, ssl=True)
        print("WebSocket Connection established")

    async def send_subscription(self):
        sub_msg = {
            "method": "SUBSCRIPTION",
            "params": [f"spot@public.aggre.depth.v3.api.pb@10ms@{self.symbol}"]
        }
        msg = json.dumps(sub_msg)
        await self.websocket.send(msg)
        print("WebSocketClient subscribed to market stream:", msg)

    async def handle_received_data(self, message):
        if isinstance(message, bytes):
            await self.handle_binary_delta(message)

    def set_orderbook_update_callback(self, callback):
        self.on_orderbook_update = callback

    def set_orderbook_snapshot_callback(self, callback):
        self.on_orderbook_snapshot = callback

    def get_delta_version_status(self, from_version: int, to_version: int) -> int:
        if to_version < self.current_version:
            return DeltaVersionStatus.Outdated
        if from_version > self.current_version + 1:
            return DeltaVersionStatus.GapDetected
        if from_version != self.current_version + 1:
            return DeltaVersionStatus.NotSequential
        return DeltaVersionStatus.Valid

    async def run_loop(self):
        while True:
            if self.needs_resync:
                print("Resync needed")
                await self.get_order_book_snapshot()
            try:
                msg = await self.websocket.recv()
                await self.handle_received_data(msg)
            except websockets.exceptions.ConnectionClosed:
                await asyncio.sleep(1)
                await self.connect()
                await self.send_subscription()

    async def handle_binary_delta(self, message: bytes):
        if self.needs_resync:
            return

        data = PushDataV3ApiWrapper()
        if not data.ParseFromString(message):
            return

        if not data.HasField("publicAggreDepths"):
            return

        depth = data.publicAggreDepths
        from_version = int(depth.fromVersion)
        to_version = int(depth.toVersion)

        status = self.get_delta_version_status(from_version, to_version)
        if status in (DeltaVersionStatus.GapDetected, DeltaVersionStatus.NotSequential):
            print(f"Version gap detected: expected {self.current_version + 1}, got {from_version}")
            self.needs_resync = True
            return

        update = {"bids": [], "asks": []}
        for bid in depth.bids:
            update["bids"].append((float(bid.price), float(bid.quantity)))
        for ask in depth.asks:
            update["asks"].append((float(ask.price), float(ask.quantity)))

        if self.on_orderbook_update:
            await self.on_orderbook_update(update)

        self.current_version = to_version

    async def get_order_book_snapshot(self):
        url = f"https://api.mexc.com/api/v3/depth?symbol={self.symbol}&limit=10"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                snapshot_json = await resp.json()

        snapshot_data = {"bids": [], "asks": []}
        for bid in snapshot_json.get("bids", []):
            snapshot_data["bids"].append((float(bid[0]), float(bid[1])))
        for ask in snapshot_json.get("asks", []):
            snapshot_data["asks"].append((float(ask[0]), float(ask[1])))

        if self.on_orderbook_snapshot:
            await self.on_orderbook_snapshot(snapshot_data)

        self.current_version = snapshot_json.get("lastUpdateId", 0)
        self.needs_resync = False
