import asyncio
import sys
from datetime import datetime
from market_maker import MarketMaker
from order_book import OrderBook

class MarketMakerMonitor:
    """Monitor and display market maker statistics"""
    
    def __init__(self, market_maker: MarketMaker, orderbook: OrderBook):
        self.market_maker = market_maker
        self.orderbook = orderbook
        self.start_time = datetime.now()
    
    async def display_status(self):
        """Continuously display market maker status"""
        while True:
            self.clear_screen()
            self.print_header()
            self.print_market_data()
            self.print_position_data()
            self.print_pnl_data()
            self.print_order_status()
            
            await asyncio.sleep(1)  # Update every second
    
    def clear_screen(self):
        """Clear console screen"""
        print("\033[2J\033[H", end="")  # ANSI escape codes to clear screen
    
    def print_header(self):
        """Print header information"""
        runtime = datetime.now() - self.start_time
        print("=" * 60)
        print(f"MARKET MAKER MONITOR - {self.market_maker.symbol}")
        print(f"Runtime: {runtime} | Status: {'ACTIVE' if self.market_maker.is_trading_enabled else 'STOPPED'}")
        print("=" * 60)
    
    def print_market_data(self):
        """Print market data"""
        best_bid = self.orderbook.get_best_bid()
        best_ask = self.orderbook.get_best_ask()
        spread = self.orderbook.get_spread()
        spread_pct = self.orderbook.get_spread_percentage()
        
        print("\n📊 MARKET DATA")
        print(f"Best Bid: {best_bid:.6f} | Best Ask: {best_ask:.6f}")
        print(f"Spread: {spread:.6f} ({spread_pct:.3f}%)")
        print(f"Mid Price: {(best_bid + best_ask) / 2:.6f}")
    
    def print_position_data(self):
        """Print position information"""
        mm = self.market_maker
        position_pct = (mm.position / mm.max_position * 100) if mm.max_position > 0 else 0
        
        print("\n📦 POSITION")
        print(f"Current: {mm.position:.2f} / {mm.max_position} ({position_pct:.1f}%)")
        print(f"Avg Buy: {mm.get_avg_buy_price():.6f} | Avg Sell: {mm.get_avg_sell_price():.6f}")
    
    def print_pnl_data(self):
        """Print P&L information"""
        mm = self.market_maker
        unrealized = mm.get_unrealized_pnl()
        total_pnl = mm.realized_pnl + unrealized
        
        print("\n💰 P&L")
        print(f"Realized: {mm.realized_pnl:.4f}")
        print(f"Unrealized: {unrealized:.4f}")
        print(f"Total: {total_pnl:.4f}")
        print(f"Trades: {mm.trades_count}")
    
    def print_order_status(self):
        """Print current order status"""
        mm = self.market_maker
        
        print("\n📋 ACTIVE ORDERS")
        if mm.current_buy and mm.current_buy.order_id:
            print(f"Buy: {mm.current_buy.quantity} @ {mm.current_buy.price:.6f} (ID: {mm.current_buy.order_id[:8]}...)")
        else:
            print("Buy: None")
        
        if mm.current_sell and mm.current_sell.order_id:
            print(f"Sell: {mm.current_sell.quantity} @ {mm.current_sell.price:.6f} (ID: {mm.current_sell.order_id[:8]}...)")
        else:
            print("Sell: None")
        
        print("\n" + "=" * 60)

async def run_monitor(market_maker: MarketMaker, orderbook: OrderBook):
    """Run the monitoring interface"""
    monitor = MarketMakerMonitor(market_maker, orderbook)
    await monitor.display_status()

if __name__ == "__main__":
    print("This module should be imported and run with an existing market maker instance")