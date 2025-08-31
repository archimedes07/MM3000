class MarketMakerConfig:
    """Configuration for the market maker strategy"""
    
    # Order parameters
    ORDER_QUANTITY = 4
    TICK_SIZE = 0.0001
    
    # Spread strategy
    SPREAD_TICKS = 2  # Number of ticks for spread (2 = 0.000002)
    MIN_SPREAD_PERCENTAGE = 0.05  # Minimum spread as percentage (0.05%)
    AGGRESSIVE_MODE = False  # When True, join best bid/ask; when False, use spread
    
    # Position management
    MAX_POSITION = 100  # Maximum position size (long or short)
    POSITION_SKEW_FACTOR = 0.5  # How much to skew prices based on position (0-1)
    
    # Risk controls
    MAX_ORDER_AGE_SECONDS = 30  # Cancel orders older than this
    MIN_ORDER_REFRESH_SECONDS = 2  # Minimum time between order updates
    
    # P&L settings
    STOP_LOSS_AMOUNT = -50  # Stop trading if total P&L falls below this
    TAKE_PROFIT_AMOUNT = 100  # Optional: stop trading after reaching profit target
    
    # Market conditions
    MIN_ORDERBOOK_DEPTH = 5  # Minimum number of levels in orderbook to trade
    MAX_SPREAD_TO_TRADE = 0.5  # Don't trade if spread is larger than this percentage
    
    @classmethod
    def get_adaptive_spread(cls, volatility: float, position: float, max_position: float) -> int:
        """
        Dynamically adjust spread based on market conditions
        Higher volatility = wider spread
        Larger position = wider spread to reduce risk
        """
        base_spread = cls.SPREAD_TICKS
        
        # Adjust for volatility (placeholder - would need volatility calculation)
        volatility_adjustment = int(volatility * 10)
        
        # Adjust for position size
        position_ratio = abs(position) / max_position if max_position > 0 else 0
        position_adjustment = int(position_ratio * 3)
        
        return max(1, base_spread + volatility_adjustment + position_adjustment)