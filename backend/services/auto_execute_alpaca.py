"""
Auto-Execute Engine for Trading AI
Automatically executes trading signals on Alpaca with proper money management.

Features:
- AI-powered signal analysis
- Risk-based position sizing
- Automatic order placement on Alpaca
- Telegram notifications
- Health monitoring and reliability
"""
import asyncio
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from enum import Enum

from services.ai_analyzer import get_ai_analyzer, SignalAnalysis, SignalQuality
from services.alpaca_broker import create_alpaca_broker, AlpacaAPIError, AlpacaBroker
from services.notification_service import get_notification_service

logger = logging.getLogger(__name__)


class ExecutionMode(str, Enum):
    PAPER = "paper"          # Local paper trading only
    ALPACA_PAPER = "alpaca_paper"  # Alpaca paper trading
    ALPACA_LIVE = "alpaca_live"    # Alpaca live trading (real money!)


@dataclass
class RiskConfig:
    """Risk management configuration"""
    max_risk_per_trade: float = 0.02      # 2% of account per trade
    max_total_risk: float = 0.10          # 10% max total exposure
    max_position_size: float = 0.20       # 20% of account per position max
    min_risk_reward: float = 1.5          # Minimum R:R ratio
    default_trade_amount: float = 100.0   # Default $ amount per trade
    scale_with_confidence: bool = True    # Scale position with AI confidence
    
    # Position sizing based on AI score
    score_multipliers: Dict[int, float] = field(default_factory=lambda: {
        90: 2.0,   # Excellent signal: 2x normal size
        80: 1.5,   # Good signal: 1.5x
        70: 1.0,   # Decent signal: normal size
        60: 0.5,   # Marginal signal: half size
    })


@dataclass 
class AutoExecuteConfig:
    """Auto-execute configuration"""
    enabled: bool = True
    mode: ExecutionMode = ExecutionMode.ALPACA_PAPER
    
    # Signal filtering
    min_confidence: float = 0.6           # Minimum parser confidence
    min_ai_score: float = 60.0            # Minimum AI score to execute
    require_ai_approval: bool = True      # Require AI to approve trade
    allowed_sources: List[str] = field(default_factory=lambda: [
        'telegram', 'telegram_channel', 'telegram_bot', 'webhook', 'rss'
    ])
    
    # Limits
    max_daily_trades: int = 10
    max_open_positions: int = 5
    cooldown_minutes: int = 5             # Cooldown between trades on same asset
    
    # Risk management
    risk: RiskConfig = field(default_factory=RiskConfig)
    
    # Notifications
    notify_on_signal: bool = True
    notify_on_trade: bool = True
    notify_on_error: bool = True


@dataclass
class TradeRecord:
    """Record of an executed trade"""
    signal_id: str
    symbol: str
    side: str
    amount: float
    order_id: str
    status: str
    ai_score: float
    timestamp: datetime
    alpaca_order: Dict = field(default_factory=dict)
    error: Optional[str] = None


class AutoExecuteEngine:
    """
    Intelligent auto-execution engine with Alpaca integration.
    
    Flow:
    1. Signal received (Telegram/RSS/Webhook)
    2. AI analysis performed
    3. Risk management check
    4. Order placed on Alpaca
    5. Notification sent
    6. Position monitored
    """
    
    def __init__(self, config: AutoExecuteConfig = None):
        self.config = config or AutoExecuteConfig()
        self.ai_analyzer = get_ai_analyzer()
        self.broker: Optional[AlpacaBroker] = None
        
        # State tracking
        self.daily_trades = 0
        self.last_reset_date = datetime.now(timezone.utc).date()
        self.trade_history: List[TradeRecord] = []
        self.last_trade_time: Dict[str, datetime] = {}  # symbol -> last trade time
        self.pending_signals: List[Dict] = []
        
        # Health monitoring
        self.last_health_check = datetime.now(timezone.utc)
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
        
        logger.info(f"AutoExecuteEngine initialized (mode={self.config.mode.value}, enabled={self.config.enabled})")
    
    async def initialize(self):
        """Initialize broker connection"""
        if self.config.mode in (ExecutionMode.ALPACA_PAPER, ExecutionMode.ALPACA_LIVE):
            paper = self.config.mode == ExecutionMode.ALPACA_PAPER
            self.broker = create_alpaca_broker(paper=paper)
            
            # Test connection
            try:
                balance = await self.broker.get_balance()
                logger.info(f"Alpaca connected. Balance: ${balance['total']:,.2f}")
            except Exception as e:
                logger.error(f"Failed to connect to Alpaca: {e}")
                raise
    
    async def process_signal(self, signal: Dict) -> Dict:
        """
        Process a trading signal through the full pipeline.
        
        Returns execution result with details.
        """
        result = {
            "signal_id": signal.get('id'),
            "asset": signal.get('asset'),
            "action": signal.get('action'),
            "executed": False,
            "order": None,
            "reason": None,
            "ai_analysis": None,
            "risk_check": None
        }
        
        # Check if enabled
        if not self.config.enabled:
            result["reason"] = "Auto-Execute deaktiviert"
            return result
        
        # Reset daily counter if needed
        self._check_daily_reset()
        
        # Pre-checks
        pre_check = self._pre_flight_checks(signal)
        if not pre_check["passed"]:
            result["reason"] = pre_check["reason"]
            await self._notify_rejection(signal, pre_check["reason"])
            return result
        
        # AI Analysis
        ai_analysis = None
        if self.config.require_ai_approval and self.ai_analyzer:
            try:
                ai_analysis = await self.ai_analyzer.analyze_signal(signal)
                result["ai_analysis"] = {
                    "score": ai_analysis.score,
                    "quality": ai_analysis.quality.value,
                    "should_execute": ai_analysis.should_execute,
                    "reasoning": ai_analysis.reasoning
                }
                
                if not ai_analysis.should_execute:
                    result["reason"] = f"AI lehnt ab (Score: {ai_analysis.score:.0f}/100)"
                    await self._notify_rejection(signal, result["reason"])
                    return result
                    
                if ai_analysis.score < self.config.min_ai_score:
                    result["reason"] = f"AI Score zu niedrig ({ai_analysis.score:.0f} < {self.config.min_ai_score})"
                    await self._notify_rejection(signal, result["reason"])
                    return result
                    
            except Exception as e:
                logger.error(f"AI analysis failed: {e}")
                if self.config.require_ai_approval:
                    result["reason"] = f"AI Analyse fehlgeschlagen: {e}"
                    return result
        
        # Risk Management Check
        risk_check = await self._check_risk_management(signal, ai_analysis)
        result["risk_check"] = risk_check
        
        if not risk_check["approved"]:
            result["reason"] = risk_check["reason"]
            await self._notify_rejection(signal, risk_check["reason"])
            return result
        
        # Execute the trade
        try:
            order_result = await self._execute_on_alpaca(
                signal=signal,
                amount=risk_check["position_size"],
                ai_analysis=ai_analysis
            )
            
            if order_result["success"]:
                self.daily_trades += 1
                self.last_trade_time[signal.get('asset', '')] = datetime.now(timezone.utc)
                self.consecutive_errors = 0
                
                result["executed"] = True
                result["order"] = order_result
                result["reason"] = "Erfolgreich auf Alpaca ausgeführt"
                
                # Record trade
                self.trade_history.append(TradeRecord(
                    signal_id=signal.get('id', ''),
                    symbol=order_result.get('symbol', ''),
                    side=signal.get('action', ''),
                    amount=risk_check["position_size"],
                    order_id=order_result.get('order_id', ''),
                    status=order_result.get('status', ''),
                    ai_score=ai_analysis.score if ai_analysis else 0,
                    timestamp=datetime.now(timezone.utc),
                    alpaca_order=order_result
                ))
                
                # Send success notification
                await self._notify_trade_executed(signal, order_result, ai_analysis)
                
            else:
                self.consecutive_errors += 1
                result["reason"] = order_result.get("error", "Unbekannter Fehler")
                await self._notify_error(signal, result["reason"])
                
        except Exception as e:
            self.consecutive_errors += 1
            logger.error(f"Trade execution failed: {e}")
            result["reason"] = f"Ausführungsfehler: {e}"
            await self._notify_error(signal, str(e))
        
        return result
    
    def _pre_flight_checks(self, signal: Dict) -> Dict:
        """Run pre-flight checks before processing"""
        # Check daily limit
        if self.daily_trades >= self.config.max_daily_trades:
            return {"passed": False, "reason": f"Tageslimit erreicht ({self.daily_trades}/{self.config.max_daily_trades})"}
        
        # Check source
        source = signal.get('source', '').lower()
        if source and self.config.allowed_sources:
            if not any(s in source for s in self.config.allowed_sources):
                return {"passed": False, "reason": f"Quelle nicht erlaubt: {source}"}
        
        # Check confidence
        confidence = signal.get('confidence', 0)
        if confidence < self.config.min_confidence:
            return {"passed": False, "reason": f"Confidence zu niedrig ({confidence:.0%} < {self.config.min_confidence:.0%})"}
        
        # Check cooldown
        asset = signal.get('asset', '')
        if asset in self.last_trade_time:
            time_since = datetime.now(timezone.utc) - self.last_trade_time[asset]
            if time_since < timedelta(minutes=self.config.cooldown_minutes):
                remaining = self.config.cooldown_minutes - (time_since.seconds // 60)
                return {"passed": False, "reason": f"Cooldown aktiv für {asset} ({remaining} min)"}
        
        # Check consecutive errors (circuit breaker)
        if self.consecutive_errors >= self.max_consecutive_errors:
            return {"passed": False, "reason": f"Circuit Breaker: {self.consecutive_errors} aufeinanderfolgende Fehler"}
        
        return {"passed": True, "reason": None}
    
    async def _check_risk_management(self, signal: Dict, ai_analysis: Optional[SignalAnalysis]) -> Dict:
        """Check risk management rules and calculate position size"""
        result = {
            "approved": False,
            "reason": None,
            "position_size": 0,
            "risk_amount": 0
        }
        
        # Get account balance
        if self.broker:
            try:
                balance = await self.broker.get_balance()
                available = balance.get('available', 0)
                total_equity = balance.get('total', 0)
            except Exception as e:
                logger.error(f"Failed to get balance: {e}")
                result["reason"] = f"Kontostand nicht verfügbar: {e}"
                return result
        else:
            available = 10000  # Default for paper trading
            total_equity = 10000
        
        # Check open positions limit
        if self.broker:
            try:
                positions = await self.broker.get_positions()
                if len(positions) >= self.config.max_open_positions:
                    result["reason"] = f"Max. Positionen erreicht ({len(positions)}/{self.config.max_open_positions})"
                    return result
            except:
                pass
        
        # Calculate position size based on risk
        risk_config = self.config.risk
        
        # Base position size
        base_amount = risk_config.default_trade_amount
        
        # Scale with AI score if enabled
        if risk_config.scale_with_confidence and ai_analysis:
            score = ai_analysis.score
            multiplier = 1.0
            
            for threshold, mult in sorted(risk_config.score_multipliers.items(), reverse=True):
                if score >= threshold:
                    multiplier = mult
                    break
            
            base_amount *= multiplier
            logger.info(f"Position scaled by {multiplier}x based on AI score {score}")
        
        # Apply max position size limit
        max_position = total_equity * risk_config.max_position_size
        position_size = min(base_amount, max_position)
        
        # Check R:R ratio if we have entry, SL, TP
        entry = signal.get('entry', 0)
        stop_loss = signal.get('stop_loss', 0)
        take_profits = signal.get('take_profits', [])
        
        if entry and stop_loss and take_profits:
            risk = abs(entry - stop_loss)
            reward = abs(take_profits[0] - entry) if take_profits else risk
            
            if risk > 0:
                rr_ratio = reward / risk
                if rr_ratio < risk_config.min_risk_reward:
                    result["reason"] = f"R:R Ratio zu niedrig ({rr_ratio:.2f} < {risk_config.min_risk_reward})"
                    return result
        
        # Ensure minimum size
        position_size = max(position_size, 10)  # Minimum $10
        
        result["approved"] = True
        result["position_size"] = round(position_size, 2)
        result["risk_amount"] = round(position_size * risk_config.max_risk_per_trade, 2)
        
        return result
    
    async def _execute_on_alpaca(self, signal: Dict, amount: float, ai_analysis: Optional[SignalAnalysis]) -> Dict:
        """Execute trade on Alpaca"""
        result = {
            "success": False,
            "order_id": None,
            "symbol": None,
            "side": None,
            "amount": amount,
            "status": None,
            "error": None
        }
        
        if not self.broker:
            await self.initialize()
        
        # Convert symbol for Alpaca
        symbol = signal.get('asset', '').replace('/', '').replace('USDT', 'USD')
        side = 'buy' if signal.get('action', '').lower() in ['long', 'buy'] else 'sell'
        
        result["symbol"] = symbol
        result["side"] = side
        
        try:
            # Check if asset is tradable
            try:
                asset_info = await self.broker.get_asset(symbol)
                if not asset_info.get('tradable'):
                    result["error"] = f"{symbol} nicht handelbar auf Alpaca"
                    return result
            except AlpacaAPIError:
                # Try stock symbol without USD
                if symbol.endswith('USD'):
                    symbol = symbol[:-3]
                    result["symbol"] = symbol
            
            # Place market order with notional amount
            order = await self.broker.place_market_order(
                symbol=symbol,
                side=side,
                notional=amount,
                time_in_force='gtc'
            )
            
            result["success"] = True
            result["order_id"] = order.get('order_id')
            result["status"] = order.get('status')
            result["filled_qty"] = order.get('filled_quantity')
            result["avg_price"] = order.get('avg_fill_price')
            
            logger.info(f"Order placed: {symbol} {side} ${amount} -> {order.get('status')}")
            
        except AlpacaAPIError as e:
            result["error"] = str(e)
            logger.error(f"Alpaca order failed: {e}")
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Order execution failed: {e}")
        
        return result
    
    async def _notify_trade_executed(self, signal: Dict, order: Dict, ai_analysis: Optional[SignalAnalysis]):
        """Send notification for executed trade"""
        if not self.config.notify_on_trade:
            return
        
        notifier = get_notification_service()
        if not notifier:
            return
        
        score_text = f"🤖 AI Score: {ai_analysis.score:.0f}/100" if ai_analysis else ""
        
        message = f"""✅ <b>Auto-Trade ausgeführt!</b>

📊 <b>Asset:</b> {order.get('symbol')}
📈 <b>Richtung:</b> {order.get('side', '').upper()}
💰 <b>Betrag:</b> ${order.get('amount', 0):,.2f}
📋 <b>Status:</b> {order.get('status')}
🔢 <b>Order ID:</b> <code>{order.get('order_id', '')[:8]}...</code>

{score_text}

<i>Quelle: {signal.get('source', 'Unknown')}</i>"""
        
        await notifier.send(message)
    
    async def _notify_rejection(self, signal: Dict, reason: str):
        """Send notification for rejected signal"""
        if not self.config.notify_on_signal:
            return
        
        notifier = get_notification_service()
        if not notifier:
            return
        
        message = f"""⚠️ <b>Signal abgelehnt</b>

📊 <b>Asset:</b> {signal.get('asset')}
📈 <b>Richtung:</b> {signal.get('action', '').upper()}
❌ <b>Grund:</b> {reason}

<i>Quelle: {signal.get('source', 'Unknown')}</i>"""
        
        await notifier.send(message)
    
    async def _notify_error(self, signal: Dict, error: str):
        """Send notification for error"""
        if not self.config.notify_on_error:
            return
        
        notifier = get_notification_service()
        if not notifier:
            return
        
        message = f"""🚨 <b>Auto-Execute Fehler</b>

📊 <b>Asset:</b> {signal.get('asset')}
❌ <b>Fehler:</b> {error}

<i>Consecutive Errors: {self.consecutive_errors}/{self.max_consecutive_errors}</i>"""
        
        await notifier.send(message)
    
    def _check_daily_reset(self):
        """Reset daily counter if new day"""
        today = datetime.now(timezone.utc).date()
        if today > self.last_reset_date:
            self.daily_trades = 0
            self.last_reset_date = today
            logger.info("Daily trade counter reset")
    
    def update_config(self, **kwargs):
        """Update configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Config updated: {key} = {value}")
    
    def get_status(self) -> Dict:
        """Get current status"""
        return {
            "enabled": self.config.enabled,
            "mode": self.config.mode.value,
            "daily_trades": self.daily_trades,
            "max_daily_trades": self.config.max_daily_trades,
            "min_ai_score": self.config.min_ai_score,
            "min_confidence": self.config.min_confidence,
            "require_ai_approval": self.config.require_ai_approval,
            "max_open_positions": self.config.max_open_positions,
            "consecutive_errors": self.consecutive_errors,
            "ai_analyzer_available": self.ai_analyzer is not None,
            "broker_connected": self.broker is not None,
            "risk_config": {
                "max_risk_per_trade": self.config.risk.max_risk_per_trade,
                "default_trade_amount": self.config.risk.default_trade_amount,
                "scale_with_confidence": self.config.risk.scale_with_confidence
            },
            "recent_trades": len(self.trade_history),
            "last_trade": self.trade_history[-1].timestamp.isoformat() if self.trade_history else None
        }
    
    def get_trade_history(self, limit: int = 20) -> List[Dict]:
        """Get recent trade history"""
        return [
            {
                "signal_id": t.signal_id,
                "symbol": t.symbol,
                "side": t.side,
                "amount": t.amount,
                "order_id": t.order_id,
                "status": t.status,
                "ai_score": t.ai_score,
                "timestamp": t.timestamp.isoformat(),
                "error": t.error
            }
            for t in self.trade_history[-limit:]
        ]
    
    async def health_check(self) -> Dict:
        """Perform health check"""
        status = {
            "healthy": True,
            "checks": {}
        }
        
        # Check AI analyzer
        status["checks"]["ai_analyzer"] = self.ai_analyzer is not None
        
        # Check broker connection
        if self.broker:
            try:
                await self.broker.get_balance()
                status["checks"]["broker"] = True
            except:
                status["checks"]["broker"] = False
                status["healthy"] = False
        else:
            status["checks"]["broker"] = False
            if self.config.mode != ExecutionMode.PAPER:
                status["healthy"] = False
        
        # Check consecutive errors
        status["checks"]["error_threshold"] = self.consecutive_errors < self.max_consecutive_errors
        if not status["checks"]["error_threshold"]:
            status["healthy"] = False
        
        self.last_health_check = datetime.now(timezone.utc)
        
        return status
    
    async def close(self):
        """Close connections"""
        if self.broker:
            await self.broker.close()


# Global instance
_auto_execute_engine: Optional[AutoExecuteEngine] = None


def get_auto_execute_engine() -> Optional[AutoExecuteEngine]:
    """Get global auto-execute engine"""
    return _auto_execute_engine


async def init_auto_execute_engine(config: AutoExecuteConfig = None) -> AutoExecuteEngine:
    """Initialize global auto-execute engine"""
    global _auto_execute_engine
    _auto_execute_engine = AutoExecuteEngine(config)
    await _auto_execute_engine.initialize()
    return _auto_execute_engine


# Legacy compatibility
def init_auto_execute_engine_sync(trading_engine=None, config=None, notification_callback=None) -> AutoExecuteEngine:
    """Sync init for backwards compatibility"""
    global _auto_execute_engine
    
    # Convert old config to new
    new_config = AutoExecuteConfig(
        enabled=config.enabled if config else True,
        mode=ExecutionMode.ALPACA_PAPER,
        min_confidence=config.min_confidence if config else 0.6,
        min_ai_score=config.min_ai_score if config else 60.0,
        require_ai_approval=config.require_ai_approval if config else True,
        max_daily_trades=config.max_daily_trades if config else 10,
    )
    
    _auto_execute_engine = AutoExecuteEngine(new_config)
    return _auto_execute_engine
