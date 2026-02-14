"""
Trading AI - Simplified Server
Clean, efficient trading system with Alpaca integration.
"""
import asyncio
import os
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Services
from services.alpaca_broker import create_alpaca_broker, AlpacaAPIError
from services.telegram_bot import init_telegram_bot, get_telegram_bot
from services.telegram_channel_monitor import init_channel_monitor, get_channel_monitor
from services.ai_analyzer import get_ai_analyzer, init_ai_analyzer
from services.notification_service import init_notification_service, get_notification_service

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('server')

# FastAPI App
app = FastAPI(title="Trading AI", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'trading_ai')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Global state
telegram_bot_task = None
channel_monitor_task = None

# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    """Global configuration"""
    # Trading mode
    use_live_trading: bool = os.environ.get('ALPACA_LIVE', 'false').lower() == 'true'
    
    # Auto-execute settings
    auto_execute_enabled: bool = True
    min_win_probability: float = 0.70  # 70% minimum to execute
    default_trade_amount: float = 100.0  # $100 per trade
    max_daily_trades: int = 10
    max_open_positions: int = 5
    
    # Notification chat ID
    telegram_chat_id: int = 8202282349

config = Config()

# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class SignalCreate(BaseModel):
    asset: str
    action: str  # long/short
    entry: float
    stop_loss: Optional[float] = None
    take_profits: Optional[List[float]] = []
    confidence: Optional[float] = 0.7
    source: Optional[str] = "manual"

class TradeExecute(BaseModel):
    signal_id: str

class ConfigUpdate(BaseModel):
    auto_execute_enabled: Optional[bool] = None
    min_win_probability: Optional[float] = None
    default_trade_amount: Optional[float] = None
    use_live_trading: Optional[bool] = None

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_broker():
    """Get Alpaca broker (paper or live based on config)"""
    return create_alpaca_broker(paper=not config.use_live_trading)

async def analyze_signal_quality(signal: dict) -> dict:
    """Quick signal quality analysis - returns win probability"""
    analyzer = get_ai_analyzer()
    
    if not analyzer:
        # Fallback: use confidence as probability
        return {
            "win_probability": signal.get('confidence', 0.5),
            "recommendation": "execute" if signal.get('confidence', 0) >= 0.7 else "skip",
            "reason": "AI nicht verfügbar - nutze Signal-Confidence"
        }
    
    try:
        analysis = await analyzer.analyze_signal(signal)
        win_prob = analysis.score / 100  # Convert 0-100 to 0-1
        
        return {
            "win_probability": win_prob,
            "score": analysis.score,
            "quality": analysis.quality.value,
            "recommendation": "execute" if analysis.should_execute else "skip",
            "reason": analysis.reasoning[:100] if analysis.reasoning else ""
        }
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return {
            "win_probability": signal.get('confidence', 0.5),
            "recommendation": "skip",
            "reason": f"Analyse-Fehler: {str(e)[:50]}"
        }

async def execute_on_alpaca(signal: dict, amount: float) -> dict:
    """Execute trade on Alpaca"""
    broker = get_broker()
    
    try:
        # Convert symbol (BTC/USDT -> BTCUSD)
        symbol = signal['asset'].replace('/', '').replace('USDT', 'USD')
        side = 'buy' if signal['action'].lower() in ['long', 'buy'] else 'sell'
        
        # Check if tradable
        try:
            asset_info = await broker.get_asset(symbol)
            if not asset_info.get('tradable'):
                # Try without USD
                if symbol.endswith('USD'):
                    symbol = symbol[:-3]
        except:
            if symbol.endswith('USD'):
                symbol = symbol[:-3]
        
        # Place order
        order = await broker.place_market_order(
            symbol=symbol,
            side=side,
            notional=amount,
            time_in_force='gtc'
        )
        
        await broker.close()
        
        return {
            "success": True,
            "order_id": order.get('order_id'),
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "status": order.get('status')
        }
        
    except AlpacaAPIError as e:
        await broker.close()
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def send_notification(message: str):
    """Send Telegram notification"""
    notifier = get_notification_service()
    if notifier:
        await notifier.send(message)

# =============================================================================
# API ROUTES
# =============================================================================

@app.get("/api/")
async def root():
    return {"message": "Trading AI v2.0", "status": "running"}

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "mode": "LIVE" if config.use_live_trading else "PAPER",
        "auto_execute": config.auto_execute_enabled
    }

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    return {
        "auto_execute_enabled": config.auto_execute_enabled,
        "min_win_probability": config.min_win_probability,
        "default_trade_amount": config.default_trade_amount,
        "max_daily_trades": config.max_daily_trades,
        "max_open_positions": config.max_open_positions,
        "use_live_trading": config.use_live_trading,
        "mode": "LIVE" if config.use_live_trading else "PAPER"
    }

@app.put("/api/config")
async def update_config(update: ConfigUpdate):
    """Update configuration"""
    if update.auto_execute_enabled is not None:
        config.auto_execute_enabled = update.auto_execute_enabled
    if update.min_win_probability is not None:
        config.min_win_probability = update.min_win_probability
    if update.default_trade_amount is not None:
        config.default_trade_amount = update.default_trade_amount
    if update.use_live_trading is not None:
        config.use_live_trading = update.use_live_trading
        # Update environment for persistence
        mode = "LIVE" if update.use_live_trading else "PAPER"
        await send_notification(f"⚠️ Trading-Modus gewechselt: <b>{mode}</b>")
    
    return await get_config()

@app.post("/api/config/toggle-live")
async def toggle_live_trading():
    """Toggle between Paper and Live trading"""
    config.use_live_trading = not config.use_live_trading
    mode = "LIVE 🔴" if config.use_live_trading else "PAPER 🟡"
    
    await send_notification(f"⚠️ Trading-Modus: <b>{mode}</b>")
    
    return {
        "use_live_trading": config.use_live_trading,
        "mode": "LIVE" if config.use_live_trading else "PAPER"
    }

# -----------------------------------------------------------------------------
# BROKER / ALPACA
# -----------------------------------------------------------------------------

@app.get("/api/broker/balance")
async def get_balance():
    """Get Alpaca account balance"""
    try:
        broker = get_broker()
        balance = await broker.get_balance()
        await broker.close()
        return {
            **balance,
            "mode": "LIVE" if config.use_live_trading else "PAPER"
        }
    except AlpacaAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/broker/positions")
async def get_positions():
    """Get open positions"""
    try:
        broker = get_broker()
        positions = await broker.get_positions()
        await broker.close()
        return {"positions": positions, "count": len(positions)}
    except AlpacaAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/broker/orders")
async def get_orders(status: str = "open"):
    """Get orders"""
    try:
        broker = get_broker()
        orders = await broker.get_orders(status)
        await broker.close()
        return {"orders": orders, "count": len(orders)}
    except AlpacaAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/broker/position/{symbol}")
async def close_position(symbol: str):
    """Close a position"""
    try:
        broker = get_broker()
        result = await broker.close_position(symbol)
        await broker.close()
        
        if result:
            await send_notification(f"📤 Position geschlossen: <b>{symbol}</b>")
            return result
        raise HTTPException(status_code=404, detail="Position not found")
    except AlpacaAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))

# -----------------------------------------------------------------------------
# SIGNALS
# -----------------------------------------------------------------------------

@app.get("/api/signals")
async def get_signals(executed: bool = None, limit: int = 50):
    """Get signals"""
    query = {}
    if executed is not None:
        query["executed"] = executed
    
    signals = await db.signals.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return signals

@app.post("/api/signals")
async def create_signal(signal: SignalCreate):
    """Create a new signal"""
    signal_dict = {
        "id": str(uuid.uuid4()),
        "asset": signal.asset,
        "action": signal.action,
        "entry": signal.entry,
        "stop_loss": signal.stop_loss,
        "take_profits": signal.take_profits or [],
        "confidence": signal.confidence or 0.7,
        "source": signal.source or "manual",
        "executed": False,
        "dismissed": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.signals.insert_one(signal_dict)
    
    # Notify
    await send_notification(
        f"📊 <b>Neues Signal</b>\n\n"
        f"Asset: {signal.asset}\n"
        f"Richtung: {signal.action.upper()}\n"
        f"Entry: ${signal.entry:,.2f}\n"
        f"Confidence: {signal.confidence:.0%}"
    )
    
    # Auto-analyze and possibly execute
    if config.auto_execute_enabled:
        asyncio.create_task(auto_process_signal(signal_dict))
    
    return signal_dict

@app.delete("/api/signals/{signal_id}")
async def dismiss_signal(signal_id: str):
    """Dismiss a signal"""
    result = await db.signals.update_one(
        {"id": signal_id},
        {"$set": {"dismissed": True}}
    )
    return {"success": result.modified_count > 0}

# -----------------------------------------------------------------------------
# TRADES
# -----------------------------------------------------------------------------

@app.post("/api/trades/execute")
async def execute_trade(trade: TradeExecute):
    """Execute a trade from a signal"""
    # Get signal
    signal = await db.signals.find_one({"id": trade.signal_id}, {"_id": 0})
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    if signal.get("executed"):
        raise HTTPException(status_code=400, detail="Signal already executed")
    
    # Analyze
    analysis = await analyze_signal_quality(signal)
    
    # Execute on Alpaca
    result = await execute_on_alpaca(signal, config.default_trade_amount)
    
    if result["success"]:
        # Mark as executed
        await db.signals.update_one(
            {"id": trade.signal_id},
            {"$set": {"executed": True, "analysis": analysis}}
        )
        
        # Save trade
        trade_record = {
            "id": str(uuid.uuid4()),
            "signal_id": trade.signal_id,
            "order_id": result["order_id"],
            "symbol": result["symbol"],
            "side": result["side"],
            "amount": result["amount"],
            "status": result["status"],
            "win_probability": analysis["win_probability"],
            "mode": "LIVE" if config.use_live_trading else "PAPER",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.trades.insert_one(trade_record)
        
        # Notify
        mode = "🔴 LIVE" if config.use_live_trading else "🟡 PAPER"
        await send_notification(
            f"✅ <b>Trade ausgeführt!</b> {mode}\n\n"
            f"📊 {result['symbol']} {result['side'].upper()}\n"
            f"💰 ${result['amount']:.2f}\n"
            f"📈 Win-Prob: {analysis['win_probability']:.0%}\n"
            f"📋 Order: <code>{result['order_id'][:8]}...</code>"
        )
        
        return {**result, "analysis": analysis, "mode": "LIVE" if config.use_live_trading else "PAPER"}
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Trade failed"))

@app.get("/api/trades")
async def get_trades(limit: int = 50):
    """Get trade history"""
    trades = await db.trades.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return trades

# -----------------------------------------------------------------------------
# TELEGRAM
# -----------------------------------------------------------------------------

@app.get("/api/telegram/status")
async def get_telegram_status():
    """Get Telegram bot and channel monitor status"""
    bot = get_telegram_bot()
    monitor = get_channel_monitor()
    
    return {
        "bot": {
            "running": bot is not None and bot.running if bot else False,
            "username": bot.bot_username if bot else None
        },
        "channel_monitor": {
            "running": monitor is not None and monitor.running if monitor else False,
            "channels": len(monitor.channel_ids) if monitor else 0
        }
    }

# -----------------------------------------------------------------------------
# AUTO-PROCESS
# -----------------------------------------------------------------------------

async def auto_process_signal(signal: dict):
    """Auto-process a signal: analyze and execute if good enough"""
    try:
        # Quick analysis
        analysis = await analyze_signal_quality(signal)
        
        logger.info(f"Signal {signal['asset']}: Win-Prob {analysis['win_probability']:.0%}")
        
        # Check if should execute
        if analysis['win_probability'] >= config.min_win_probability:
            # Check position limits
            broker = get_broker()
            positions = await broker.get_positions()
            await broker.close()
            
            if len(positions) >= config.max_open_positions:
                await send_notification(
                    f"⚠️ Signal übersprungen: Max. Positionen erreicht\n"
                    f"Asset: {signal['asset']}"
                )
                return
            
            # Execute
            result = await execute_on_alpaca(signal, config.default_trade_amount)
            
            if result["success"]:
                await db.signals.update_one(
                    {"id": signal["id"]},
                    {"$set": {"executed": True, "analysis": analysis}}
                )
                
                # Save trade
                trade_record = {
                    "id": str(uuid.uuid4()),
                    "signal_id": signal["id"],
                    "order_id": result["order_id"],
                    "symbol": result["symbol"],
                    "side": result["side"],
                    "amount": result["amount"],
                    "status": result["status"],
                    "win_probability": analysis["win_probability"],
                    "mode": "LIVE" if config.use_live_trading else "PAPER",
                    "auto_executed": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.trades.insert_one(trade_record)
                
                mode = "🔴 LIVE" if config.use_live_trading else "🟡 PAPER"
                await send_notification(
                    f"🤖 <b>Auto-Trade!</b> {mode}\n\n"
                    f"📊 {result['symbol']} {result['side'].upper()}\n"
                    f"💰 ${result['amount']:.2f}\n"
                    f"📈 Win-Prob: {analysis['win_probability']:.0%}\n"
                    f"✨ Automatisch ausgeführt"
                )
            else:
                await send_notification(
                    f"❌ Auto-Trade fehlgeschlagen\n"
                    f"Asset: {signal['asset']}\n"
                    f"Fehler: {result.get('error', 'Unknown')}"
                )
        else:
            await send_notification(
                f"⏭️ Signal übersprungen\n\n"
                f"Asset: {signal['asset']}\n"
                f"Win-Prob: {analysis['win_probability']:.0%} (min: {config.min_win_probability:.0%})\n"
                f"Grund: {analysis.get('reason', 'Zu niedrige Wahrscheinlichkeit')}"
            )
            
    except Exception as e:
        logger.error(f"Auto-process error: {e}")

# -----------------------------------------------------------------------------
# TELEGRAM SIGNAL CALLBACK
# -----------------------------------------------------------------------------

async def telegram_signal_callback(signal_data: dict):
    """Called when a signal is received from Telegram"""
    logger.info(f"Telegram signal: {signal_data.get('asset')} {signal_data.get('action')}")
    
    signal_dict = {
        "id": str(uuid.uuid4()),
        "asset": signal_data.get('asset', ''),
        "action": signal_data.get('action', ''),
        "entry": signal_data.get('entry', 0),
        "stop_loss": signal_data.get('stop_loss'),
        "take_profits": signal_data.get('take_profits', []),
        "confidence": signal_data.get('confidence', 0.7),
        "source": signal_data.get('source', 'telegram'),
        "executed": False,
        "dismissed": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": signal_data.get('metadata', {})
    }
    
    await db.signals.insert_one(signal_dict)
    
    # Auto-process
    if config.auto_execute_enabled:
        await auto_process_signal(signal_dict)

# -----------------------------------------------------------------------------
# STARTUP / SHUTDOWN
# -----------------------------------------------------------------------------

@app.on_event("startup")
async def startup():
    global telegram_bot_task, channel_monitor_task
    
    logger.info("Trading AI v2.0 starting...")
    
    # Initialize AI analyzer
    init_ai_analyzer()
    logger.info("AI Analyzer initialized")
    
    # Initialize Telegram bot
    bot = await init_telegram_bot(telegram_signal_callback)
    if bot:
        telegram_bot_task = asyncio.create_task(bot.start_polling())
        logger.info(f"Telegram bot started: @{bot.bot_username}")
    
    # Initialize notification service
    notifier = init_notification_service(bot, chat_ids=[config.telegram_chat_id])
    logger.info("Notification service initialized")
    
    # Initialize channel monitor
    monitor = await init_channel_monitor(telegram_signal_callback)
    if monitor:
        try:
            if await monitor.client.is_user_authorized():
                channel_monitor_task = asyncio.create_task(monitor.start_monitoring())
                logger.info("Channel monitor started")
        except Exception as e:
            logger.warning(f"Channel monitor: {e}")
    
    # Test Alpaca connection
    try:
        broker = get_broker()
        balance = await broker.get_balance()
        await broker.close()
        mode = "LIVE" if config.use_live_trading else "PAPER"
        logger.info(f"Alpaca connected ({mode}): ${balance['total']:,.2f}")
    except Exception as e:
        logger.error(f"Alpaca connection failed: {e}")
    
    logger.info("Trading AI v2.0 ready!")

@app.on_event("shutdown")
async def shutdown():
    global telegram_bot_task, channel_monitor_task
    
    bot = get_telegram_bot()
    if bot:
        await bot.stop()
    if telegram_bot_task:
        telegram_bot_task.cancel()
    
    monitor = get_channel_monitor()
    if monitor:
        await monitor.stop()
    if channel_monitor_task:
        channel_monitor_task.cancel()
    
    client.close()
    logger.info("Trading AI shutdown complete")

# Run with: uvicorn server:app --host 0.0.0.0 --port 8001
