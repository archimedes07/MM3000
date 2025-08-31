import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "protogenerated"))

import asyncio
from websocket_client import WebSocketClient
from order_book import OrderBook
from market_maker import MarketMaker

async def main():
    order_book = OrderBook()
    market_maker = MarketMaker(order_book, "LAUNCHCOINUSDT")

    async def orderbook_update_handler(update):
        for price, qty in update["bids"]:
            order_book.update_bid(price, qty)
        for price, qty in update["asks"]:
            order_book.update_ask(price, qty)
        asyncio.create_task(market_maker.on_orderbook_update())

    async def orderbook_snapshot_handler(snapshot):
        order_book.clear()
        for price, qty in snapshot["bids"]:
            order_book.update_bid(price, qty)
        for price, qty in snapshot["asks"]:
            order_book.update_ask(price, qty)

    client = WebSocketClient("LAUNCHCOINUSDT")
    client.set_orderbook_update_callback(orderbook_update_handler)
    client.set_orderbook_snapshot_callback(orderbook_snapshot_handler)

    await client.connect()
    await client.send_subscription()
    await client.run_loop()

if __name__ == "__main__":
    asyncio.run(main())