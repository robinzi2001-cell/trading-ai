"""
Paper Trading Engine for Trading AI
Simulates trade execution for testing and demo purposes.
"""
from typing import List, Optional, Dict
from datetime import datetime, timezone
import random
import logging

from models.signals import Signal, SignalAction
from models.trading import Trade, Position, Portfolio, PositionSide, TradeStatus, ExitReason, Order, OrderSide, OrderType, OrderStatus
from models.settings import TradingSettings
from services.risk_manager import RiskManager, RiskCheckResult

logger = logging.getLogger(__name__)


class TradingEngine:
    """Paper Trading Engine"""
    
    def __init__(self, settings: Optional[TradingSettings] = None):
        self.settings = settings or TradingSettings()
        self.risk_manager = RiskManager(self.settings.risk_settings)
        
        # Portfolio state
        self.portfolio = Portfolio(
            initial_balance=self.settings.initial_balance,
            current_balance=self.settings.initial_balance,
            available_balance=self.settings.initial_balance
        )
        
        # Positions and trades
        self.positions: Dict[str, Position] = {}  # symbol -> Position
        self.trades: Dict[str, Trade] = {}  # trade_id -> Trade
        self.open_trades: List[str] = []
        
        logger.info(f"Trading Engine initialized with ${self.settings.initial_balance:,.2f}")
    
    def update_settings(self, settings: TradingSettings):
        self.settings = settings
        self.risk_manager.update_settings(settings.risk_settings)
    
    def execute_signal(self, signal: Signal, custom_quantity: Optional[float] = None) -> Optional[Trade]:
        """Execute a trading signal (paper trading)"""
        logger.info(f"Executing signal: {signal.asset} {signal.action.value.upper()}")
        
        # Get current positions
        current_positions = list(self.positions.values())
        
        # Risk validation
        risk_check = self.risk_manager.validate_trade(
            signal=signal,
            balance=self.portfolio.available_balance,
            current_positions=current_positions
        )
        
        if not risk_check.approved:
            logger.warning(f"Trade rejected: {risk_check.reason}")
            return None
        
        for warning in risk_check.warnings:
            logger.warning(f"Risk warning: {warning}")
        
        # Determine position size
        position_size = custom_quantity if custom_quantity else risk_check.position_size
        
        # Simulate entry (with small slippage)
        slippage_factor = random.uniform(0.9995, 1.0005)
        entry_price = signal.entry * slippage_factor
        
        # Create trade
        is_long = signal.action in (SignalAction.LONG, SignalAction.BUY)
        trade = Trade(
            signal_id=signal.id,
            symbol=signal.asset,
            side=PositionSide.LONG if is_long else PositionSide.SHORT,
            entry_price=entry_price,
            quantity=position_size,
            leverage=signal.leverage,
            stop_loss=signal.stop_loss,
            take_profits=signal.take_profits,
            status=TradeStatus.OPEN,
            metadata={
                'risk_amount': risk_check.risk_amount,
                'risk_percent': risk_check.risk_percent,
                'signal_confidence': signal.confidence
            }
        )
        
        # Create position
        position = Position(
            symbol=signal.asset,
            side=PositionSide.LONG if is_long else PositionSide.SHORT,
            entry_price=entry_price,
            quantity=position_size,
            leverage=signal.leverage,
            current_price=entry_price,
            stop_loss=signal.stop_loss,
            take_profits=signal.take_profits
        )
        
        # Store trade and position
        self.trades[trade.id] = trade
        self.open_trades.append(trade.id)
        self.positions[signal.asset] = position
        
        # Update portfolio
        margin_required = (position_size * entry_price) / signal.leverage
        self.portfolio.margin_used += margin_required
        self.portfolio.available_balance = self.portfolio.current_balance - self.portfolio.margin_used
        self.portfolio.open_positions = len(self.positions)
        self.portfolio.total_positions_value = sum(p.quantity * p.current_price for p in self.positions.values())
        
        logger.success(f"Trade executed: {trade.id}")
        logger.info(f"   Entry: ${trade.entry_price:.2f}")
        logger.info(f"   Size: {trade.quantity:.6f}")
        logger.info(f"   SL: ${trade.stop_loss:.2f}" if trade.stop_loss else "   SL: None")
        
        return trade
    
    def close_trade(self, trade_id: str, exit_reason: ExitReason = ExitReason.MANUAL, exit_price: Optional[float] = None) -> bool:
        """Close an open trade"""
        trade = self.trades.get(trade_id)
        if not trade:
            logger.error(f"Trade not found: {trade_id}")
            return False
        
        if trade.status == TradeStatus.CLOSED:
            logger.warning(f"Trade {trade_id} already closed")
            return False
        
        position = self.positions.get(trade.symbol)
        if not position:
            logger.warning(f"No position found for {trade.symbol}")
            trade.status = TradeStatus.CLOSED
            return True
        
        # Simulate exit price (with slippage)
        if exit_price is None:
            # Use entry as base and simulate price movement
            if exit_reason == ExitReason.STOP_LOSS:
                exit_price = trade.stop_loss
            elif exit_reason == ExitReason.TAKE_PROFIT and trade.take_profits:
                exit_price = trade.take_profits[0]
            else:
                slippage = random.uniform(-0.005, 0.005)
                exit_price = trade.entry_price * (1 + slippage)
        
        # Close the trade
        trade.close(exit_price=exit_price, exit_reason=exit_reason)
        
        # Update portfolio
        self.portfolio.update_from_trade(trade)
        
        # Release margin
        margin_released = (trade.quantity * trade.entry_price) / trade.leverage
        self.portfolio.margin_used -= margin_released
        self.portfolio.available_balance = self.portfolio.current_balance - self.portfolio.margin_used
        
        # Remove position
        if trade.symbol in self.positions:
            del self.positions[trade.symbol]
        
        # Remove from open trades
        if trade_id in self.open_trades:
            self.open_trades.remove(trade_id)
        
        self.portfolio.open_positions = len(self.positions)
        
        logger.success(f"Trade closed: {trade_id}")
        logger.info(f"   Exit: ${trade.exit_price:.2f}")
        logger.info(f"   P&L: ${trade.realized_pnl:.2f} ({trade.realized_pnl_percent:.2f}%)")
        
        return True
    
    def update_prices(self, prices: Dict[str, float]):
        """Update current prices for all positions"""
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol].update_pnl(price)
        
        self.portfolio.total_positions_value = sum(p.quantity * p.current_price for p in self.positions.values())
    
    def simulate_price_update(self, symbol: str, change_percent: float = None):
        """Simulate a price update for a position"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        if change_percent is None:
            change_percent = random.uniform(-2, 2)
        
        new_price = position.current_price * (1 + change_percent / 100)
        position.update_pnl(new_price)
        
        # Check if SL/TP hit
        for trade_id in self.open_trades:
            trade = self.trades.get(trade_id)
            if trade and trade.symbol == symbol:
                if trade.side == PositionSide.LONG:
                    if trade.stop_loss and new_price <= trade.stop_loss:
                        self.close_trade(trade_id, ExitReason.STOP_LOSS, trade.stop_loss)
                    elif trade.take_profits and new_price >= trade.take_profits[0]:
                        self.close_trade(trade_id, ExitReason.TAKE_PROFIT, trade.take_profits[0])
                else:  # SHORT
                    if trade.stop_loss and new_price >= trade.stop_loss:
                        self.close_trade(trade_id, ExitReason.STOP_LOSS, trade.stop_loss)
                    elif trade.take_profits and new_price <= trade.take_profits[0]:
                        self.close_trade(trade_id, ExitReason.TAKE_PROFIT, trade.take_profits[0])
    
    def get_open_trades(self) -> List[Trade]:
        return [self.trades[tid] for tid in self.open_trades if tid in self.trades]
    
    def get_closed_trades(self) -> List[Trade]:
        return [t for t in self.trades.values() if t.status == TradeStatus.CLOSED]
    
    def get_all_trades(self) -> List[Trade]:
        return list(self.trades.values())
    
    def get_positions(self) -> List[Position]:
        return list(self.positions.values())
    
    def get_portfolio(self) -> Portfolio:
        return self.portfolio
    
    def get_statistics(self) -> Dict:
        """Get trading statistics"""
        closed_trades = self.get_closed_trades()
        winning = [t for t in closed_trades if t.realized_pnl and t.realized_pnl > 0]
        losing = [t for t in closed_trades if t.realized_pnl and t.realized_pnl < 0]
        
        total_pnl = sum(t.realized_pnl or 0 for t in closed_trades)
        unrealized_pnl = sum(p.unrealized_pnl for p in self.positions.values())
        
        avg_win = sum(t.realized_pnl for t in winning) / len(winning) if winning else 0
        avg_loss = sum(t.realized_pnl for t in losing) / len(losing) if losing else 0
        
        return {
            'total_trades': len(self.trades),
            'open_trades': len(self.open_trades),
            'closed_trades': len(closed_trades),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': (len(winning) / len(closed_trades) * 100) if closed_trades else 0,
            'total_pnl': total_pnl,
            'unrealized_pnl': unrealized_pnl,
            'combined_pnl': total_pnl + unrealized_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(sum(t.realized_pnl for t in winning) / sum(t.realized_pnl for t in losing)) if losing and sum(t.realized_pnl for t in losing) != 0 else 0,
            'current_balance': self.portfolio.current_balance,
            'available_balance': self.portfolio.available_balance,
            'margin_used': self.portfolio.margin_used
        }


# Singleton instance
trading_engine = TradingEngine()
