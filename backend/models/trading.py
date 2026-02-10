"""
Trading Engine - Data Models
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class OrderStatus(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class PositionSide(str, Enum):
    LONG = "long"
    SHORT = "short"


class TradeStatus(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class ExitReason(str, Enum):
    TAKE_PROFIT = "tp"
    STOP_LOSS = "sl"
    TRAILING_STOP = "trailing_stop"
    MANUAL = "manual"
    LIQUIDATION = "liquidation"
    EXPIRED = "expired"


class Order(BaseModel):
    """Order representation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    broker: str = "paper"
    broker_order_id: Optional[str] = None
    
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    
    executed_quantity: float = 0.0
    executed_price: Optional[float] = None
    average_price: Optional[float] = None
    
    status: OrderStatus = OrderStatus.PENDING
    commission: float = 0.0
    slippage: float = 0.0
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: Optional[datetime] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def to_dict(self) -> dict:
        data = self.model_dump()
        data['created_at'] = data['created_at'].isoformat()
        if data['executed_at']:
            data['executed_at'] = data['executed_at'].isoformat()
        return data


class Position(BaseModel):
    """Open Position"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    broker: str = "paper"
    symbol: str
    
    side: PositionSide
    entry_price: float
    quantity: float
    leverage: int = 1
    
    current_price: float
    unrealized_pnl: float = 0.0
    unrealized_pnl_percent: float = 0.0
    
    stop_loss: Optional[float] = None
    take_profits: List[float] = Field(default_factory=list)
    
    opened_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def update_pnl(self, current_price: float):
        self.current_price = current_price
        if self.side == PositionSide.LONG:
            pnl = (current_price - self.entry_price) * self.quantity
        else:
            pnl = (self.entry_price - current_price) * self.quantity
        
        self.unrealized_pnl = pnl * self.leverage
        position_value = self.entry_price * self.quantity
        self.unrealized_pnl_percent = (pnl / position_value) * 100 if position_value else 0
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> dict:
        data = self.model_dump()
        data['opened_at'] = data['opened_at'].isoformat()
        data['updated_at'] = data['updated_at'].isoformat()
        return data


class Trade(BaseModel):
    """Completed Trade"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    signal_id: Optional[str] = None
    
    broker: str = "paper"
    symbol: str
    side: PositionSide
    
    entry_price: float
    entry_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    quantity: float
    leverage: int = 1
    
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    exit_reason: Optional[ExitReason] = None
    
    realized_pnl: Optional[float] = None
    realized_pnl_percent: Optional[float] = None
    
    total_commission: float = 0.0
    status: TradeStatus = TradeStatus.PENDING
    
    stop_loss: Optional[float] = None
    take_profits: List[float] = Field(default_factory=list)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def close(self, exit_price: float, exit_reason: ExitReason, commission: float = 0.0):
        self.exit_price = exit_price
        self.exit_time = datetime.now(timezone.utc)
        self.exit_reason = exit_reason
        self.status = TradeStatus.CLOSED
        
        if self.side == PositionSide.LONG:
            pnl = (exit_price - self.entry_price) * self.quantity
        else:
            pnl = (self.entry_price - exit_price) * self.quantity
        
        self.realized_pnl = (pnl * self.leverage) - commission
        position_value = self.entry_price * self.quantity
        self.realized_pnl_percent = (pnl / position_value) * 100 if position_value else 0
        self.total_commission += commission
    
    def to_dict(self) -> dict:
        data = self.model_dump()
        data['entry_time'] = data['entry_time'].isoformat()
        if data['exit_time']:
            data['exit_time'] = data['exit_time'].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Trade':
        if isinstance(data.get('entry_time'), str):
            data['entry_time'] = datetime.fromisoformat(data['entry_time'])
        if isinstance(data.get('exit_time'), str):
            data['exit_time'] = datetime.fromisoformat(data['exit_time'])
        return cls(**data)


class Portfolio(BaseModel):
    """Portfolio State"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    broker: str = "paper"
    
    initial_balance: float = 10000.0
    current_balance: float = 10000.0
    available_balance: float = 10000.0
    margin_used: float = 0.0
    
    total_pnl: float = 0.0
    total_pnl_percent: float = 0.0
    
    open_positions: int = 0
    total_positions_value: float = 0.0
    
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    
    max_drawdown: float = 0.0
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def update_from_trade(self, trade: Trade):
        if trade.status != TradeStatus.CLOSED or trade.realized_pnl is None:
            return
        
        self.total_trades += 1
        self.total_pnl += trade.realized_pnl
        self.current_balance += trade.realized_pnl
        self.available_balance = self.current_balance - self.margin_used
        
        self.total_pnl_percent = ((self.current_balance - self.initial_balance) / self.initial_balance) * 100
        
        if trade.realized_pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        self.win_rate = (self.winning_trades / self.total_trades) * 100 if self.total_trades > 0 else 0
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> dict:
        data = self.model_dump()
        data['created_at'] = data['created_at'].isoformat()
        data['updated_at'] = data['updated_at'].isoformat()
        return data


class TradeCreate(BaseModel):
    """Input model for creating trades"""
    signal_id: str
    quantity: Optional[float] = None


class TradeClose(BaseModel):
    """Input model for closing trades"""
    trade_id: str
    exit_reason: str = "manual"
