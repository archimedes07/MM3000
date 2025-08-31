import asyncio
import time
import random
from typing import Optional
from dataclasses import dataclass
from order_executor import OrderExecutor

@dataclass
class ActiveOrder:
    order_id: str
    side: str
    price: float
    quantity: float
    timestamp: float

class FastMarketMaker:
    """Aggressive market maker optimized for speed and anti-gaming"""
    
    def __init__(self, orderbook, symbol):
        self.symbol = symbol
        self.orderbook = orderbook
        self.order_executor = OrderExecutor("mx0vglIZOoLYMTFKD6", "f319935c8e2242beb14854c3d12a849f")
        
        # Active orders
        self.buy_order: Optional[ActiveOrder] = None
        self.sell_order: Optional[ActiveOrder] = None
        
        # Configuration for TURBO/SATS (high volatility meme coins)
        self.base_quantity = 50  # Start small, increase if profitable
        self.min_spread_bps = 10  # 0.10% minimum spread (10 basis points)
        self.target_spread_bps = 20  # 0.20% target spread
        self.tick_size = 0.000001  # Adjust per pair
        
        # Anti-gaming features
        self.use_randomization = True
        self.last_order_time = 0
        self.min_order_interval = 0.5  # Don't update too frequently
        
        # Position tracking
        self.position = 0
        self.max_position = 500  # In base currency
        self.total_volume = 0
        self.realized_pnl = 0
        
        # Competition tracking
        self.competition_detected = False
        self.spread_competition_threshold = 5  # If spread < 5 ticks, competition exists
        
    async def on_orderbook_update(self):
        """Fast orderbook update handler"""
        # Rate limiting
        now = time.time()
        if now - self.last_order_time < self.min_order_interval:
            return
            
        best_bid = self.orderbook.get_best_bid()
        best_ask = self.orderbook.get_best_ask()
        
        if best_bid == 0 or best_ask == 0:
            return
            
        spread = best_ask - best_bid
        spread_bps = (spread / best_bid) * 10000  # Basis points
        
        # Detect competition
        self.competition_detected = spread < (self.tick_size * self.spread_competition_threshold)
        
        # Only trade if spread is profitable
        if spread_bps < self.min_spread_bps:
            return  # Too tight, skip
            
        # Calculate our prices
        buy_price, sell_price = self.calculate_optimal_prices(best_bid, best_ask, spread_bps)
        
        # Update orders
        asyncio.create_task(self.update_buy_order(buy_price))
        asyncio.create_task(self.update_sell_order(sell_price))
        
        self.last_order_time = now
    
    def calculate_optimal_prices(self, best_bid: float, best_ask: float, spread_bps: float) -> tuple:
        """Calculate optimal bid/ask prices with anti-gaming logic"""
        
        if self.competition_detected:
            # Competition mode: Join the best prices aggressively
            if self.use_randomization and random.random() < 0.3:
                # Sometimes skip a tick to confuse other bots
                buy_price = best_bid
                sell_price = best_ask
            else:
                # Improve by one tick
                buy_price = best_bid + self.tick_size
                sell_price = best_ask - self.tick_size
        else:
            # No competition: Use wider spreads for better profit
            mid_price = (best_bid + best_ask) / 2
            half_spread = (self.target_spread_bps / 10000) * mid_price / 2
            
            buy_price = round(mid_price - half_spread, 6)
            sell_price = round(mid_price + half_spread, 6)
            
            # Don't cross the market
            buy_price = min(buy_price, best_ask - self.tick_size)
            sell_price = max(sell_price, best_bid + self.tick_size)
        
        # Position-based adjustment
        if self.position > self.max_position * 0.5:
            # Too long, lower buy price and raise sell price
            buy_price -= self.tick_size * 2
            sell_price -= self.tick_size  # More aggressive selling
        elif self.position < -self.max_position * 0.5:
            # Too short, raise buy price and lower sell price
            buy_price += self.tick_size  # More aggressive buying
            sell_price += self.tick_size * 2
            
        # Add randomization to prevent gaming
        if self.use_randomization:
            if random.random() < 0.2:  # 20% of the time
                buy_price += self.tick_size * random.choice([-1, 0, 1])
                sell_price += self.tick_size * random.choice([-1, 0, 1])
        
        return buy_price, sell_price
    
    async def update_buy_order(self, target_price: float):
        """Update buy order with minimal latency"""
        # Check position limits
        if self.position >= self.max_position:
            if self.buy_order:
                await self.cancel_order(self.buy_order, "BUY")
            return
            
        # Only update if price changed significantly
        if self.buy_order and abs(self.buy_order.price - target_price) < self.tick_size * 2:
            return  # Don't update for small changes
            
        # Cancel old order if exists
        if self.buy_order:
            await self.cancel_order(self.buy_order, "BUY")
        
        # Place new order with random size variation
        quantity = self.base_quantity
        if self.use_randomization:
            quantity = int(quantity * random.uniform(0.9, 1.3))  # Changed from 0.8-1.2 to avoid going below $1
            
        resp = await self.order_executor.place_buy_limit_order(self.symbol, target_price, quantity)
        
        if resp.success:
            self.buy_order = ActiveOrder(
                order_id=resp.order_id,
                side="BUY",
                price=target_price,
                quantity=quantity,
                timestamp=time.time()
            )
            print(f"BUY: {quantity} @ {target_price:.6f}")
    
    async def update_sell_order(self, target_price: float):
        """Update sell order with minimal latency"""
        # Check position limits
        if self.position <= -self.max_position:
            if self.sell_order:
                await self.cancel_order(self.sell_order, "SELL")
            return
            
        # Only update if price changed significantly
        if self.sell_order and abs(self.sell_order.price - target_price) < self.tick_size * 2:
            return  # Don't update for small changes
            
        # Cancel old order if exists
        if self.sell_order:
            await self.cancel_order(self.sell_order, "SELL")
        
        # Place new order with random size variation
        quantity = self.base_quantity
        if self.use_randomization:
            quantity = int(quantity * random.uniform(0.9, 1.3))  # Changed from 0.8-1.2 to avoid going below $1
            
        resp = await self.order_executor.place_sell_limit_order(self.symbol, target_price, quantity)
        
        if resp.success:
            self.sell_order = ActiveOrder(
                order_id=resp.order_id,
                side="SELL",
                price=target_price,
                quantity=quantity,
                timestamp=time.time()
            )
            print(f"SELL: {quantity} @ {target_price:.6f}")
    
    async def cancel_order(self, order: ActiveOrder, side: str):
        """Cancel order and clean up"""
        try:
            await self.order_executor.cancel_order(self.symbol, order.order_id)
            if side == "BUY":
                self.buy_order = None
            else:
                self.sell_order = None
        except:
            pass  # Ignore cancel errors
    
    async def check_fills_periodically(self):
        """Check for filled orders every 2 seconds"""
        while True:
            await asyncio.sleep(2)
            
            # Check buy order
            if self.buy_order:
                status = await self.order_executor.get_order_status(self.symbol, self.buy_order.order_id)
                if status.success and status.status == "FILLED":
                    self.position += self.buy_order.quantity
                    self.total_volume += self.buy_order.quantity * self.buy_order.price
                    print(f"✅ BUY FILLED: {self.buy_order.quantity} @ {self.buy_order.price:.6f} | Pos: {self.position}")
                    self.buy_order = None
                elif status.success and status.status == "CANCELED":
                    self.buy_order = None
            
            # Check sell order
            if self.sell_order:
                status = await self.order_executor.get_order_status(self.symbol, self.sell_order.order_id)
                if status.success and status.status == "FILLED":
                    self.position -= self.sell_order.quantity
                    self.total_volume += self.sell_order.quantity * self.sell_order.price
                    profit = self.sell_order.quantity * (self.sell_order.price - self.buy_order.price if self.buy_order else 0)
                    self.realized_pnl += profit
                    print(f"✅ SELL FILLED: {self.sell_order.quantity} @ {self.sell_order.price:.6f} | Pos: {self.position} | P&L: {self.realized_pnl:.4f}")
                    self.sell_order = None
                elif status.success and status.status == "CANCELED":
                    self.sell_order = None
    
    async def start(self):
        """Start the market maker"""
        print(f"Starting FastMarketMaker for {self.symbol}")
        print(f"Config: Spread {self.min_spread_bps}-{self.target_spread_bps} bps | Max Pos: {self.max_position}")
        
        # Start fill checker
        asyncio.create_task(self.check_fills_periodically())