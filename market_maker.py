import asyncio
from typing import Optional
from dataclasses import dataclass
import time
from order_executor import OrderExecutor

@dataclass
class PendingOrder:
    order_id: str = ""
    side: str = ""
    price: float = 0.0
    quantity: float = 0.0
    placed_time: float = 0.0

class MarketMaker:
    def __init__(self, orderbook, symbol):
        self.symbol = symbol
        self.orderbook = orderbook
        self.order_executor = OrderExecutor("mx0vglIZOoLYMTFKD6", "f319935c8e2242beb14854c3d12a849f")
        self.current_buy: Optional[PendingOrder] = None
        self.current_sell: Optional[PendingOrder] = None
        self.lock = asyncio.Lock()
        self.tick_size = 0.00001
        self.order_quantity = 0.4

    async def on_orderbook_update(self):
        async with self.lock:
            if self.get_best_bid() == 0 or self.get_best_ask() == 0:
                return

            await self.check_current_buy_order()
            #await self.check_current_sell_order()
            await self.place_new_buy_order_if_needed()
            #await self.place_new_sell_order_if_needed()

    def get_best_bid(self):
        return self.orderbook.get_best_bid()

    def get_best_ask(self):
        return self.orderbook.get_best_ask()

    async def check_current_buy_order(self):
        if self.current_buy and self.current_buy.order_id:
            status = await self.order_executor.get_order_status(self.symbol, self.current_buy.order_id)
            if status.success:
                if status.status in ["FILLED", "CANCELED"]:
                    print(f"Buy order {self.current_buy.order_id} is {status.status}")
                    self.current_buy = None
                elif self.current_buy.price != self.get_best_bid():
                    print(f"Cancelling buy order: {self.current_buy.order_id}")
                    cancel_resp = await self.order_executor.cancel_order(self.symbol, self.current_buy.order_id)
                    if cancel_resp.success:
                        self.current_buy = None

    async def check_current_sell_order(self):
        if self.current_sell and self.current_sell.order_id:
            status = await self.order_executor.get_order_status(self.symbol, self.current_sell.order_id)
            if status.success:
                if status.status in ["FILLED", "CANCELED"]:
                    print(f"Sell order {self.current_sell.order_id} is {status.status}")
                    self.current_sell = None
                elif self.current_sell.price != self.get_best_ask():
                    print(f"Cancelling sell order: {self.current_sell.order_id}")
                    cancel_resp = await self.order_executor.cancel_order(self.symbol, self.current_sell.order_id)
                    if cancel_resp.success:
                        self.current_sell = None

    async def place_new_buy_order_if_needed(self):
        if not self.current_buy:
            buy_price = self.get_best_bid()
            resp = await self.order_executor.place_buy_limit_order(self.symbol, buy_price, self.order_quantity)
            if resp.success:
                self.current_buy = PendingOrder(
                    order_id=resp.order_id,
                    side="BUY",
                    price=buy_price,
                    quantity=self.order_quantity,
                    placed_time=time.time()
                )
                print(f"Placed buy order: {resp.order_id} @ {buy_price}")
            else:
                print(f"Failed to place buy order: {resp.error_message}")

    async def place_new_sell_order_if_needed(self):
        if not self.current_sell:
            sell_price = self.get_best_ask()
            resp = await self.order_executor.place_sell_limit_order(self.symbol, sell_price, self.order_quantity)
            if resp.success:
                self.current_sell = PendingOrder(
                    order_id=resp.order_id,
                    side="SELL",
                    price=sell_price,
                    quantity=self.order_quantity,
                    placed_time=time.time()
                )
                print(f"Placed sell order: {resp.order_id} @ {sell_price}")
            else:
                print(f"Failed to place sell order: {resp.error_message}")
