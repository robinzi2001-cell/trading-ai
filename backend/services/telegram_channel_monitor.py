"""
Telegram Channel Monitor for Trading AI
Monitors trading signal channels like Evening Trader, Fat Pig Signals.

Note: First run requires phone verification via interactive session.
Run `python telegram_channel_monitor.py --login` to authenticate.
"""
import asyncio
import os
import logging
from datetime import datetime, timezone
from typing import Optional, Callable, List
from pathlib import Path

try:
    from telethon import TelegramClient, events
    from telethon.tl.types import Channel
    from telethon.errors import SessionPasswordNeededError
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

from services.telegram_listener import TelegramSignalParser, KNOWN_CHANNELS

logger = logging.getLogger(__name__)

# Session file path
SESSION_PATH = Path(__file__).parent.parent / "telegram_session"


class TelegramChannelMonitor:
    """
    Monitors Telegram channels for trading signals using user account.
    
    Supported channels:
    - Evening Trader (@eveningtrader)
    - Fat Pig Signals (@fatpigsignals)
    """
    
    # Popular free signal channels
    DEFAULT_CHANNELS = [
        "eveningtrader",      # Evening Trader
        "fatpigsignals",      # Fat Pig Signals
        # Add more channels here
    ]
    
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        signal_callback: Callable = None,
        channels: List[str] = None
    ):
        if not TELETHON_AVAILABLE:
            raise ImportError("Telethon not installed. Run: pip install telethon")
        
        self.api_id = api_id
        self.api_hash = api_hash
        self.signal_callback = signal_callback
        self.channels = channels or self.DEFAULT_CHANNELS
        
        self.client: Optional[TelegramClient] = None
        self.monitored_entities = {}
        self.running = False
        
        logger.info(f"TelegramChannelMonitor initialized for {len(self.channels)} channels")
    
    async def connect(self, phone: str = None):
        """Connect to Telegram"""
        self.client = TelegramClient(
            str(SESSION_PATH),
            self.api_id,
            self.api_hash
        )
        
        await self.client.connect()
        
        if not await self.client.is_user_authorized():
            if phone:
                await self.client.send_code_request(phone)
                logger.info("Code sent to phone. Check Telegram app.")
                return False
            else:
                logger.warning("Not authorized. Need to login first.")
                return False
        
        me = await self.client.get_me()
        logger.info(f"Connected as: {me.first_name} (@{me.username})")
        return True
    
    async def login(self, phone: str, code: str = None, password: str = None):
        """Complete login with code/password"""
        if not self.client:
            await self.connect()
        
        if code:
            try:
                await self.client.sign_in(phone, code)
            except SessionPasswordNeededError:
                if password:
                    await self.client.sign_in(password=password)
                else:
                    logger.error("2FA enabled. Password required.")
                    return False
        
        return await self.client.is_user_authorized()
    
    async def resolve_channels(self):
        """Resolve channel usernames to entities"""
        for username in self.channels:
            try:
                entity = await self.client.get_entity(username)
                
                if isinstance(entity, Channel):
                    self.monitored_entities[entity.id] = {
                        "entity": entity,
                        "username": username,
                        "title": entity.title
                    }
                    logger.info(f"✅ Resolved: {entity.title} (@{username})")
                else:
                    logger.warning(f"⚠️ {username} is not a channel")
                    
            except Exception as e:
                logger.error(f"❌ Failed to resolve @{username}: {e}")
        
        return len(self.monitored_entities) > 0
    
    async def start_monitoring(self):
        """Start monitoring channels for signals"""
        if not self.client or not await self.client.is_user_authorized():
            logger.error("Not connected. Call connect() first.")
            return
        
        if not await self.resolve_channels():
            logger.error("No channels resolved. Check usernames.")
            return
        
        # Register message handler
        @self.client.on(events.NewMessage(chats=list(self.monitored_entities.keys())))
        async def message_handler(event):
            await self._handle_message(event)
        
        self.running = True
        logger.info(f"🟢 Monitoring {len(self.monitored_entities)} channels...")
        
        # Keep running
        await self.client.run_until_disconnected()
    
    async def _handle_message(self, event):
        """Process incoming message"""
        message = event.message
        if not message.text:
            return
        
        channel_id = event.chat_id
        channel_info = self.monitored_entities.get(channel_id, {})
        channel_name = channel_info.get("title", "Unknown")
        username = channel_info.get("username", "")
        
        text = message.text
        
        # Check if looks like signal
        if not self._looks_like_signal(text):
            return
        
        logger.info(f"📊 Signal detected from {channel_name}")
        
        # Parse based on channel
        if "evening" in username.lower():
            parsed = TelegramSignalParser.parse_evening_trader(text)
        elif "fat" in username.lower() or "pig" in username.lower():
            parsed = TelegramSignalParser.parse_fat_pig_signals(text)
        else:
            parsed = TelegramSignalParser.parse_evening_trader(text)
        
        # Create signal data
        signal_data = {
            "source": "telegram_channel",
            "source_id": f"tg_ch_{channel_id}_{message.id}",
            "channel_name": channel_name,
            "channel_username": username,
            "text": text,
            "parsed": parsed,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Log signal
        if parsed.get("confidence", 0) >= 0.5:
            logger.info(f"   Asset: {parsed.get('asset')}")
            logger.info(f"   Action: {parsed.get('action')}")
            logger.info(f"   Entry: {parsed.get('entry')}")
            logger.info(f"   Confidence: {parsed.get('confidence', 0)*100:.0f}%")
        
        # Call callback
        if self.signal_callback and parsed.get("confidence", 0) >= 0.5:
            try:
                await self.signal_callback(signal_data)
                logger.info("   ✅ Signal stored!")
            except Exception as e:
                logger.error(f"   ❌ Callback failed: {e}")
    
    def _looks_like_signal(self, text: str) -> bool:
        """Check if message looks like trading signal"""
        text_upper = text.upper()
        
        indicators = [
            any(x in text_upper for x in ['LONG', 'SHORT', 'BUY', 'SELL']),
            'ENTRY' in text_upper or '@' in text,
            'SL' in text_upper or 'STOP' in text_upper,
            any(x in text_upper for x in ['USDT', 'USD', 'BTC', 'ETH']),
        ]
        
        return sum(indicators) >= 2
    
    async def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.client:
            await self.client.disconnect()
        logger.info("Channel monitor stopped")


# Global instance
_monitor_instance: Optional[TelegramChannelMonitor] = None


def get_channel_monitor() -> Optional[TelegramChannelMonitor]:
    """Get global monitor instance"""
    return _monitor_instance


async def init_channel_monitor(signal_callback: Callable = None) -> Optional[TelegramChannelMonitor]:
    """Initialize channel monitor"""
    global _monitor_instance
    
    api_id = os.environ.get('TELEGRAM_API_ID')
    api_hash = os.environ.get('TELEGRAM_API_HASH')
    
    if not api_id or not api_hash:
        logger.warning("TELEGRAM_API_ID or TELEGRAM_API_HASH not set")
        return None
    
    try:
        _monitor_instance = TelegramChannelMonitor(
            api_id=int(api_id),
            api_hash=api_hash,
            signal_callback=signal_callback
        )
        
        # Try to connect (will fail if not authenticated)
        connected = await _monitor_instance.connect()
        
        if connected:
            logger.info("Channel monitor connected and ready")
            return _monitor_instance
        else:
            logger.warning("Channel monitor needs authentication")
            return _monitor_instance
            
    except Exception as e:
        logger.error(f"Failed to init channel monitor: {e}")
        return None


# CLI for initial login
async def interactive_login():
    """Interactive login for first-time setup"""
    import getpass
    
    api_id = os.environ.get('TELEGRAM_API_ID') or input("API ID: ")
    api_hash = os.environ.get('TELEGRAM_API_HASH') or input("API Hash: ")
    
    monitor = TelegramChannelMonitor(int(api_id), api_hash)
    
    phone = input("Phone number (with country code, e.g. +49...): ")
    
    await monitor.connect(phone)
    
    code = input("Enter the code sent to Telegram: ")
    
    try:
        success = await monitor.login(phone, code)
        if success:
            print("✅ Login successful! Session saved.")
            print("The channel monitor will now work automatically.")
        else:
            password = getpass.getpass("2FA Password (if enabled): ")
            success = await monitor.login(phone, code, password)
            if success:
                print("✅ Login successful!")
            else:
                print("❌ Login failed")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    await monitor.stop()


if __name__ == "__main__":
    import sys
    
    if "--login" in sys.argv:
        print("=" * 50)
        print("Telegram Channel Monitor - First Time Setup")
        print("=" * 50)
        asyncio.run(interactive_login())
    else:
        print("Usage:")
        print("  python telegram_channel_monitor.py --login  # First time setup")
        print("")
        print("After login, the monitor runs automatically with the server.")
