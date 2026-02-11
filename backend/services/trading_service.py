"""
Trading Service for Trading AI
Handles trade execution on both Paper Trading and Binance Testnet.
"""
import asyncio
import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from services.binance_broker import create_binance_broker, BinanceBroker, BinanceAPIError
from services.notification_service import get_notification_service

logger = logging.getLogger(__name__)


class TradingMode(str, Enum):
    PAPER = "paper"
    BINANCE_TESTNET = "binance_testnet"
    BINANCE_LIVE = "binance_live"


@dataclass
class TradeResult:
    """Result of a trade execution"""
    success: bool
    trade_id: Optional[str] = None
    order_id: Optional[int] = None
    symbol: str = ""
    side: str = ""
    quantity: float = 0.0
    entry_price: float = 0.0
    stop_loss_order_id: Optional[int] = None
    take_profit_order_id: Optional[int] = None
    error: Optional[str] = None
    mode: TradingMode = TradingMode.PAPER


class TradingService:
    """
    Unified Trading Service that can execute on Paper or Binance.
    """
    
    def __init__(self, mode: TradingMode = TradingMode.BINANCE_TESTNET):
        self.mode = mode
        self.broker: Optional[BinanceBroker] = None
        self.active_orders: Dict[str, List[int]] = {}  # symbol -> order_ids
        
        logger.info(f"TradingService initialized in {mode.value} mode")
    
    async def initialize(self):
        """Initialize the broker connection"""
        if self.mode in (TradingMode.BINANCE_TESTNET, TradingMode.BINANCE_LIVE):
            testnet = self.mode == TradingMode.BINANCE_TESTNET
            self.broker = create_binance_broker(testnet=testnet)
            
            # Test connection
            try:
                balance = await self.broker.get_balance()
                logger.info(f"Binance {'Testnet' if testnet else 'Live'} connected. Balance: ${balance['available']:,.2f}")
            except Exception as e:
                logger.error(f"Failed to connect to Binance: {e}")
                raise
    
    async def execute_signal(
        self,
        signal: Dict[str, Any],
        position_size: Optional[float] = None,
        ai_analysis: Optional[Dict] = None
    ) -> TradeResult:
        """
        Execute a trading signal on Binance Testnet.
        
        Args:
            signal: Signal dict with asset, action, entry, stop_loss, take_profits, leverage
            position_size: Override position size (in base currency units)
            ai_analysis: AI analysis result for logging
        
        Returns:
            TradeResult with execution details
        """
        symbol = signal.get('asset', '').replace('/', '')
        action = signal.get('action', 'long').lower()
        entry = signal.get('entry', 0)
        stop_loss = signal.get('stop_loss', 0)
        take_profits = signal.get('take_profits', [])
        leverage = signal.get('leverage', 1)
        
        logger.info(f"Executing signal: {symbol} {action.upper()}")
        logger.info(f"  Entry: ${entry:,.2f}, SL: ${stop_loss:,.2f}, Leverage: {leverage}x")
        
        if self.mode == TradingMode.PAPER:
            # Paper trading - just log
            return TradeResult(
                success=True,
                trade_id=f"paper_{datetime.now().timestamp()}",
                symbol=symbol,
                side=action,
                quantity=position_size or 0.01,
                entry_price=entry,
                mode=TradingMode.PAPER
            )
        
        # Binance execution
        if not self.broker:
            await self.initialize()
        
        try:
            # 1. Set leverage
            try:
                await self.broker.set_leverage(symbol, leverage)
            except BinanceAPIError as e:
                if e.code != -4028:  # Ignore "no change" error
                    logger.warning(f"Leverage warning: {e}")
            
            # 2. Calculate position size if not provided
            if not position_size:
                balance = await self.broker.get_balance()
                available = balance['available']
                # Risk 2% of account per trade
                risk_amount = available * 0.02
                # Position size based on stop loss distance
                sl_distance = abs(entry - stop_loss)
                if sl_distance > 0:
                    position_size = (risk_amount * leverage) / sl_distance
                else:
                    position_size = (risk_amount * leverage) / entry * 100  # 1% of entry as fallback
                
                # Round to appropriate precision
                position_size = self._round_quantity(symbol, position_size)
            
            logger.info(f"  Position size: {position_size}")
            
            # 3. Place market order
            side = 'BUY' if action in ('long', 'buy') else 'SELL'
            order_result = await self.broker.place_market_order(
                symbol=symbol,
                side=side,
                quantity=position_size
            )
            
            entry_price = order_result.get('avg_price') or entry
            order_id = order_result.get('order_id')
            
            logger.info(f"  Market order filled: {order_id} @ ${entry_price:,.2f}")
            
            # 4. Place stop loss
            sl_order_id = None
            if stop_loss:
                sl_side = 'SELL' if side == 'BUY' else 'BUY'
                try:
                    sl_result = await self.broker.place_stop_loss(
                        symbol=symbol,
                        side=sl_side,
                        quantity=position_size,
                        stop_price=stop_loss
                    )
                    sl_order_id = sl_result.get('order_id')
                    logger.info(f"  Stop loss placed: {sl_order_id} @ ${stop_loss:,.2f}")
                except BinanceAPIError as e:
                    logger.warning(f"  Stop loss failed: {e}")
            
            # 5. Place take profit (first target only)
            tp_order_id = None
            if take_profits:
                tp_side = 'SELL' if side == 'BUY' else 'BUY'
                try:
                    tp_result = await self.broker.place_take_profit(
                        symbol=symbol,
                        side=tp_side,
                        quantity=position_size,
                        take_profit_price=take_profits[0]
                    )
                    tp_order_id = tp_result.get('order_id')
                    logger.info(f"  Take profit placed: {tp_order_id} @ ${take_profits[0]:,.2f}")
                except BinanceAPIError as e:
                    logger.warning(f"  Take profit failed: {e}")
            
            # Store active orders
            self.active_orders[symbol] = [o for o in [order_id, sl_order_id, tp_order_id] if o]
            
            # Send notification
            notifier = get_notification_service()
            if notifier:
                await notifier.send_trade_executed({
                    'symbol': symbol,
                    'side': action,
                    'entry_price': entry_price,
                    'quantity': position_size,
                    'leverage': leverage,
                    'stop_loss': stop_loss,
                    'take_profits': take_profits
                })
            
            return TradeResult(
                success=True,
                trade_id=f"binance_{order_id}",
                order_id=order_id,
                symbol=symbol,
                side=action,
                quantity=position_size,
                entry_price=entry_price,
                stop_loss_order_id=sl_order_id,
                take_profit_order_id=tp_order_id,
                mode=self.mode
            )
            
        except BinanceAPIError as e:
            logger.error(f"Binance execution failed: {e}")
            return TradeResult(
                success=False,
                symbol=symbol,
                side=action,
                error=str(e),
                mode=self.mode
            )
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return TradeResult(
                success=False,
                symbol=symbol,
                side=action,
                error=str(e),
                mode=self.mode
            )
    
    async def close_position(self, symbol: str) -> TradeResult:
        """Close an open position"""
        if self.mode == TradingMode.PAPER:
            return TradeResult(success=True, symbol=symbol, mode=TradingMode.PAPER)
        
        if not self.broker:
            await self.initialize()
        
        try:
            # Cancel all open orders for this symbol
            if symbol in self.active_orders:
                try:
                    await self.broker.cancel_all_orders(symbol)
                    logger.info(f"Cancelled all orders for {symbol}")
                except BinanceAPIError:
                    pass
            
            # Close position
            result = await self.broker.close_position(symbol)
            
            if result:
                # Send notification
                notifier = get_notification_service()
                if notifier:
                    await notifier.send_trade_closed({
                        'symbol': symbol,
                        'entry_price': result.get('avg_price', 0),
                        'exit_price': result.get('avg_price', 0),
                        'exit_reason': 'Manual'
                    })
                
                return TradeResult(
                    success=True,
                    order_id=result.get('order_id'),
                    symbol=symbol,
                    mode=self.mode
                )
            
            return TradeResult(
                success=False,
                symbol=symbol,
                error="No position found",
                mode=self.mode
            )
            
        except BinanceAPIError as e:
            return TradeResult(
                success=False,
                symbol=symbol,
                error=str(e),
                mode=self.mode
            )
    
    async def get_positions(self) -> List[Dict]:
        """Get all open positions"""
        if self.mode == TradingMode.PAPER:
            return []
        
        if not self.broker:
            await self.initialize()
        
        return await self.broker.get_positions()
    
    async def get_balance(self) -> Dict:
        """Get account balance"""
        if self.mode == TradingMode.PAPER:
            return {'total': 10000, 'available': 10000}
        
        if not self.broker:
            await self.initialize()
        
        return await self.broker.get_balance()
    
    def _round_quantity(self, symbol: str, quantity: float) -> float:
        """Round quantity to appropriate precision for symbol"""
        # Common precision rules for Binance Futures
        precision_map = {
            'BTCUSDT': 3,
            'ETHUSDT': 3,
            'SOLUSDT': 0,
            'XRPUSDT': 0,
            'DOGEUSDT': 0,
            'BNBUSDT': 2,
        }
        
        precision = precision_map.get(symbol.replace('/', ''), 3)
        return round(quantity, precision)
    
    async def close(self):
        """Close broker connection"""
        if self.broker:
            await self.broker.close()


# Global instance
_trading_service: Optional[TradingService] = None


def get_trading_service() -> Optional[TradingService]:
    """Get global trading service"""
    return _trading_service


async def init_trading_service(mode: TradingMode = TradingMode.BINANCE_TESTNET) -> TradingService:
    """Initialize global trading service"""
    global _trading_service
    _trading_service = TradingService(mode)
    await _trading_service.initialize()
    return _trading_service
