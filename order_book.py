from typing import Dict

class OrderBook:
    def __init__(self):
        self.bids: Dict[float, float] = {}
        self.asks: Dict[float, float] = {}

    def get_bids(self) -> Dict[float, float]:
        return self.bids.copy()

    def get_asks(self) -> Dict[float, float]:
        return self.asks.copy()

    def update_bid(self, price: float, quantity: float):
        if quantity == 0:
            self.bids.pop(price, None)
        else:
            self.bids[price] = quantity

    def update_ask(self, price: float, quantity: float):
        if quantity == 0:
            self.asks.pop(price, None)
        else:
            self.asks[price] = quantity

    def get_best_bid(self) -> float:
        return max(self.bids.keys(), default=0.0)

    def get_best_ask(self) -> float:
        return min(self.asks.keys(), default=0.0)

    def get_second_best_bid(self) -> float:
        if len(self.bids) < 2:
            return 0.0
        sorted_bids = sorted(self.bids.keys(), reverse=True)
        return sorted_bids[1]

    def get_second_best_ask(self) -> float:
        if len(self.asks) < 2:
            return 0.0
        sorted_asks = sorted(self.asks.keys())
        return sorted_asks[1]

    def get_bid_quantity(self, price: float) -> float:
        return self.bids.get(price, 0.0)

    def get_ask_quantity(self, price: float) -> float:
        return self.asks.get(price, 0.0)

    def clear(self):
        self.bids.clear()
        self.asks.clear()
