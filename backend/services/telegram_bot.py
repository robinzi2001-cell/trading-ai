"""
Telegram Bot for Trading AI
Receives trading signals via Telegram Bot API.
Bot: @traiding_r2d2_bot
"""
import asyncio
import os
import logging
from datetime import datetime, timezone
from typing import Optional, Callable, List
import httpx

logger = logging.getLogger(__name__)


class TelegramBot:
    """
    Telegram Bot for receiving trading signals.
    Uses the Bot API (not Telethon) for simpler integration.
    """
    
    def __init__(self, token: str, signal_callback: Callable = None):
        self.token = token
        self.signal_callback = signal_callback
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.running = False
        self.last_update_id = 0
        self.authorized_users: List[int] = []  # Restrict to specific users
        
        logger.info("TelegramBot initialized")
    
    async def get_me(self) -> dict:
        """Get bot info"""
        response = await self.client.get(f"{self.base_url}/getMe")
        data = response.json()
        if data.get('ok'):
            return data['result']
        raise Exception(f"Bot API error: {data}")
    
    async def send_message(self, chat_id: int, text: str, parse_mode: str = "HTML") -> dict:
        """Send a message"""
        response = await self.client.post(
            f"{self.base_url}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
        )
        return response.json()
    
    async def set_commands(self):
        """Set bot commands"""
        commands = [
            {"command": "start", "description": "Start the bot"},
            {"command": "help", "description": "Show help message"},
            {"command": "signal", "description": "Submit a trading signal"},
            {"command": "status", "description": "Get system status"},
            {"command": "portfolio", "description": "Get portfolio summary"},
            {"command": "positions", "description": "Get open positions"},
        ]
        
        response = await self.client.post(
            f"{self.base_url}/setMyCommands",
            json={"commands": commands}
        )
        return response.json()
    
    async def start_polling(self):
        """Start polling for updates"""
        self.running = True
        logger.info("Telegram Bot started polling...")
        
        # Set bot commands
        await self.set_commands()
        
        while self.running:
            try:
                updates = await self._get_updates()
                for update in updates:
                    await self._process_update(update)
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(5)
            
            await asyncio.sleep(1)
    
    async def _get_updates(self) -> list:
        """Get new updates from Telegram"""
        try:
            response = await self.client.get(
                f"{self.base_url}/getUpdates",
                params={
                    "offset": self.last_update_id + 1,
                    "timeout": 30,
                    "allowed_updates": ["message"]
                },
                timeout=35.0  # Slightly longer than Telegram's timeout
            )
            
            data = response.json()
        if not data.get('ok'):
            return []
        
        updates = data.get('result', [])
        if updates:
            self.last_update_id = updates[-1]['update_id']
        
        return updates
    
    async def _process_update(self, update: dict):
        """Process an incoming update"""
        message = update.get('message')
        if not message:
            return
        
        chat_id = message['chat']['id']
        user_id = message['from']['id']
        username = message['from'].get('username', 'Unknown')
        text = message.get('text', '')
        
        logger.info(f"Message from @{username} ({user_id}): {text[:50]}...")
        
        # Handle commands
        if text.startswith('/'):
            await self._handle_command(chat_id, user_id, text)
            return
        
        # Check if message looks like a signal
        if self._looks_like_signal(text):
            await self._handle_signal(chat_id, user_id, username, text)
    
    async def _handle_command(self, chat_id: int, user_id: int, text: str):
        """Handle bot commands"""
        command = text.split()[0].lower().replace('@traiding_r2d2_bot', '')
        
        if command == '/start':
            welcome = """
🤖 <b>Trading AI Bot</b>

Willkommen! Ich bin dein Trading-Signal-Assistent.

<b>So sendest du Signale:</b>
Schicke mir einfach eine Nachricht im Format:

<code>BTC/USDT LONG
Entry: 96500
SL: 94000
TP1: 98000
TP2: 100000
Leverage: 5x</code>

Oder nutze /signal für eine geführte Eingabe.

<b>Befehle:</b>
/help - Hilfe anzeigen
/status - System-Status
/portfolio - Portfolio-Übersicht
/positions - Offene Positionen
"""
            await self.send_message(chat_id, welcome)
        
        elif command == '/help':
            help_text = """
📚 <b>Trading AI Bot - Hilfe</b>

<b>Signal-Format:</b>
<code>ASSET ACTION
Entry: PREIS
SL: PREIS
TP1: PREIS
TP2: PREIS (optional)
Leverage: Xx (optional)</code>

<b>Beispiel:</b>
<code>ETH/USDT LONG
Entry: 3450
SL: 3300
TP1: 3600
TP2: 3800
Leverage: 3x</code>

<b>Unterstützte Aktionen:</b>
LONG, SHORT, BUY, SELL

<b>Unterstützte Assets:</b>
Crypto: BTC/USDT, ETH/USDT, etc.
Forex: EURUSD, GBPUSD, etc.
"""
            await self.send_message(chat_id, help_text)
        
        elif command == '/status':
            status = """
✅ <b>System Status</b>

🟢 Signal Parser: Online
🟢 Trading Engine: Online
🟢 Risk Manager: Online
📊 Mode: Paper Trading

Dashboard: Verfügbar im Web-Interface
"""
            await self.send_message(chat_id, status)
        
        elif command == '/portfolio':
            portfolio_text = """
💼 <b>Portfolio</b>

Um dein Portfolio zu sehen, öffne das Web-Dashboard.

<i>Live-Daten werden dort in Echtzeit angezeigt.</i>
"""
            await self.send_message(chat_id, portfolio_text)
        
        elif command == '/positions':
            positions_text = """
📈 <b>Offene Positionen</b>

Um deine Positionen zu sehen, öffne das Web-Dashboard.

<i>Dort kannst du auch Trades schließen.</i>
"""
            await self.send_message(chat_id, positions_text)
        
        elif command == '/signal':
            signal_help = """
📝 <b>Signal senden</b>

Schicke mir dein Signal im folgenden Format:

<code>BTC/USDT LONG
Entry: 96500
SL: 94000
TP1: 98000
Leverage: 3x</code>

Oder kopiere einfach ein Signal aus deinem Trading-Channel!
"""
            await self.send_message(chat_id, signal_help)
        
        else:
            await self.send_message(chat_id, "❓ Unbekannter Befehl. Nutze /help für Hilfe.")
    
    async def _handle_signal(self, chat_id: int, user_id: int, username: str, text: str):
        """Handle incoming trading signal"""
        from services.telegram_listener import TelegramSignalParser
        
        # Parse the signal
        parsed = TelegramSignalParser.parse_evening_trader(text)
        
        if parsed['confidence'] < 0.5:
            await self.send_message(
                chat_id,
                "⚠️ <b>Signal nicht erkannt</b>\n\n"
                "Bitte überprüfe das Format:\n"
                "<code>ASSET ACTION\nEntry: PREIS\nSL: PREIS\nTP: PREIS</code>"
            )
            return
        
        # Build signal data
        signal_data = {
            "source": "telegram_bot",
            "source_id": f"tg_bot_{chat_id}_{user_id}",
            "text": text,
            "parsed": parsed,
            "user": username,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Send confirmation
        confirmation = f"""
✅ <b>Signal erkannt!</b>

📊 <b>Asset:</b> {parsed['asset']}
📈 <b>Aktion:</b> {parsed['action'].upper()}
💰 <b>Entry:</b> ${parsed['entry']:,.2f}
🛑 <b>Stop Loss:</b> ${parsed['stop_loss']:,.2f}
"""
        
        if parsed['take_profits']:
            tps = [f"${tp:,.2f}" for tp in parsed['take_profits']]
            confirmation += f"🎯 <b>Take Profits:</b> {', '.join(tps)}\n"
        
        if parsed['leverage']:
            confirmation += f"⚡ <b>Leverage:</b> {parsed['leverage']}x\n"
        
        confirmation += f"\n🎯 <b>Confidence:</b> {parsed['confidence']*100:.0f}%"
        confirmation += "\n\n<i>Signal wurde an das Dashboard gesendet.</i>"
        
        await self.send_message(chat_id, confirmation)
        
        # Call callback to store signal
        if self.signal_callback:
            try:
                await self.signal_callback(signal_data)
            except Exception as e:
                logger.error(f"Signal callback failed: {e}")
    
    def _looks_like_signal(self, text: str) -> bool:
        """Check if message looks like a trading signal"""
        text_upper = text.upper()
        
        has_action = any(x in text_upper for x in ['LONG', 'SHORT', 'BUY', 'SELL'])
        has_entry = 'ENTRY' in text_upper or '@' in text
        has_sl = 'SL' in text_upper or 'STOP' in text_upper
        has_asset = any(x in text_upper for x in ['USDT', 'USD', 'BTC', 'ETH', 'EUR'])
        
        return sum([has_action, has_entry, has_sl, has_asset]) >= 2
    
    async def stop(self):
        """Stop the bot"""
        self.running = False
        await self.client.aclose()
        logger.info("Telegram Bot stopped")


# Global bot instance
_bot_instance: Optional[TelegramBot] = None


def get_telegram_bot() -> Optional[TelegramBot]:
    """Get the global bot instance"""
    global _bot_instance
    return _bot_instance


async def init_telegram_bot(signal_callback: Callable = None) -> Optional[TelegramBot]:
    """Initialize the Telegram bot"""
    global _bot_instance
    
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not set")
        return None
    
    _bot_instance = TelegramBot(token, signal_callback)
    
    # Verify bot
    try:
        me = await _bot_instance.get_me()
        logger.info(f"Telegram Bot initialized: @{me.get('username')}")
    except Exception as e:
        logger.error(f"Failed to initialize bot: {e}")
        _bot_instance = None
        return None
    
    return _bot_instance


# Test function
async def test_bot():
    """Test the bot"""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        print("No token set")
        return
    
    bot = TelegramBot(token)
    me = await bot.get_me()
    print(f"Bot: @{me['username']}")
    print(f"Name: {me['first_name']}")
    
    await bot.client.aclose()


if __name__ == "__main__":
    asyncio.run(test_bot())
