"""
Auto-Execute Engine for Trading AI
Automatically executes trading signals based on AI analysis and risk management.
Supports both Paper Trading and Binance Testnet execution.
"""
import asyncio
import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass

from services.ai_analyzer import AISignalAnalyzer, SignalAnalysis, SignalQuality, get_ai_analyzer
from services.trading_engine import TradingEngine

logger = logging.getLogger(__)


@dataclass
class AutoExecuteConfig:
    """Auto-execute configuration"""
    enabled: bool = False
    min_confidence: float = 0.6  # Minimum parser confidence
    min_ai_score: float = 60.0   # Minimum AI score to execute
    require_ai_approval: bool = True  # Require AI to approve
    max_daily_trades: int = 10
    allowed_sources: list = None  # None = all sources
    
    # Risk adjustments
    reduce_size_below_score: float = 70.0  # Reduce position size if score below this
    size_reduction_factor: float = 0.5     # Reduce to this factor
    
    def __post_init__(self):
        if self.allowed_sources is None:
            self.allowed_sources = ['telegram', 'telegram_channel', 'telegram_bot', 'webhook']


class AutoExecuteEngine:
    """
    Automatically executes trading signals with AI analysis.
    """
    
    def __init__(
        self,
        trading_engine: TradingEngine,
        config: AutoExecuteConfig = None,
        notification_callback: Callable = None
    ):
        self.trading_engine = trading_engine
        self.config = config or AutoExecuteConfig()
        self.notification_callback = notification_callback
        self.ai_analyzer = get_ai_analyzer()
        
        self.daily_trades = 0
        self.last_reset_date = datetime.now(timezone.utc).date()
        
        logger.info(f"AutoExecuteEngine initialized (enabled={self.config.enabled})")
    
    def update_config(self, **kwargs):
        """Update configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        logger.info(f"AutoExecute config updated: {kwargs}")
    
    async def process_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming signal through auto-execute pipeline.
        
        Returns:
            Dict with execution result and analysis
        """
        result = {
            "signal_id": signal.get('id'),
            "asset": signal.get('asset'),
            "action": signal.get('action'),
            "executed": False,
            "ai_analysis": None,
            "trade": None,
            "reason": None
        }
        
        # Reset daily counter if new day
        today = datetime.now(timezone.utc).date()
        if today != self.last_reset_date:
            self.daily_trades = 0
            self.last_reset_date = today
        
        # Check if auto-execute is enabled
        if not self.config.enabled:
            result["reason"] = "Auto-Execute deaktiviert"
            return result
        
        # Check daily limit
        if self.daily_trades >= self.config.max_daily_trades:
            result["reason"] = f"Tageslimit erreicht ({self.config.max_daily_trades})"
            await self._notify(f"⚠️ Tageslimit erreicht: {signal.get('asset')} nicht ausgeführt")
            return result
        
        # Check source
        source = signal.get('source', '')
        if self.config.allowed_sources and source not in self.config.allowed_sources:
            result["reason"] = f"Quelle '{source}' nicht erlaubt"
            return result
        
        # Check minimum confidence
        confidence = signal.get('confidence', 0)
        if confidence < self.config.min_confidence:
            result["reason"] = f"Confidence zu niedrig ({confidence*100:.0f}% < {self.config.min_confidence*100:.0f}%)"
            return result
        
        # AI Analysis
        ai_analysis = None
        if self.config.require_ai_approval and self.ai_analyzer:
            logger.info(f"Running AI analysis for {signal.get('asset')}...")
            ai_analysis = await self.ai_analyzer.analyze_signal(signal)
            result["ai_analysis"] = {
                "quality": ai_analysis.quality.value,
                "score": ai_analysis.score,
                "should_execute": ai_analysis.should_execute,
                "reasoning": ai_analysis.reasoning,
                "warnings": ai_analysis.warnings
            }
            
            # Check AI approval
            if not ai_analysis.should_execute:
                result["reason"] = f"AI Ablehnung: {ai_analysis.reasoning}"
                await self._notify(
                    f"🤖 AI hat Signal abgelehnt:\n"
                    f"Asset: {signal.get('asset')}\n"
                    f"Score: {ai_analysis.score:.0f}/100\n"
                    f"Grund: {ai_analysis.reasoning}"
                )
                return result
            
            # Check AI score
            if ai_analysis.score < self.config.min_ai_score:
                result["reason"] = f"AI Score zu niedrig ({ai_analysis.score:.0f} < {self.config.min_ai_score:.0f})"
                return result
        
        # Calculate position size
        position_size = None
        if ai_analysis and ai_analysis.score < self.config.reduce_size_below_score:
            position_size = self.config.size_reduction_factor
            logger.info(f"Reducing position size to {position_size*100:.0f}% due to low AI score")
        
        # Execute the trade
        try:
            from models.signals import Signal
            
            # Convert dict to Signal object if needed
            if not isinstance(signal, Signal):
                signal_obj = Signal(
                    id=signal.get('id'),
                    source=signal.get('source', 'auto'),
                    asset=signal.get('asset'),
                    action=signal.get('action'),
                    entry=signal.get('entry'),
                    stop_loss=signal.get('stop_loss'),
                    take_profits=signal.get('take_profits', []),
                    leverage=signal.get('leverage', 1),
                    confidence=signal.get('confidence', 0.5)
                )
            else:
                signal_obj = signal
            
            # Execute trade
            trade = self.trading_engine.execute_signal(signal_obj, position_size)
            
            if trade:
                self.daily_trades += 1
                result["executed"] = True
                result["trade"] = trade.to_dict()
                result["reason"] = "Erfolgreich ausgeführt"
                
                # Send notification
                await self._notify(
                    f"✅ Auto-Trade ausgeführt!\n\n"
                    f"📊 {trade.symbol} {trade.side.value.upper()}\n"
                    f"💰 Entry: ${trade.entry_price:,.2f}\n"
                    f"📏 Size: {trade.quantity:.6f}\n"
                    f"🛑 SL: ${trade.stop_loss:,.2f}\n"
                    f"🎯 TP: {[f'${tp:,.2f}' for tp in trade.take_profits]}\n"
                    f"⚡ Leverage: {trade.leverage}x\n\n"
                    f"🤖 AI Score: {ai_analysis.score:.0f}/100" if ai_analysis else ""
                )
                
                logger.info(f"Auto-executed trade: {trade.symbol} {trade.side.value}")
            else:
                result["reason"] = "Trade von Risk Manager abgelehnt"
                await self._notify(
                    f"⚠️ Trade abgelehnt (Risk Manager):\n"
                    f"Asset: {signal.get('asset')}"
                )
                
        except Exception as e:
            result["reason"] = f"Ausführungsfehler: {e}"
            logger.error(f"Auto-execute error: {e}")
        
        return result
    
    async def _notify(self, message: str):
        """Send notification via callback"""
        if self.notification_callback:
            try:
                await self.notification_callback(message)
            except Exception as e:
                logger.error(f"Notification failed: {e}")
    
    def get_status(self) -> Dict:
        """Get auto-execute status"""
        return {
            "enabled": self.config.enabled,
            "daily_trades": self.daily_trades,
            "max_daily_trades": self.config.max_daily_trades,
            "min_confidence": self.config.min_confidence,
            "min_ai_score": self.config.min_ai_score,
            "require_ai_approval": self.config.require_ai_approval,
            "ai_analyzer_available": self.ai_analyzer is not None
        }


# Global instance
_auto_execute_engine: Optional[AutoExecuteEngine] = None


def get_auto_execute_engine() -> Optional[AutoExecuteEngine]:
    """Get global auto-execute engine"""
    return _auto_execute_engine


def init_auto_execute_engine(
    trading_engine: TradingEngine,
    config: AutoExecuteConfig = None,
    notification_callback: Callable = None
) -> AutoExecuteEngine:
    """Initialize global auto-execute engine"""
    global _auto_execute_engine
    _auto_execute_engine = AutoExecuteEngine(
        trading_engine=trading_engine,
        config=config,
        notification_callback=notification_callback
    )
    return _auto_execute_engine
