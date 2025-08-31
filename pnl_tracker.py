from dataclasses import dataclass, field
from typing import List, Dict
import time

@dataclass
class Trade:
    order_id: str
    side: str  # "BUY" or "SELL"
    price: float
    quantity: float
    timestamp: float = field(default_factory=time.time)

class PnLTracker:
    def __init__(self):
        self.trades: List[Trade] = []
        self.position: float = 0.0  # Current position (positive = long, negative = short)
        self.total_buy_value: float = 0.0
        self.total_sell_value: float = 0.0
        self.total_buy_quantity: float = 0.0
        self.total_sell_quantity: float = 0.0
        self.realized_pnl: float = 0.0
        self.fees_paid: float = 0.0
        self.fee_rate: float = 0.001  # 0.1% default fee
        
    def add_trade(self, order_id: str, side: str, price: float, quantity: float):
        """Record a filled trade"""
        trade = Trade(order_id, side, price, quantity)
        self.trades.append(trade)
        
        # Calculate fee
        fee = price * quantity * self.fee_rate
        self.fees_paid += fee
        
        if side == "BUY":
            self.position += quantity
            self.total_buy_value += price * quantity
            self.total_buy_quantity += quantity
        else:  # SELL
            self.position -= quantity
            self.total_sell_value += price * quantity
            self.total_sell_quantity += quantity
            
        # Update realized PnL
        self._update_realized_pnl()
        
    def _update_realized_pnl(self):
        """Calculate realized PnL from matched trades"""
        # Simple FIFO matching for realized PnL
        matched_quantity = min(self.total_buy_quantity, self.total_sell_quantity)
        if matched_quantity > 0:
            avg_buy_price = self.total_buy_value / self.total_buy_quantity if self.total_buy_quantity > 0 else 0
            avg_sell_price = self.total_sell_value / self.total_sell_quantity if self.total_sell_quantity > 0 else 0
            self.realized_pnl = (avg_sell_price - avg_buy_price) * matched_quantity - self.fees_paid
            
    def get_unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized PnL based on current market price"""
        if self.position == 0:
            return 0.0
            
        if self.position > 0:  # Long position
            avg_buy_price = self.total_buy_value / self.total_buy_quantity if self.total_buy_quantity > 0 else 0
            return (current_price - avg_buy_price) * self.position
        else:  # Short position
            avg_sell_price = self.total_sell_value / self.total_sell_quantity if self.total_sell_quantity > 0 else 0
            return (avg_sell_price - current_price) * abs(self.position)
            
    def get_total_pnl(self, current_price: float) -> float:
        """Get total PnL (realized + unrealized)"""
        return self.realized_pnl + self.get_unrealized_pnl(current_price)
        
    def get_stats(self, current_price: float) -> Dict:
        """Get comprehensive PnL statistics"""
        total_trades = len(self.trades)
        buy_trades = sum(1 for t in self.trades if t.side == "BUY")
        sell_trades = sum(1 for t in self.trades if t.side == "SELL")
        
        return {
            "position": self.position,
            "total_trades": total_trades,
            "buy_trades": buy_trades,
            "sell_trades": sell_trades,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.get_unrealized_pnl(current_price),
            "total_pnl": self.get_total_pnl(current_price),
            "fees_paid": self.fees_paid,
            "avg_buy_price": self.total_buy_value / self.total_buy_quantity if self.total_buy_quantity > 0 else 0,
            "avg_sell_price": self.total_sell_value / self.total_sell_quantity if self.total_sell_quantity > 0 else 0,
        }
        
    def print_stats(self, current_price: float):
        """Print formatted PnL statistics"""
        stats = self.get_stats(current_price)
        print("\n=== PnL Statistics ===")
        print(f"Position: {stats['position']:.4f}")
        print(f"Total Trades: {stats['total_trades']} (Buy: {stats['buy_trades']}, Sell: {stats['sell_trades']})")
        print(f"Avg Buy Price: {stats['avg_buy_price']:.5f}")
        print(f"Avg Sell Price: {stats['avg_sell_price']:.5f}")
        print(f"Realized PnL: ${stats['realized_pnl']:.2f}")
        print(f"Unrealized PnL: ${stats['unrealized_pnl']:.2f}")
        print(f"Total PnL: ${stats['total_pnl']:.2f}")
        print(f"Fees Paid: ${stats['fees_paid']:.2f}")
        print("=" * 22)