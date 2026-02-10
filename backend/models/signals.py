"""
Signal Data Models for Trading AI
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import uuid


class MarketType(str, Enum):
    CRYPTO = "crypto"
    FOREX = "forex"
    STOCKS = "stocks"
    COMMODITIES = "commodities"
    INDICES = "indices"


class SignalAction(str, Enum):
    LONG = "long"
    SHORT = "short"
    BUY = "buy"
    SELL = "sell"


class SignalSource(str, Enum):
    TELEGRAM = "telegram"
    EMAIL = "email"
    WEBHOOK = "webhook"
    MANUAL = "manual"
    AI = "ai"


class Signal(BaseModel):
    """Normalized Trading Signal"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: SignalSource
    source_id: Optional[str] = None
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Trading Data
    asset: str
    market_type: Optional[MarketType] = None
    action: SignalAction
    entry: float
    stop_loss: float
    take_profits: List[float] = Field(default_factory=list)
    
    # Optional
    leverage: int = Field(default=1, ge=1, le=125)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    timeframe: Optional[str] = None
    
    # Context
    original_text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Status
    executed: bool = False
    dismissed: bool = False
    
    @field_validator('asset')
    @classmethod
    def normalize_asset(cls, v: str) -> str:
        return v.strip().upper()
    
    @field_validator('take_profits')
    @classmethod
    def validate_take_profits(cls, v: List[float]) -> List[float]:
        if not v:
            return v
        return sorted(set(v))
    
    def to_dict(self) -> dict:
        data = self.model_dump()
        data['received_at'] = data['received_at'].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Signal':
        if isinstance(data.get('received_at'), str):
            data['received_at'] = datetime.fromisoformat(data['received_at'])
        return cls(**data)


class ParsedSignal(BaseModel):
    """Intermediate parsing result before full validation"""
    raw_text: str
    confidence: float = 0.0
    
    # Extracted fields
    asset: Optional[str] = None
    action: Optional[str] = None
    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profits: List[float] = Field(default_factory=list)
    leverage: Optional[int] = None
    timeframe: Optional[str] = None
    
    # Metadata
    extracted_values: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    
    def is_valid(self) -> bool:
        required = [self.asset, self.action, self.entry, self.stop_loss]
        return all(v is not None for v in required)
    
    def to_signal(self, source: SignalSource, source_id: Optional[str] = None) -> Optional[Signal]:
        if not self.is_valid():
            return None
        
        try:
            market_type = self._detect_market_type(self.asset)
            action = SignalAction.LONG if self.action.lower() in ['long', 'buy'] else SignalAction.SHORT
            
            return Signal(
                source=source,
                source_id=source_id,
                asset=self.asset,
                market_type=market_type,
                action=action,
                entry=self.entry,
                stop_loss=self.stop_loss,
                take_profits=self.take_profits,
                leverage=self.leverage or 1,
                confidence=self.confidence,
                timeframe=self.timeframe,
                original_text=self.raw_text,
                metadata=self.extracted_values
            )
        except Exception as e:
            self.errors.append(f"Signal creation error: {e}")
            return None
    
    @staticmethod
    def _detect_market_type(asset: str) -> MarketType:
        asset = asset.upper()
        if any(pair in asset for pair in ['USDT', 'USDC', 'BUSD', 'BTC/', '/BTC']):
            return MarketType.CRYPTO
        if len(asset) == 6 and asset.isalpha():
            return MarketType.FOREX
        if any(comm in asset for comm in ['XAU', 'XAG', 'OIL', 'GLD', 'SLV']):
            return MarketType.COMMODITIES
        if any(idx in asset for idx in ['SPX', 'NDX', 'DJI', 'DAX']):
            return MarketType.INDICES
        return MarketType.STOCKS


class SignalCreate(BaseModel):
    """Input model for creating signals"""
    asset: str
    action: str
    entry: float
    stop_loss: float
    take_profits: List[float] = Field(default_factory=list)
    leverage: int = 1
    source: str = "manual"
    confidence: float = 0.5
    original_text: Optional[str] = None


class SignalWebhook(BaseModel):
    """Input model for webhook signals"""
    text: Optional[str] = None
    asset: Optional[str] = None
    action: Optional[str] = None
    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profits: Optional[List[float]] = None
    leverage: Optional[int] = None
    source_id: Optional[str] = None
