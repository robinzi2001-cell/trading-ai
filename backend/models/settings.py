"""
Settings Models for Trading AI
"""
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


class RiskSettings(BaseModel):
    """Risk Management Settings"""
    max_risk_per_trade_percent: float = Field(default=2.0, ge=0.1, le=10.0)
    max_open_positions: int = Field(default=5, ge=1, le=20)
    max_correlation: float = Field(default=0.7, ge=0.0, le=1.0)
    min_risk_reward_ratio: float = Field(default=1.5, ge=0.5, le=10.0)
    max_portfolio_risk_percent: float = Field(default=10.0, ge=1.0, le=50.0)
    default_leverage: int = Field(default=1, ge=1, le=125)
    
    def to_dict(self) -> dict:
        return self.model_dump()


class TradingSettings(BaseModel):
    """Trading System Settings"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Account
    initial_balance: float = 10000.0
    paper_trading: bool = True
    auto_execute: bool = False
    
    # Risk
    risk_settings: RiskSettings = Field(default_factory=RiskSettings)
    
    # Signal Sources
    telegram_enabled: bool = False
    telegram_channels: List[str] = Field(default_factory=list)
    
    email_enabled: bool = False
    email_address: Optional[str] = None
    
    webhook_enabled: bool = True
    webhook_api_keys: List[str] = Field(default_factory=list)
    
    # Broker
    broker_name: str = "paper"
    broker_testnet: bool = True
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> dict:
        data = self.model_dump()
        data['created_at'] = data['created_at'].isoformat()
        data['updated_at'] = data['updated_at'].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TradingSettings':
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class SettingsUpdate(BaseModel):
    """Input model for updating settings"""
    initial_balance: Optional[float] = None
    paper_trading: Optional[bool] = None
    auto_execute: Optional[bool] = None
    
    max_risk_per_trade_percent: Optional[float] = None
    max_open_positions: Optional[int] = None
    min_risk_reward_ratio: Optional[float] = None
    default_leverage: Optional[int] = None
    
    telegram_enabled: Optional[bool] = None
    telegram_channels: Optional[List[str]] = None
    
    email_enabled: Optional[bool] = None
    email_address: Optional[str] = None
    
    webhook_enabled: Optional[bool] = None
