"""
Risk Management System for Trading AI
Validates trades before execution and manages risk limits.
"""
from typing import List, Dict, Any, Optional
import logging

from models.signals import Signal, SignalAction
from models.trading import Position, PositionSide
from models.settings import RiskSettings

logger = logging.getLogger(__name__)


class RiskCheckResult:
    """Result of risk validation"""
    def __init__(
        self,
        approved: bool,
        reason: Optional[str] = None,
        warnings: List[str] = None,
        position_size: float = 0.0,
        risk_amount: float = 0.0,
        risk_percent: float = 0.0
    ):
        self.approved = approved
        self.reason = reason
        self.warnings = warnings or []
        self.position_size = position_size
        self.risk_amount = risk_amount
        self.risk_percent = risk_percent
    
    def to_dict(self) -> dict:
        return {
            'approved': self.approved,
            'reason': self.reason,
            'warnings': self.warnings,
            'position_size': self.position_size,
            'risk_amount': self.risk_amount,
            'risk_percent': self.risk_percent
        }


class RiskManager:
    """Risk Management System"""
    
    def __init__(self, settings: Optional[RiskSettings] = None):
        self.settings = settings or RiskSettings()
        logger.info(f"Risk Manager initialized: max_risk={self.settings.max_risk_per_trade_percent}%")
    
    def update_settings(self, settings: RiskSettings):
        self.settings = settings
    
    def validate_trade(
        self,
        signal: Signal,
        balance: float,
        current_positions: List[Position]
    ) -> RiskCheckResult:
        """Validate if trade should be executed"""
        warnings = []
        
        # Check max open positions
        if len(current_positions) >= self.settings.max_open_positions:
            return RiskCheckResult(
                approved=False,
                reason=f"Max open positions reached ({self.settings.max_open_positions})"
            )
        
        # Check if we already have position in this asset
        for pos in current_positions:
            if pos.symbol == signal.asset:
                return RiskCheckResult(
                    approved=False,
                    reason=f"Already have open position in {signal.asset}"
                )
        
        if balance <= 0:
            return RiskCheckResult(approved=False, reason="Insufficient balance")
        
        # Calculate position size based on risk
        position_size_result = self.calculate_position_size(
            entry_price=signal.entry,
            stop_loss=signal.stop_loss,
            account_balance=balance,
            max_risk_percent=self.settings.max_risk_per_trade_percent,
            leverage=signal.leverage
        )
        
        if not position_size_result['valid']:
            return RiskCheckResult(
                approved=False,
                reason=position_size_result['reason']
            )
        
        position_size = position_size_result['position_size']
        risk_amount = position_size_result['risk_amount']
        risk_percent = position_size_result['risk_percent']
        
        # Check risk/reward ratio
        if signal.take_profits:
            rr_ratio = self._calculate_risk_reward(
                entry=signal.entry,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profits[0],
                action=signal.action
            )
            
            if rr_ratio < self.settings.min_risk_reward_ratio:
                warnings.append(f"Low R:R ratio: {rr_ratio:.2f} (min: {self.settings.min_risk_reward_ratio})")
        
        # Check total portfolio risk
        total_risk = risk_amount
        for pos in current_positions:
            if pos.stop_loss:
                pos_risk = abs(pos.entry_price - pos.stop_loss) * pos.quantity
                total_risk += pos_risk
        
        total_risk_percent = (total_risk / balance) * 100
        
        if total_risk_percent > self.settings.max_portfolio_risk_percent:
            return RiskCheckResult(
                approved=False,
                reason=f"Portfolio risk too high: {total_risk_percent:.1f}% (max: {self.settings.max_portfolio_risk_percent}%)"
            )
        
        # Correlation check
        for pos in current_positions:
            if self._are_correlated(signal.asset, pos.symbol):
                warnings.append(f"High correlation with open position: {pos.symbol}")
        
        logger.info(f"Risk check PASSED for {signal.asset}: size={position_size:.4f}, risk={risk_percent:.2f}%")
        
        return RiskCheckResult(
            approved=True,
            warnings=warnings,
            position_size=position_size,
            risk_amount=risk_amount,
            risk_percent=risk_percent
        )
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        account_balance: float,
        max_risk_percent: float = 2.0,
        leverage: int = 1
    ) -> dict:
        """Calculate position size based on risk"""
        risk_amount = account_balance * (max_risk_percent / 100)
        risk_per_unit = abs(entry_price - stop_loss)
        
        if risk_per_unit <= 0:
            return {
                'valid': False,
                'reason': 'Invalid stop loss (must be different from entry)',
                'position_size': 0,
                'risk_amount': 0,
                'risk_percent': 0
            }
        
        position_size = risk_amount / risk_per_unit
        actual_risk_amount = position_size * risk_per_unit
        actual_risk_percent = (actual_risk_amount / account_balance) * 100
        
        position_value = position_size * entry_price
        max_position_value = account_balance * leverage
        
        if position_value > max_position_value:
            return {
                'valid': False,
                'reason': f'Position too large for account (need ${position_value:.2f}, have ${max_position_value:.2f})',
                'position_size': 0,
                'risk_amount': 0,
                'risk_percent': 0
            }
        
        logger.debug(f"Position size: {position_size:.6f} units (risk: ${risk_amount:.2f}, {actual_risk_percent:.2f}%)")
        
        return {
            'valid': True,
            'position_size': position_size,
            'risk_amount': actual_risk_amount,
            'risk_percent': actual_risk_percent,
            'position_value': position_value
        }
    
    def _calculate_risk_reward(
        self,
        entry: float,
        stop_loss: float,
        take_profit: float,
        action: SignalAction
    ) -> float:
        """Calculate risk/reward ratio"""
        is_long = action in (SignalAction.LONG, SignalAction.BUY)
        
        if is_long:
            risk = abs(entry - stop_loss)
            reward = abs(take_profit - entry)
        else:
            risk = abs(stop_loss - entry)
            reward = abs(entry - take_profit)
        
        if risk <= 0:
            return 0.0
        
        return reward / risk
    
    def _are_correlated(self, symbol1: str, symbol2: str) -> bool:
        """Check if two symbols are correlated"""
        base1 = symbol1.split('/')[0] if '/' in symbol1 else symbol1[:3]
        base2 = symbol2.split('/')[0] if '/' in symbol2 else symbol2[:3]
        return base1 == base2


# Singleton instance
risk_manager = RiskManager()
