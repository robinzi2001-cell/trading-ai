"""
Notification Service for Trading AI
Sends notifications via Telegram bot.
"""
import asyncio
import os
import logging
from datetime import datetime, timezone
from typing import Optional, List

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Sends notifications to users via Telegram.
    """
    
    def __init__(self, bot = None, chat_ids: List[int] = None):
        self.bot = bot
        self.chat_ids = chat_ids or []
        self.enabled = True
        
        logger.info(f"NotificationService initialized for {len(self.chat_ids)} chats")
    
    def set_bot(self, bot):
        """Set the Telegram bot instance"""
        self.bot = bot
    
    def add_chat(self, chat_id: int):
        """Add a chat to receive notifications"""
        if chat_id not in self.chat_ids:
            self.chat_ids.append(chat_id)
            logger.info(f"Added notification chat: {chat_id}")
    
    def remove_chat(self, chat_id: int):
        """Remove a chat from notifications"""
        if chat_id in self.chat_ids:
            self.chat_ids.remove(chat_id)
    
    async def send(self, message: str, parse_mode: str = "HTML"):
        """Send notification to all registered chats"""
        if not self.enabled or not self.bot:
            return
        
        for chat_id in self.chat_ids:
            try:
                await self.bot.send_message(chat_id, message, parse_mode)
            except Exception as e:
                logger.error(f"Failed to send notification to {chat_id}: {e}")
    
    async def send_signal_alert(self, signal: dict):
        """Send alert for new signal"""
        msg = f"""
🔔 <b>Neues Signal!</b>

📊 <b>Asset:</b> {signal.get('asset')}
📈 <b>Aktion:</b> {signal.get('action', '').upper()}
💰 <b>Entry:</b> ${signal.get('entry', 0):,.2f}
🛑 <b>Stop Loss:</b> ${signal.get('stop_loss', 0):,.2f}
"""
        
        tps = signal.get('take_profits', [])
        if tps:
            tp_str = ', '.join([f"${tp:,.2f}" for tp in tps])
            msg += f"🎯 <b>Take Profits:</b> {tp_str}\n"
        
        leverage = signal.get('leverage', 1)
        if leverage > 1:
            msg += f"⚡ <b>Leverage:</b> {leverage}x\n"
        
        confidence = signal.get('confidence', 0)
        msg += f"🎯 <b>Confidence:</b> {confidence*100:.0f}%\n"
        
        source = signal.get('channel_name') or signal.get('source', 'Unknown')
        msg += f"📡 <b>Quelle:</b> {source}"
        
        await self.send(msg)
    
    async def send_trade_executed(self, trade: dict):
        """Send alert for executed trade"""
        pnl = trade.get('unrealized_pnl', 0)
        pnl_str = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
        
        msg = f"""
✅ <b>Trade Ausgeführt!</b>

📊 <b>Asset:</b> {trade.get('symbol')}
📈 <b>Side:</b> {trade.get('side', '').upper()}
💰 <b>Entry:</b> ${trade.get('entry_price', 0):,.2f}
📏 <b>Size:</b> {trade.get('quantity', 0):.6f}
⚡ <b>Leverage:</b> {trade.get('leverage', 1)}x

🛑 <b>SL:</b> ${trade.get('stop_loss', 0):,.2f}
"""
        
        tps = trade.get('take_profits', [])
        if tps:
            msg += f"🎯 <b>TPs:</b> {', '.join([f'${tp:,.2f}' for tp in tps])}\n"
        
        await self.send(msg)
    
    async def send_trade_closed(self, trade: dict):
        """Send alert for closed trade"""
        pnl = trade.get('realized_pnl', 0)
        pnl_percent = trade.get('realized_pnl_percent', 0)
        
        emoji = "🟢" if pnl >= 0 else "🔴"
        pnl_str = f"+${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
        
        msg = f"""
{emoji} <b>Trade Geschlossen!</b>

📊 <b>Asset:</b> {trade.get('symbol')}
💰 <b>Entry:</b> ${trade.get('entry_price', 0):,.2f}
💰 <b>Exit:</b> ${trade.get('exit_price', 0):,.2f}

📈 <b>P&L:</b> {pnl_str} ({pnl_percent:+.2f}%)
🏷️ <b>Grund:</b> {trade.get('exit_reason', 'Manual')}
"""
        
        await self.send(msg)
    
    async def send_ai_analysis(self, signal: dict, analysis: dict):
        """Send AI analysis result"""
        score = analysis.get('score', 0)
        quality = analysis.get('quality', 'unknown')
        
        emoji = "✅" if analysis.get('should_execute') else "❌"
        
        msg = f"""
🤖 <b>AI Analyse</b>

📊 <b>Asset:</b> {signal.get('asset')}
{emoji} <b>Empfehlung:</b> {'Ausführen' if analysis.get('should_execute') else 'Nicht ausführen'}

📈 <b>Score:</b> {score:.0f}/100
🏷️ <b>Qualität:</b> {quality.upper()}

💬 <b>Begründung:</b>
{analysis.get('reasoning', 'N/A')}
"""
        
        warnings = analysis.get('warnings', [])
        if warnings:
            msg += f"\n⚠️ <b>Warnungen:</b>\n"
            for w in warnings:
                msg += f"• {w}\n"
        
        await self.send(msg)
    
    async def send_social_alert(self, post: dict, analysis: dict):
        """Send alert for market-moving social media post"""
        impact = analysis.get('impact_score', 0)
        sentiment = analysis.get('sentiment', 'neutral')
        
        if sentiment == 'bullish':
            emoji = "🚀"
        elif sentiment == 'bearish':
            emoji = "📉"
        else:
            emoji = "📊"
        
        msg = f"""
{emoji} <b>Social Media Alert!</b>

👤 <b>Autor:</b> {post.get('author')}
🐦 <b>Plattform:</b> {post.get('platform', 'X/Twitter')}

📝 <b>Post:</b>
<i>{post.get('text', '')[:300]}{'...' if len(post.get('text', '')) > 300 else ''}</i>

📊 <b>Impact Score:</b> {impact:+.0f}
📈 <b>Sentiment:</b> {sentiment.upper()}
🎯 <b>Betroffene Assets:</b> {', '.join(analysis.get('affected_assets', []))}

💡 <b>Empfehlung:</b> {analysis.get('suggested_action', 'wait').upper()}
⏰ <b>Dringlichkeit:</b> {analysis.get('urgency', 'N/A')}
"""
        
        await self.send(msg)


# Global instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """Get global notification service"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service


def init_notification_service(bot = None, chat_ids: List[int] = None) -> NotificationService:
    """Initialize notification service"""
    global _notification_service
    _notification_service = NotificationService(bot, chat_ids)
    return _notification_service
