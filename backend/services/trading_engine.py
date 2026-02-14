"""
Paper Trading Engine for Trading AI
Simple in-memory trading simulation.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from enum import Enum
import uuid
import random

logger = logging.getLogger(__name__)


class TradeStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class ExitReason(str, Enum):
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    MANUAL = "manual"
    TRAILING_STOP = "trailing_stop"


class PositionSide(str, Enum):
    LONG = "long"
    SHORT = "short"


@dataclass
class Trade:
    id: str
    signal_id: str
    symbol: str
    side: PositionSide
    entry_price: float
    quantity: float
    stop_loss: float
    take_profits: List[float]
    leverage: int = 1
    status: TradeStatus = TradeStatus.OPEN
    entry_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[ExitReason] = None
    pnl: float = 0.0
    pnl_percent: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "signal_id": self.signal_id,
            "symbol": self.symbol,
            "side": self.side.value if isinstance(self.side, PositionSide) else self.side,
            "entry_price": self.entry_price,
            "quantity": self.quantity,
            "stop_loss": self.stop_loss,
            "take_profits": self.take_profits,
            "leverage": self.leverage,
            "status": self.status.value if isinstance(self.status, TradeStatus) else self.status,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "exit_price": self.exit_price,
            "exit_reason": self.exit_reason.value if self.exit_reason else None,
            "pnl": self.pnl,
            "pnl_percent": self.pnl_percent
        }


@dataclass
class Position:
    symbol: str
    side: PositionSide
    quantity: float
    entry_price: float
    current_price: float
    leverage: int = 1
    unrealized_pnl: float = 0.0
    unrealized_pnl_percent: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "side": self.side.value if isinstance(self.side, PositionSide) else self.side,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "leverage": self.leverage,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_percent": self.unrealized_pnl_percent
        }


@dataclass 
class Portfolio:
    initial_balance: float = 10000.0
    current_balance: float = 10000.0
    total_pnl: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    def to_dict(self) -> dict:
        return {
            "initial_balance": self.initial_balance,
            "current_balance": self.current_balance,
            "total_pnl": self.total_pnl,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": self.winning_trades / self.total_trades if self.total_trades > 0 else 0
        }


class TradingEngine:
    """Simple paper trading engine"""
    
    def __init__(self, settings=None):
        self.trades: Dict[str, Trade] = {}
        self.positions: Dict[str, Position] = {}
        self.portfolio = Portfolio()
        self.settings = settings
        
        logger.info("TradingEngine initialized")
    
    def execute_signal(self, signal) -> Optional[Trade]:
        """Execute a trade from a signal"""
        trade = Trade(
            id=str(uuid.uuid4()),
            signal_id=signal.id if hasattr(signal, 'id') else str(uuid.uuid4()),
            symbol=signal.asset if hasattr(signal, 'asset') else signal.get('asset', ''),
            side=PositionSide.LONG if str(signal.action if hasattr(signal, 'action') else signal.get('action', '')).lower() in ['long', 'buy'] else PositionSide.SHORT,
            entry_price=signal.entry if hasattr(signal, 'entry') else signal.get('entry', 0),
            quantity=0.01,  # Default quantity
            stop_loss=signal.stop_loss if hasattr(signal, 'stop_loss') else signal.get('stop_loss', 0),
            take_profits=signal.take_profits if hasattr(signal, 'take_profits') else signal.get('take_profits', []),
            leverage=signal.leverage if hasattr(signal, 'leverage') else signal.get('leverage', 1)
        )
        
        self.trades[trade.id] = trade
        
        # Create position
        self.positions[trade.symbol] = Position(
            symbol=trade.symbol,
            side=trade.side,
            quantity=trade.quantity,
            entry_price=trade.entry_price,
            current_price=trade.entry_price,
            leverage=trade.leverage
        )
        
        logger.info(f"Trade executed: {trade.symbol} {trade.side.value}")
        return trade
    
    def close_trade(self, trade_id: str, exit_reason: ExitReason = ExitReason.MANUAL) -> bool:
        """Close a trade"""
        trade = self.trades.get(trade_id)
        if not trade or trade.status != TradeStatus.OPEN:
            return False
        
        # Get current price (simulated)
        position = self.positions.get(trade.symbol)
        current_price = position.current_price if position else trade.entry_price
        
        # Calculate P&L
        if trade.side == PositionSide.LONG:
            pnl = (current_price - trade.entry_price) * trade.quantity * trade.leverage
            pnl_percent = ((current_price - trade.entry_price) / trade.entry_price) * 100 * trade.leverage
        else:
            pnl = (trade.entry_price - current_price) * trade.quantity * trade.leverage
            pnl_percent = ((trade.entry_price - current_price) / trade.entry_price) * 100 * trade.leverage
        
        trade.exit_price = current_price
        trade.exit_time = datetime.now(timezone.utc)
        trade.exit_reason = exit_reason
        trade.status = TradeStatus.CLOSED
        trade.pnl = pnl
        trade.pnl_percent = pnl_percent
        
        # Update portfolio
        self.portfolio.current_balance += pnl
        self.portfolio.total_pnl += pnl
        self.portfolio.total_trades += 1
        if pnl > 0:
            self.portfolio.winning_trades += 1
        else:
            self.portfolio.losing_trades += 1
        
        # Remove position
        if trade.symbol in self.positions:
            del self.positions[trade.symbol]
        
        logger.info(f"Trade closed: {trade.symbol} P&L: ${pnl:.2f}")
        return True
    
    def get_open_trades(self) -> List[Trade]:
        """Get all open trades"""
        return [t for t in self.trades.values() if t.status == TradeStatus.OPEN]
    
    def get_all_trades(self) -> List[Trade]:
        """Get all trades"""
        return list(self.trades.values())
    
    def get_positions(self) -> List[Position]:
        """Get all open positions"""
        return list(self.positions.values())
    
    def get_portfolio(self) -> Portfolio:
        """Get portfolio"""
        return self.portfolio
    
    def get_statistics(self) -> dict:
        """Get trading statistics"""
        return {
            "total_trades": self.portfolio.total_trades,
            "winning_trades": self.portfolio.winning_trades,
            "losing_trades": self.portfolio.losing_trades,
            "win_rate": self.portfolio.winning_trades / self.portfolio.total_trades if self.portfolio.total_trades > 0 else 0,
            "total_pnl": self.portfolio.total_pnl,
            "current_balance": self.portfolio.current_balance,
            "open_positions": len(self.positions)
        }
    
    def simulate_price_update(self, symbol: str, change_percent: float = None):
        """Simulate price update for testing"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        if change_percent is None:
            change_percent = random.uniform(-2, 2)
        
        position.current_price *= (1 + change_percent / 100)
        
        # Update P&L
        if position.side == PositionSide.LONG:
            position.unrealized_pnl = (position.current_price - position.entry_price) * position.quantity * position.leverage
            position.unrealized_pnl_percent = ((position.current_price - position.entry_price) / position.entry_price) * 100 * position.leverage
        else:
            position.unrealized_pnl = (position.entry_price - position.current_price) * position.quantity * position.leverage
            position.unrealized_pnl_percent = ((position.entry_price - position.current_price) / position.entry_price) * 100 * position.leverage
    
    def update_settings(self, settings):
        """Update engine settings"""
        self.settings = settings
        if settings and hasattr(settings, 'initial_balance'):
            self.portfolio.initial_balance = settings.initial_balance
