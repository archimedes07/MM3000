import asyncio
from typing import Optional
from dataclasses import dataclass
import time
from order_executor import OrderExecutor
from pnl_tracker import PnLTracker

@dataclass
class PendingOrder:
    order_id: str = ""
    side: str = ""
    price: float = 0.0
    quantity: float = 0.0
    placed_time: float = 0.0
    is_pending: bool = False

class MarketMaker:
    def __init__(self, orderbook, symbol):
        self.symbol = symbol
        self.orderbook = orderbook
        self.order_executor = OrderExecutor("mx0vglIZOoLYMTFKD6", "f319935c8e2242beb14854c3d12a849f")
        self.current_buy: Optional[PendingOrder] = None
        self.current_sell: Optional[PendingOrder] = None
        self.buy_lock = asyncio.Lock()
        self.sell_lock = asyncio.Lock()
        self.tick_size = 0.000001
        self.order_quantity = 0.4
        self.pnl_tracker = PnLTracker()
        self.last_pnl_print = time.time()

    async def on_orderbook_update(self):
        if self.get_best_bid() == 0 or self.get_best_ask() == 0:
            return

        asyncio.create_task(self.handle_buy())
        asyncio.create_task(self.handle_sell())
        
        # Print PnL stats every 30 seconds
        if time.time() - self.last_pnl_print > 30:
            mid_price = (self.get_best_bid() + self.get_best_ask()) / 2
            self.pnl_tracker.print_stats(mid_price)
            self.last_pnl_print = time.time()

    async def handle_buy(self):
        async with self.buy_lock:
            await self.check_current_buy_order()
            await self.place_new_buy_order_if_needed()

    async def handle_sell(self):
        async with self.sell_lock:
            await self.check_current_sell_order()
            await self.place_new_sell_order_if_needed()

    def get_best_bid(self):
        return self.orderbook.get_best_bid()

    def get_best_ask(self):
        return self.orderbook.get_best_ask()

    def is_only_one_at_current_bid_level(self):
        if not self.current_buy:
            return False
        return self.orderbook.get_bid_quantity(self.current_buy.price) == self.current_buy.quantity

    def is_only_one_at_current_ask_level(self):
        if not self.current_sell:
            return False
        return self.orderbook.get_bid_quantity(self.current_sell.price) == self.current_sell.quantity

    def should_cancel_current_buy(self):
        distance_to_second_bid = round(self.get_best_bid() - self.orderbook.get_second_best_bid(), 6)
        if self.is_only_one_at_current_bid_level() and distance_to_second_bid > self.tick_size:
            return True
        return self.current_buy.price != self.get_best_bid()

    def should_cancel_current_sell(self):
        distance_to_second_ask = round(self.orderbook.get_second_best_ask() - self.get_best_ask(), 6)
        if self.is_only_one_at_current_ask_level() and distance_to_second_ask > self.tick_size:
            return True
        return self.current_sell.price != self.get_best_ask()

    async def check_current_buy_order(self):
        if self.current_buy and self.current_buy.order_id and not self.current_buy.is_pending:
            status = await self.order_executor.get_order_status(self.symbol, self.current_buy.order_id)
            if status.success:
                if status.status in ["FILLED", "CANCELED"]:
                    print(f"Buy order {self.current_buy.order_id} is {status.status}")
                    if status.status == "FILLED":
                        # Record the trade in PnL tracker
                        self.pnl_tracker.add_trade(
                            self.current_buy.order_id,
                            "BUY",
                            self.current_buy.price,
                            self.current_buy.quantity
                        )
                    self.current_buy = None
                elif self.should_cancel_current_buy():
                    print(f"Cancelling buy order: {self.current_buy.order_id}")
                    self.current_buy.is_pending = True  # Mark as pending BEFORE cancel
                    cancel_resp = await self.order_executor.cancel_order(self.symbol, self.current_buy.order_id)
                    if cancel_resp.success:
                        self.current_buy = None
                    else:
                        self.current_buy.is_pending = False  # Reset if cancel failed

    async def check_current_sell_order(self):
        if self.current_sell and self.current_sell.order_id and not self.current_sell.is_pending:
            status = await self.order_executor.get_order_status(self.symbol, self.current_sell.order_id)
            if status.success:
                if status.status in ["FILLED", "CANCELED"]:
                    print(f"Sell order {self.current_sell.order_id} is {status.status}")
                    if status.status == "FILLED":
                        # Record the trade in PnL tracker
                        self.pnl_tracker.add_trade(
                            self.current_sell.order_id,
                            "SELL",
                            self.current_sell.price,
                            self.current_sell.quantity
                        )
                    self.current_sell = None
                elif self.should_cancel_current_sell():
                    print(f"Cancelling sell order: {self.current_sell.order_id}")
                    self.current_sell.is_pending = True  # Mark as pending BEFORE cancel
                    cancel_resp = await self.order_executor.cancel_order(self.symbol, self.current_sell.order_id)
                    if cancel_resp.success:
                        self.current_sell = None
                    else:
                        self.current_sell.is_pending = False  # Reset if cancel failed

    async def place_new_buy_order_if_needed(self):
        if not self.current_buy or (self.current_buy and not self.current_buy.order_id and not self.current_buy.is_pending):
            buy_price = self.get_best_bid()

            self.current_buy = PendingOrder(
                side="BUY",
                price=buy_price,
                quantity=self.order_quantity,
                placed_time=time.time(),
                is_pending=True
            )

            resp = await self.order_executor.place_buy_limit_order(self.symbol, buy_price, self.order_quantity)

            if resp.success:
                self.current_buy.order_id = resp.order_id
                self.current_buy.is_pending = False  # No longer pending
                print(f"Placed buy order: {resp.order_id} @ {buy_price}")
            else:
                print(f"Failed to place buy order: {resp.error_message}")
                self.current_buy = None  # Reset on failure

    async def place_new_sell_order_if_needed(self):
        if not self.current_sell or (
                self.current_sell and not self.current_sell.order_id and not self.current_sell.is_pending):
            sell_price = self.get_best_ask()

            self.current_sell = PendingOrder(
                side="SELL",
                price=sell_price,
                quantity=self.order_quantity,
                placed_time=time.time(),
                is_pending=True
            )

            resp = await self.order_executor.place_sell_limit_order(self.symbol, sell_price, self.order_quantity)

            if resp.success:
                self.current_sell.order_id = resp.order_id
                self.current_sell.is_pending = False  # No longer pending
                print(f"Placed sell order: {resp.order_id} @ {sell_price}")
            else:
                print(f"Failed to place sell order: {resp.error_message}")
                self.current_sell = None  # Reset on failure
