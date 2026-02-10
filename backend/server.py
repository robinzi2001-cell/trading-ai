"""
Trading AI Backend Server
FastAPI backend for automated trading signal processing and execution.
"""
from fastapi import FastAPI, APIRouter, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone
import asyncio
import os
import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from models.signals import Signal, SignalSource, SignalCreate, SignalWebhook, ParsedSignal
from models.trading import Trade, Position, Portfolio, TradeCreate, TradeClose, TradeStatus, ExitReason, PositionSide
from models.settings import TradingSettings, RiskSettings, SettingsUpdate
from services.signal_parser import SignalParser
from services.risk_manager import RiskManager
from services.trading_engine import TradingEngine
from services.telegram_listener import TelegramSignalParser, KNOWN_CHANNELS
from services.binance_broker import create_binance_broker, BinanceAPIError
from services.telegram_bot import init_telegram_bot, get_telegram_bot
from services.telegram_channel_monitor import init_channel_monitor, get_channel_monitor

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize services
signal_parser = SignalParser()
trading_engine = TradingEngine()

# Create FastAPI app
app = FastAPI(
    title="Trading AI",
    description="Automated Trading Signal Processing and Execution System",
    version="1.0.0"
)

# Create API router
api_router = APIRouter(prefix="/api")

# ============ SIGNALS ENDPOINTS ============

@api_router.get("/")
async def root():
    return {"message": "Trading AI System v1.0", "status": "operational"}


@api_router.get("/signals", response_model=List[dict])
async def get_signals(
    limit: int = Query(default=50, le=100),
    executed: Optional[bool] = None,
    dismissed: Optional[bool] = None
):
    """Get all signals with optional filtering"""
    query = {}
    if executed is not None:
        query['executed'] = executed
    if dismissed is not None:
        query['dismissed'] = dismissed
    
    signals = await db.signals.find(query, {"_id": 0}).sort("received_at", -1).limit(limit).to_list(limit)
    return signals


@api_router.get("/signals/{signal_id}")
async def get_signal(signal_id: str):
    """Get a specific signal by ID"""
    signal = await db.signals.find_one({"id": signal_id}, {"_id": 0})
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal


@api_router.post("/signals", response_model=dict)
async def create_signal(input: SignalCreate):
    """Create a new manual signal"""
    try:
        source = SignalSource(input.source) if input.source else SignalSource.MANUAL
    except ValueError:
        source = SignalSource.MANUAL
    
    signal = Signal(
        source=source,
        asset=input.asset,
        action=input.action,
        entry=input.entry,
        stop_loss=input.stop_loss,
        take_profits=input.take_profits,
        leverage=input.leverage,
        confidence=input.confidence,
        original_text=input.original_text
    )
    
    await db.signals.insert_one(signal.to_dict())
    logger.info(f"Signal created: {signal.id} - {signal.asset} {signal.action.value}")
    
    return signal.to_dict()


@api_router.post("/signals/webhook", response_model=dict)
async def webhook_signal(input: SignalWebhook):
    """Receive signals via webhook (TradingView compatible)"""
    
    # If raw text provided, parse it
    if input.text:
        parsed = signal_parser.parse(input.text)
        if not parsed.is_valid():
            raise HTTPException(status_code=400, detail=f"Could not parse signal: {parsed.errors}")
        
        signal = parsed.to_signal(source=SignalSource.WEBHOOK, source_id=input.source_id)
        if not signal:
            raise HTTPException(status_code=400, detail="Failed to create signal from parsed data")
    else:
        # Direct JSON signal
        if not all([input.asset, input.action, input.entry, input.stop_loss]):
            raise HTTPException(status_code=400, detail="Missing required fields: asset, action, entry, stop_loss")
        
        signal = Signal(
            source=SignalSource.WEBHOOK,
            source_id=input.source_id,
            asset=input.asset,
            action=input.action,
            entry=input.entry,
            stop_loss=input.stop_loss,
            take_profits=input.take_profits or [],
            leverage=input.leverage or 1
        )
    
    await db.signals.insert_one(signal.to_dict())
    logger.info(f"Webhook signal received: {signal.id} - {signal.asset}")
    
    return signal.to_dict()


@api_router.delete("/signals/{signal_id}")
async def dismiss_signal(signal_id: str):
    """Dismiss/ignore a signal"""
    result = await db.signals.update_one(
        {"id": signal_id},
        {"$set": {"dismissed": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    return {"success": True, "message": "Signal dismissed"}


# ============ TRADES ENDPOINTS ============

@api_router.get("/trades", response_model=List[dict])
async def get_trades(
    limit: int = Query(default=50, le=100),
    status: Optional[str] = None
):
    """Get all trades"""
    trades = trading_engine.get_all_trades()
    
    if status:
        trades = [t for t in trades if t.status.value == status]
    
    trades = sorted(trades, key=lambda x: x.entry_time, reverse=True)[:limit]
    return [t.to_dict() for t in trades]


@api_router.get("/trades/open", response_model=List[dict])
async def get_open_trades():
    """Get all open trades"""
    trades = trading_engine.get_open_trades()
    return [t.to_dict() for t in trades]


@api_router.get("/trades/{trade_id}")
async def get_trade(trade_id: str):
    """Get a specific trade"""
    trade = trading_engine.trades.get(trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade.to_dict()


@api_router.post("/trades/execute", response_model=dict)
async def execute_trade(input: TradeCreate):
    """Execute a trade from a signal"""
    # Get the signal
    signal_data = await db.signals.find_one({"id": input.signal_id}, {"_id": 0})
    if not signal_data:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    signal = Signal.from_dict(signal_data)
    
    if signal.executed:
        raise HTTPException(status_code=400, detail="Signal already executed")
    
    # Execute the trade
    trade = trading_engine.execute_signal(signal, input.quantity)
    
    if not trade:
        raise HTTPException(status_code=400, detail="Trade rejected by risk manager")
    
    # Mark signal as executed
    await db.signals.update_one(
        {"id": input.signal_id},
        {"$set": {"executed": True}}
    )
    
    # Store trade in DB
    await db.trades.insert_one(trade.to_dict())
    
    return trade.to_dict()


@api_router.post("/trades/close", response_model=dict)
async def close_trade(input: TradeClose):
    """Close an open trade"""
    try:
        exit_reason = ExitReason(input.exit_reason)
    except ValueError:
        exit_reason = ExitReason.MANUAL
    
    success = trading_engine.close_trade(input.trade_id, exit_reason)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to close trade")
    
    trade = trading_engine.trades.get(input.trade_id)
    
    # Update trade in DB
    if trade:
        await db.trades.update_one(
            {"id": input.trade_id},
            {"$set": trade.to_dict()}
        )
    
    return {"success": True, "trade": trade.to_dict() if trade else None}


# ============ POSITIONS ENDPOINTS ============

@api_router.get("/positions", response_model=List[dict])
async def get_positions():
    """Get all open positions"""
    positions = trading_engine.get_positions()
    return [p.to_dict() for p in positions]


# ============ PORTFOLIO ENDPOINTS ============

@api_router.get("/portfolio")
async def get_portfolio():
    """Get portfolio overview"""
    portfolio = trading_engine.get_portfolio()
    return portfolio.to_dict()


@api_router.get("/portfolio/stats")
async def get_portfolio_stats():
    """Get detailed portfolio statistics"""
    return trading_engine.get_statistics()


# ============ SETTINGS ENDPOINTS ============

@api_router.get("/settings")
async def get_settings():
    """Get current trading settings"""
    settings = await db.settings.find_one({"type": "trading"}, {"_id": 0})
    if not settings:
        # Return default settings
        default = TradingSettings()
        return default.to_dict()
    return settings


@api_router.put("/settings")
async def update_settings(input: SettingsUpdate):
    """Update trading settings"""
    # Get current settings
    current = await db.settings.find_one({"type": "trading"}, {"_id": 0})
    
    if current:
        settings = TradingSettings.from_dict(current)
    else:
        settings = TradingSettings()
    
    # Update fields
    update_data = input.model_dump(exclude_none=True)
    
    # Handle risk settings separately
    risk_fields = ['max_risk_per_trade_percent', 'max_open_positions', 'min_risk_reward_ratio', 'default_leverage']
    risk_updates = {k: v for k, v in update_data.items() if k in risk_fields}
    
    if risk_updates:
        for k, v in risk_updates.items():
            setattr(settings.risk_settings, k, v)
    
    # Update other fields
    for k, v in update_data.items():
        if k not in risk_fields and hasattr(settings, k):
            setattr(settings, k, v)
    
    settings.updated_at = datetime.now(timezone.utc)
    
    # Save to DB
    settings_dict = settings.to_dict()
    settings_dict['type'] = 'trading'
    
    await db.settings.update_one(
        {"type": "trading"},
        {"$set": settings_dict},
        upsert=True
    )
    
    # Update trading engine
    trading_engine.update_settings(settings)
    
    return settings_dict


# ============ HEALTH & STATUS ============

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": "connected",
            "trading_engine": "operational",
            "signal_parser": "ready"
        }
    }


# ============ DEMO/SIMULATION ENDPOINTS ============

@api_router.post("/demo/price-update")
async def simulate_price_update(symbol: str, change_percent: float = None):
    """Simulate a price update for testing"""
    trading_engine.simulate_price_update(symbol, change_percent)
    positions = trading_engine.get_positions()
    position = next((p for p in positions if p.symbol == symbol), None)
    
    return {
        "symbol": symbol,
        "position": position.to_dict() if position else None,
        "stats": trading_engine.get_statistics()
    }


@api_router.post("/demo/reset")
async def reset_demo():
    """Reset demo/paper trading account"""
    global trading_engine
    
    # Clear database
    await db.signals.delete_many({})
    await db.trades.delete_many({})
    
    # Reset engine
    settings = await db.settings.find_one({"type": "trading"}, {"_id": 0})
    if settings:
        trading_settings = TradingSettings.from_dict(settings)
    else:
        trading_settings = TradingSettings()
    
    trading_engine = TradingEngine(trading_settings)
    
    return {"success": True, "message": "Demo account reset", "balance": trading_engine.portfolio.current_balance}


# ============ SAMPLE SIGNALS ============

@api_router.post("/demo/sample-signals")
async def create_sample_signals():
    """Create sample signals for demo"""
    sample_signals = [
        {
            "asset": "BTC/USDT",
            "action": "long",
            "entry": 96500.0,
            "stop_loss": 94000.0,
            "take_profits": [99000.0, 102000.0, 105000.0],
            "leverage": 3,
            "confidence": 0.85,
            "source": "telegram",
            "original_text": "🚀 BTC/USDT LONG\nEntry: 96500\nSL: 94000\nTP1: 99000\nTP2: 102000\nTP3: 105000\nLeverage: 3x"
        },
        {
            "asset": "ETH/USDT",
            "action": "long",
            "entry": 3450.0,
            "stop_loss": 3300.0,
            "take_profits": [3600.0, 3800.0],
            "leverage": 2,
            "confidence": 0.78,
            "source": "webhook",
            "original_text": "ETH breakout signal - Entry 3450, SL 3300, TP 3600/3800"
        },
        {
            "asset": "SOL/USDT",
            "action": "short",
            "entry": 195.0,
            "stop_loss": 205.0,
            "take_profits": [180.0, 165.0],
            "leverage": 5,
            "confidence": 0.72,
            "source": "ai",
            "original_text": "AI detected bearish divergence on SOL"
        },
        {
            "asset": "XRP/USDT",
            "action": "long",
            "entry": 2.85,
            "stop_loss": 2.65,
            "take_profits": [3.10, 3.40],
            "leverage": 2,
            "confidence": 0.65,
            "source": "manual"
        }
    ]
    
    created = []
    for data in sample_signals:
        signal = Signal(
            source=SignalSource(data['source']),
            asset=data['asset'],
            action=data['action'],
            entry=data['entry'],
            stop_loss=data['stop_loss'],
            take_profits=data['take_profits'],
            leverage=data['leverage'],
            confidence=data['confidence'],
            original_text=data.get('original_text')
        )
        await db.signals.insert_one(signal.to_dict())
        created.append(signal.to_dict())
    
    return {"success": True, "created": len(created), "signals": created}


# ============ TELEGRAM INTEGRATION ============

@api_router.get("/telegram/channels")
async def get_known_channels():
    """Get list of known Telegram signal channels"""
    channels = []
    for key, info in KNOWN_CHANNELS.items():
        channels.append({
            "id": key,
            "name": info.name,
            "username": info.username,
            "signal_type": info.signal_type.value,
            "format_hints": info.format_hints
        })
    return {"channels": channels}


from pydantic import BaseModel as PydanticBaseModel

class TextInput(PydanticBaseModel):
    text: str

@api_router.post("/telegram/parse")
async def parse_telegram_signal(input: TextInput, channel: str = "evening_trader"):
    """Parse a signal in Telegram format"""
    text = input.text
    if channel == "evening_trader":
        parsed = TelegramSignalParser.parse_evening_trader(text)
    elif channel == "fat_pig_signals":
        parsed = TelegramSignalParser.parse_fat_pig_signals(text)
    else:
        # Use generic parser
        parsed = signal_parser.parse(text)
        parsed = {
            "asset": parsed.asset,
            "action": parsed.action,
            "entry": parsed.entry,
            "stop_loss": parsed.stop_loss,
            "take_profits": parsed.take_profits,
            "leverage": parsed.leverage,
            "confidence": parsed.confidence
        }
    
    return {"parsed": parsed, "channel": channel}


@api_router.get("/telegram/config")
async def get_telegram_config():
    """Get Telegram configuration status"""
    settings = await db.settings.find_one({"type": "telegram"}, {"_id": 0})
    
    has_credentials = bool(
        os.environ.get('TELEGRAM_API_ID') and 
        os.environ.get('TELEGRAM_API_HASH')
    )
    
    return {
        "configured": has_credentials,
        "enabled": settings.get('enabled', False) if settings else False,
        "channels": settings.get('channels', []) if settings else [],
        "instructions": {
            "step1": "Get API credentials from https://my.telegram.org",
            "step2": "Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env",
            "step3": "Add channel usernames to monitor",
            "recommended_channels": ["Evening Trader", "Fat Pig Signals"]
        }
    }


@api_router.put("/telegram/config")
async def update_telegram_config(enabled: bool = None, channels: List[str] = None):
    """Update Telegram configuration"""
    update = {}
    if enabled is not None:
        update['enabled'] = enabled
    if channels is not None:
        update['channels'] = channels
    
    if update:
        update['updated_at'] = datetime.now(timezone.utc).isoformat()
        await db.settings.update_one(
            {"type": "telegram"},
            {"$set": update},
            upsert=True
        )
    
    return await get_telegram_config()


# ============ BINANCE INTEGRATION ============

@api_router.get("/binance/config")
async def get_binance_config():
    """Get Binance configuration status"""
    has_credentials = bool(
        os.environ.get('BINANCE_API_KEY') and 
        os.environ.get('BINANCE_SECRET')
    )
    
    is_testnet = os.environ.get('BINANCE_TESTNET', 'true').lower() == 'true'
    
    return {
        "configured": has_credentials,
        "testnet": is_testnet,
        "network": "testnet" if is_testnet else "live",
        "instructions": {
            "testnet": {
                "url": "https://testnet.binancefuture.com",
                "step1": "Create account at testnet.binancefuture.com",
                "step2": "Generate API keys in account settings",
                "step3": "Set BINANCE_API_KEY and BINANCE_SECRET in .env"
            },
            "live": {
                "url": "https://www.binance.com",
                "warning": "Live trading uses real money! Start with testnet first."
            }
        }
    }


@api_router.get("/binance/balance")
async def get_binance_balance():
    """Get Binance account balance"""
    api_key = os.environ.get('BINANCE_API_KEY')
    api_secret = os.environ.get('BINANCE_SECRET')
    
    if not api_key or not api_secret:
        raise HTTPException(status_code=400, detail="Binance API credentials not configured")
    
    try:
        broker = create_binance_broker(api_key, api_secret, testnet=True)
        balance = await broker.get_balance()
        await broker.close()
        return balance
    except BinanceAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get balance: {e}")


@api_router.get("/binance/price/{symbol}")
async def get_binance_price(symbol: str):
    """Get current price for a symbol"""
    try:
        broker = create_binance_broker(testnet=True)
        price = await broker.get_price(symbol)
        ticker = await broker.get_ticker(symbol)
        await broker.close()
        return {
            "symbol": symbol,
            "price": price,
            "ticker": ticker
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get price: {e}")


@api_router.get("/binance/positions")
async def get_binance_positions():
    """Get open positions on Binance"""
    api_key = os.environ.get('BINANCE_API_KEY')
    api_secret = os.environ.get('BINANCE_SECRET')
    
    if not api_key or not api_secret:
        raise HTTPException(status_code=400, detail="Binance API credentials not configured")
    
    try:
        broker = create_binance_broker(api_key, api_secret, testnet=True)
        positions = await broker.get_positions()
        await broker.close()
        return {"positions": positions}
    except BinanceAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ TELEGRAM BOT ENDPOINTS ============

@api_router.get("/telegram/bot/status")
async def get_telegram_bot_status():
    """Get Telegram bot status"""
    bot = get_telegram_bot()
    
    if not bot:
        return {
            "configured": bool(os.environ.get('TELEGRAM_BOT_TOKEN')),
            "running": False,
            "bot_username": None,
            "instructions": "Add TELEGRAM_BOT_TOKEN to .env and restart"
        }
    
    try:
        me = await bot.get_me()
        return {
            "configured": True,
            "running": bot.running,
            "bot_username": me.get('username'),
            "bot_name": me.get('first_name'),
            "bot_link": f"https://t.me/{me.get('username')}"
        }
    except Exception as e:
        return {
            "configured": True,
            "running": False,
            "error": str(e)
        }


@api_router.post("/telegram/bot/send")
async def send_telegram_message(chat_id: int, message: str):
    """Send a message via the bot"""
    bot = get_telegram_bot()
    
    if not bot:
        raise HTTPException(status_code=400, detail="Telegram bot not configured")
    
    try:
        result = await bot.send_message(chat_id, message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Include router in app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background tasks
telegram_bot_task = None
channel_monitor_task = None

async def telegram_signal_callback(signal_data: dict):
    """Callback when signal is received from Telegram bot or channel"""
    parsed = signal_data.get('parsed', {})
    
    if not parsed.get('asset') or not parsed.get('action'):
        return
    
    # Create signal in database
    signal = Signal(
        source=SignalSource.TELEGRAM,
        source_id=signal_data.get('source_id'),
        asset=parsed['asset'],
        action=parsed['action'],
        entry=parsed['entry'],
        stop_loss=parsed['stop_loss'],
        take_profits=parsed.get('take_profits', []),
        leverage=parsed.get('leverage', 1),
        confidence=parsed.get('confidence', 0.5),
        original_text=signal_data.get('text'),
        metadata={
            'telegram_user': signal_data.get('user'),
            'channel_name': signal_data.get('channel_name'),
            'channel_username': signal_data.get('channel_username')
        }
    )
    
    await db.signals.insert_one(signal.to_dict())
    source = signal_data.get('channel_name') or signal_data.get('user') or 'Telegram'
    logger.info(f"Signal from {source}: {signal.asset} {signal.action.value}")


@app.on_event("startup")
async def startup():
    global telegram_bot_task, channel_monitor_task
    
    logger.info("Trading AI Backend starting...")
    
    # Load settings from DB
    settings = await db.settings.find_one({"type": "trading"}, {"_id": 0})
    if settings:
        trading_settings = TradingSettings.from_dict(settings)
        trading_engine.update_settings(trading_settings)
        logger.info(f"Loaded settings: balance=${trading_settings.initial_balance}")
    
    # Initialize Telegram bot
    bot = await init_telegram_bot(telegram_signal_callback)
    if bot:
        telegram_bot_task = asyncio.create_task(bot.start_polling())
        logger.info("Telegram bot started")
    
    # Initialize Channel Monitor (Evening Trader, Fat Pig Signals)
    monitor = await init_channel_monitor(telegram_signal_callback)
    if monitor:
        # Check if already authorized
        try:
            if await monitor.client.is_user_authorized():
                channel_monitor_task = asyncio.create_task(monitor.start_monitoring())
                logger.info("Channel monitor started (Evening Trader, Fat Pig Signals)")
            else:
                logger.warning("Channel monitor not authorized - run login first")
        except Exception as e:
            logger.warning(f"Channel monitor setup: {e}")
    
    logger.info("Trading AI Backend started successfully")


@app.on_event("shutdown")
async def shutdown():
    global telegram_bot_task, channel_monitor_task
    
    # Stop Telegram bot
    bot = get_telegram_bot()
    if bot:
        await bot.stop()
    if telegram_bot_task:
        telegram_bot_task.cancel()
    
    # Stop Channel monitor
    monitor = get_channel_monitor()
    if monitor:
        await monitor.stop()
    if channel_monitor_task:
        channel_monitor_task.cancel()
    
    client.close()
    logger.info("Trading AI Backend shutdown complete")
