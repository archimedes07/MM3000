#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "protogenerated"))

import asyncio
from websocket_client import WebSocketClient
from order_book import OrderBook
from fast_market_maker import FastMarketMaker

# OPTIMAL PAIRS FOR MEXC (in order of recommendation)
RECOMMENDED_PAIRS = {
    "TURBOUSDT": {
        "tick_size": 0.000001,  # For price ~0.004, tick is 0.000001
        "base_quantity": 10000,  # TURBO is cheap, need more units
        "min_spread_bps": 10,
        "target_spread_bps": 25
    },
    "1000SATSUSDT": {
        "tick_size": 0.00001,
        "base_quantity": 1000,
        "min_spread_bps": 15,
        "target_spread_bps": 30
    },
    "MOODENGUSDT": {
        "tick_size": 0.00001,  # Adjusted for typical MOODENG price
        "base_quantity": 100,
        "min_spread_bps": 20,
        "target_spread_bps": 40
    },
    "WOJAKUSDT": {
        "tick_size": 0.000001,
        "base_quantity": 5000,
        "min_spread_bps": 25,
        "target_spread_bps": 50
    }
}

async def main():
    # CHANGE THIS TO YOUR PREFERRED PAIR
    SYMBOL = "TURBOUSDT"  # Start with TURBO - high volume meme coin
    
    config = RECOMMENDED_PAIRS.get(SYMBOL, {
        "tick_size": 0.000001,
        "base_quantity": 50,
        "min_spread_bps": 15,
        "target_spread_bps": 30
    })
    
    print(f"=" * 60)
    print(f"FAST MARKET MAKER - {SYMBOL}")
    print(f"Configuration: {config}")
    print(f"=" * 60)
    
    order_book = OrderBook()
    market_maker = FastMarketMaker(order_book, SYMBOL)
    
    # Apply configuration
    market_maker.tick_size = config["tick_size"]
    market_maker.base_quantity = config["base_quantity"]
    market_maker.min_spread_bps = config["min_spread_bps"]
    market_maker.target_spread_bps = config["target_spread_bps"]
    
    # Start the market maker
    await market_maker.start()

    async def orderbook_update_handler(update):
        for price, qty in update["bids"]:
            order_book.update_bid(price, qty)
        for price, qty in update["asks"]:
            order_book.update_ask(price, qty)
        await market_maker.on_orderbook_update()

    async def orderbook_snapshot_handler(snapshot):
        order_book.clear()
        for price, qty in snapshot["bids"]:
            order_book.update_bid(price, qty)
        for price, qty in snapshot["asks"]:
            order_book.update_ask(price, qty)
        print(f"Orderbook initialized. Spread: {order_book.get_spread():.6f} ({order_book.get_spread_percentage():.2f}%)")

    client = WebSocketClient(SYMBOL)
    client.set_orderbook_update_callback(orderbook_update_handler)
    client.set_orderbook_snapshot_callback(orderbook_snapshot_handler)

    await client.connect()
    await client.send_subscription()
    
    print("Market maker is running. Press Ctrl+C to stop.")
    print("-" * 60)
    
    await client.run_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down market maker...")