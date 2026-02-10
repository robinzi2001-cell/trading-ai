"""
Telegram Signal Listener for Trading AI
Uses Telethon to monitor trading signal channels like Evening Trader, Fat Pig Signals.
"""
import asyncio
import os
import re
import logging
from datetime import datetime, timezone
from typing import Optional, List, Callable
from dataclasses import dataclass
from enum import Enum

try:
    from telethon import TelegramClient, events
    from telethon.tl.types import Channel, Message
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    TelegramClient = None
    Channel = None
    Message = None

logger = logging.getLogger(__name__)


class SignalSourceChannel(Enum):
    """Known trading signal channels"""
    EVENING_TRADER = "evening_trader"
    FAT_PIG_SIGNALS = "fat_pig_signals"
    CUSTOM = "custom"


@dataclass
class TelegramConfig:
    """Telegram API configuration"""
    api_id: int
    api_hash: str
    phone_number: Optional[str] = None
    session_name: str = "trading_ai_session"
    channels: List[str] = None
    
    def __post_init__(self):
        if self.channels is None:
            self.channels = []


@dataclass 
class ChannelInfo:
    """Channel information"""
    name: str
    username: Optional[str]
    channel_id: int
    signal_type: SignalSourceChannel
    
    # Parsing configuration
    signal_patterns: List[str] = None
    format_hints: dict = None


# Known channel configurations
KNOWN_CHANNELS = {
    "evening_trader": ChannelInfo(
        name="Evening Trader",
        username="eveningtrader",
        channel_id=0,  # Will be resolved
        signal_type=SignalSourceChannel.EVENING_TRADER,
        signal_patterns=[
            r"(?:LONG|SHORT|BUY|SELL)",
            r"Entry[:\s]*[\d.,]+",
            r"(?:SL|Stop\s*Loss)[:\s]*[\d.,]+",
            r"(?:TP|Take\s*Profit|Target)[:\s]*[\d.,]+"
        ],
        format_hints={
            "typically_has_emoji": True,
            "leverage_format": "isolated",
            "multiple_targets": True
        }
    ),
    "fat_pig_signals": ChannelInfo(
        name="Fat Pig Signals",
        username="fatpigsignals",
        channel_id=0,
        signal_type=SignalSourceChannel.FAT_PIG_SIGNALS,
        signal_patterns=[
            r"#\w+",  # Hashtag asset
            r"(?:Entry|Buy|Sell)[:\s]*[\d.,]+",
            r"(?:Stoploss|SL)[:\s]*[\d.,]+",
            r"(?:Target|TP)\d*[:\s]*[\d.,]+"
        ],
        format_hints={
            "uses_hashtags": True,
            "clear_structure": True,
            "risk_reward_included": True
        }
    )
}


class TelegramSignalListener:
    """
    Telegram client for monitoring trading signal channels.
    
    Requires Telegram API credentials from https://my.telegram.org
    """
    
    def __init__(self, config: TelegramConfig, signal_callback: Callable = None):
        if not TELETHON_AVAILABLE:
            raise ImportError("Telethon is not installed. Run: pip install telethon")
        
        self.config = config
        self.client: Optional[TelegramClient] = None
        self.signal_callback = signal_callback
        self.monitored_channels: dict = {}
        self.running = False
        
        logger.info(f"TelegramSignalListener initialized with {len(config.channels)} channels")
    
    async def connect(self):
        """Connect to Telegram"""
        self.client = TelegramClient(
            self.config.session_name,
            self.config.api_id,
            self.config.api_hash
        )
        
        await self.client.start(phone=self.config.phone_number)
        
        if await self.client.is_user_authorized():
            me = await self.client.get_me()
            logger.info(f"Connected to Telegram as: {me.username or me.phone}")
        else:
            logger.warning("Not authorized - please complete login flow")
        
        return self
    
    async def resolve_channels(self):
        """Resolve channel usernames to entities"""
        for channel_name in self.config.channels:
            try:
                # Try known channels first
                if channel_name.lower() in KNOWN_CHANNELS:
                    channel_info = KNOWN_CHANNELS[channel_name.lower()]
                    username = channel_info.username
                else:
                    username = channel_name
                
                entity = await self.client.get_entity(username)
                
                if isinstance(entity, Channel):
                    self.monitored_channels[entity.id] = {
                        "entity": entity,
                        "name": entity.title,
                        "username": username,
                        "config": KNOWN_CHANNELS.get(channel_name.lower())
                    }
                    logger.info(f"Resolved channel: {entity.title} (ID: {entity.id})")
                else:
                    logger.warning(f"{username} is not a channel")
                    
            except Exception as e:
                logger.error(f"Failed to resolve channel {channel_name}: {e}")
    
    async def start_listening(self):
        """Start listening for messages in configured channels"""
        if not self.client:
            await self.connect()
        
        await self.resolve_channels()
        
        if not self.monitored_channels:
            logger.warning("No channels to monitor")
            return
        
        # Register message handler
        @self.client.on(events.NewMessage(chats=list(self.monitored_channels.keys())))
        async def message_handler(event: events.NewMessage.Event):
            await self._process_message(event.message, event.chat_id)
        
        self.running = True
        logger.info(f"Started listening to {len(self.monitored_channels)} channels")
        
        # Keep running
        await self.client.run_until_disconnected()
    
    async def _process_message(self, message: Message, channel_id: int):
        """Process incoming message for trading signals"""
        if not message.text:
            return
        
        channel_info = self.monitored_channels.get(channel_id, {})
        channel_name = channel_info.get("name", "Unknown")
        
        logger.debug(f"New message from {channel_name}: {message.text[:100]}...")
        
        # Check if message looks like a trading signal
        if self._looks_like_signal(message.text):
            logger.info(f"Potential signal detected from {channel_name}")
            
            # Create signal data
            signal_data = {
                "source": "telegram",
                "source_id": f"tg_{channel_id}_{message.id}",
                "channel_name": channel_name,
                "channel_id": channel_id,
                "text": message.text,
                "timestamp": message.date.isoformat() if message.date else datetime.now(timezone.utc).isoformat(),
                "message_id": message.id
            }
            
            # Call callback if registered
            if self.signal_callback:
                try:
                    await self.signal_callback(signal_data)
                except Exception as e:
                    logger.error(f"Signal callback failed: {e}")
    
    def _looks_like_signal(self, text: str) -> bool:
        """Check if text looks like a trading signal"""
        text_upper = text.upper()
        
        # Must have action
        has_action = any(action in text_upper for action in ['LONG', 'SHORT', 'BUY', 'SELL', 'KAUFEN', 'VERKAUFEN'])
        
        # Must have price-like numbers
        has_numbers = bool(re.search(r'\d+(?:[.,]\d+)?', text))
        
        # Should have entry/stop/target keywords
        has_levels = any(level in text_upper for level in ['ENTRY', 'SL', 'TP', 'STOP', 'TARGET', 'EINSTIEG', 'ZIEL'])
        
        # Check for crypto pairs
        has_pair = bool(re.search(r'[A-Z]{2,6}[/\-]?(?:USDT|USDC|BTC|ETH|USD|EUR)', text_upper))
        
        # Score the signal
        score = sum([has_action, has_numbers, has_levels, has_pair])
        
        return score >= 2
    
    async def get_recent_messages(self, channel_id: int, limit: int = 10) -> List[dict]:
        """Get recent messages from a channel"""
        if channel_id not in self.monitored_channels:
            return []
        
        messages = []
        entity = self.monitored_channels[channel_id]["entity"]
        
        async for message in self.client.iter_messages(entity, limit=limit):
            if message.text:
                messages.append({
                    "id": message.id,
                    "text": message.text,
                    "date": message.date.isoformat() if message.date else None
                })
        
        return messages
    
    async def stop(self):
        """Stop the listener"""
        self.running = False
        if self.client:
            await self.client.disconnect()
        logger.info("Telegram listener stopped")


class TelegramSignalParser:
    """
    Specialized parser for known Telegram signal formats.
    """
    
    @staticmethod
    def parse_evening_trader(text: str) -> dict:
        """Parse Evening Trader signal format"""
        result = {
            "asset": None,
            "action": None,
            "entry": None,
            "stop_loss": None,
            "take_profits": [],
            "leverage": None,
            "confidence": 0.0
        }
        
        text_upper = text.upper()
        
        # Extract asset (e.g., BTC/USDT, ETHUSDT)
        asset_match = re.search(r'([A-Z]{2,6})[/\-]?(USDT|USDC|BTC|ETH)', text_upper)
        if asset_match:
            result["asset"] = f"{asset_match.group(1)}/{asset_match.group(2)}"
        
        # Extract action
        if any(x in text_upper for x in ['LONG', 'BUY', '🟢', '📈']):
            result["action"] = "long"
        elif any(x in text_upper for x in ['SHORT', 'SELL', '🔴', '📉']):
            result["action"] = "short"
        
        # Extract entry price
        entry_patterns = [
            r'ENTRY[:\s]*([0-9,.]+)',
            r'OPEN[:\s]*([0-9,.]+)',
            r'@[:\s]*([0-9,.]+)'
        ]
        for pattern in entry_patterns:
            match = re.search(pattern, text_upper)
            if match:
                result["entry"] = TelegramSignalParser._parse_number(match.group(1))
                break
        
        # Extract stop loss
        sl_patterns = [
            r'(?:SL|STOP\s*LOSS|STOPLOSS)[:\s]*([0-9,.]+)',
        ]
        for pattern in sl_patterns:
            match = re.search(pattern, text_upper)
            if match:
                result["stop_loss"] = TelegramSignalParser._parse_number(match.group(1))
                break
        
        # Extract take profits
        tp_pattern = r'(?:TP|TARGET|TAKE\s*PROFIT)\s*\d*[:\s]*([0-9,.]+)'
        for match in re.finditer(tp_pattern, text_upper):
            tp = TelegramSignalParser._parse_number(match.group(1))
            if tp and tp not in result["take_profits"]:
                result["take_profits"].append(tp)
        result["take_profits"] = sorted(result["take_profits"])
        
        # Extract leverage
        lev_match = re.search(r'(?:LEV|LEVERAGE|HEBEL)[:\s]*(\d+)X?', text_upper)
        if lev_match:
            result["leverage"] = int(lev_match.group(1))
        
        # Calculate confidence
        filled_fields = sum(1 for v in [result["asset"], result["action"], result["entry"], result["stop_loss"]] if v)
        result["confidence"] = filled_fields / 4.0
        if result["take_profits"]:
            result["confidence"] = min(1.0, result["confidence"] + 0.15)
        
        return result
    
    @staticmethod
    def parse_fat_pig_signals(text: str) -> dict:
        """Parse Fat Pig Signals format"""
        result = {
            "asset": None,
            "action": None,
            "entry": None,
            "stop_loss": None,
            "take_profits": [],
            "leverage": None,
            "confidence": 0.0
        }
        
        text_upper = text.upper()
        
        # Fat Pig often uses hashtags for assets: #BTC #ETH
        hashtag_match = re.search(r'#([A-Z]{2,6})', text_upper)
        if hashtag_match:
            result["asset"] = f"{hashtag_match.group(1)}/USDT"
        
        # Or standard pair format
        if not result["asset"]:
            pair_match = re.search(r'([A-Z]{2,6})[/\-]?(USDT|USD|BTC)', text_upper)
            if pair_match:
                result["asset"] = f"{pair_match.group(1)}/{pair_match.group(2)}"
        
        # Action
        if 'BUY' in text_upper or 'LONG' in text_upper:
            result["action"] = "long"
        elif 'SELL' in text_upper or 'SHORT' in text_upper:
            result["action"] = "short"
        
        # Entry
        entry_match = re.search(r'(?:ENTRY|BUY|SELL)[:\s@]*([0-9,.]+)', text_upper)
        if entry_match:
            result["entry"] = TelegramSignalParser._parse_number(entry_match.group(1))
        
        # Stop Loss
        sl_match = re.search(r'(?:STOPLOSS|SL)[:\s]*([0-9,.]+)', text_upper)
        if sl_match:
            result["stop_loss"] = TelegramSignalParser._parse_number(sl_match.group(1))
        
        # Targets
        for match in re.finditer(r'(?:TARGET|TP)\s*\d*[:\s]*([0-9,.]+)', text_upper):
            tp = TelegramSignalParser._parse_number(match.group(1))
            if tp and tp not in result["take_profits"]:
                result["take_profits"].append(tp)
        result["take_profits"] = sorted(result["take_profits"])
        
        # Leverage
        lev_match = re.search(r'(\d+)X\s*(?:LEV|LEVERAGE)?', text_upper)
        if lev_match:
            result["leverage"] = int(lev_match.group(1))
        
        # Confidence
        filled = sum(1 for v in [result["asset"], result["action"], result["entry"], result["stop_loss"]] if v)
        result["confidence"] = filled / 4.0
        if result["take_profits"]:
            result["confidence"] = min(1.0, result["confidence"] + 0.15)
        
        return result
    
    @staticmethod
    def _parse_number(text: str) -> Optional[float]:
        """Parse number from text"""
        if not text:
            return None
        try:
            text = text.strip().replace(',', '')
            return float(text)
        except ValueError:
            return None


# Async helper for API integration
async def create_telegram_listener(
    api_id: int,
    api_hash: str,
    channels: List[str],
    signal_callback: Callable
) -> TelegramSignalListener:
    """Factory function to create and connect a Telegram listener"""
    config = TelegramConfig(
        api_id=api_id,
        api_hash=api_hash,
        channels=channels
    )
    
    listener = TelegramSignalListener(config, signal_callback)
    await listener.connect()
    
    return listener


# Test function
async def test_parser():
    """Test signal parsers with sample messages"""
    
    # Evening Trader style
    sample1 = """
    🚀 BTC/USDT LONG
    
    Entry: 96,500
    SL: 94,000
    TP1: 98,000
    TP2: 100,000
    TP3: 105,000
    
    Leverage: 5x (Isolated)
    """
    
    # Fat Pig style
    sample2 = """
    #BTC LONG
    
    Buy: 96500
    Stoploss: 94000
    Target 1: 98000
    Target 2: 100000
    
    10x Leverage
    """
    
    print("Evening Trader Parser:")
    result1 = TelegramSignalParser.parse_evening_trader(sample1)
    print(result1)
    
    print("\nFat Pig Signals Parser:")
    result2 = TelegramSignalParser.parse_fat_pig_signals(sample2)
    print(result2)


if __name__ == "__main__":
    asyncio.run(test_parser())
