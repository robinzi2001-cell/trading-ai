"""
X/Twitter Monitor for Trading AI
Monitors influential accounts for market-moving posts.
"""
import asyncio
import os
import re
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)


@dataclass
class InfluentialAccount:
    """Influential account to monitor"""
    username: str
    name: str
    category: str  # crypto, politics, business
    impact_weight: float  # 1.0 = normal, 2.0 = very influential
    keywords: List[str]  # Keywords that trigger analysis


# Influential accounts to monitor
INFLUENTIAL_ACCOUNTS = [
    InfluentialAccount(
        username="realDonaldTrump",
        name="Donald Trump",
        category="politics",
        impact_weight=2.0,
        keywords=["bitcoin", "crypto", "tariff", "china", "economy", "fed", "interest", "dollar"]
    ),
    InfluentialAccount(
        username="elonmusk",
        name="Elon Musk",
        category="crypto",
        impact_weight=2.0,
        keywords=["doge", "bitcoin", "crypto", "tesla", "x", "ai"]
    ),
    InfluentialAccount(
        username="michael_saylor",
        name="Michael Saylor",
        category="crypto",
        impact_weight=1.5,
        keywords=["bitcoin", "btc", "buy", "hodl"]
    ),
    InfluentialAccount(
        username="VitalikButerin",
        name="Vitalik Buterin",
        category="crypto",
        impact_weight=1.5,
        keywords=["ethereum", "eth", "defi", "layer2"]
    ),
    InfluentialAccount(
        username="caborai",
        name="CZ (Binance)",
        category="crypto",
        impact_weight=1.5,
        keywords=["bnb", "binance", "crypto", "4"]
    ),
]


class XTwitterMonitor:
    """
    Monitors X/Twitter for market-moving posts.
    
    Note: Full Twitter API requires authentication.
    This implementation uses a simulated/mock approach for demo.
    For production, integrate Twitter API v2 or use a third-party service.
    """
    
    def __init__(self, callback: Callable = None):
        self.callback = callback
        self.accounts = {a.username.lower(): a for a in INFLUENTIAL_ACCOUNTS}
        self.running = False
        self.processed_ids = set()
        
        logger.info(f"X/Twitter Monitor initialized for {len(self.accounts)} accounts")
    
    async def start_monitoring(self):
        """Start monitoring for new posts"""
        self.running = True
        logger.info("X/Twitter Monitor started")
        
        while self.running:
            try:
                # In production: Poll Twitter API or use streaming
                # For now: Simulated monitoring
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"X Monitor error: {e}")
                await asyncio.sleep(30)
    
    async def analyze_post(self, post: Dict) -> Optional[Dict]:
        """Analyze a post for trading signals"""
        text = post.get('text', '').lower()
        author = post.get('author', '').lower()
        
        # Get account info
        account = self.accounts.get(author)
        if not account:
            return None
        
        # Check for relevant keywords
        matched_keywords = [kw for kw in account.keywords if kw in text]
        
        if not matched_keywords:
            return None
        
        # Detect potential market impact
        impact = self._assess_impact(text, account, matched_keywords)
        
        return {
            "author": account.name,
            "username": account.username,
            "category": account.category,
            "text": post.get('text'),
            "keywords": matched_keywords,
            "impact_weight": account.impact_weight,
            "preliminary_impact": impact,
            "timestamp": post.get('timestamp', datetime.now(timezone.utc).isoformat()),
            "platform": "X/Twitter"
        }
    
    def _assess_impact(self, text: str, account: InfluentialAccount, keywords: List[str]) -> Dict:
        """Preliminary impact assessment"""
        # Sentiment indicators
        bullish_words = ['buy', 'moon', 'pump', 'bullish', 'up', 'good', 'great', 'amazing', 'support', 'love']
        bearish_words = ['sell', 'dump', 'crash', 'bearish', 'down', 'bad', 'terrible', 'ban', 'illegal']
        
        bullish_count = sum(1 for w in bullish_words if w in text)
        bearish_count = sum(1 for w in bearish_words if w in text)
        
        if bullish_count > bearish_count:
            sentiment = "bullish"
            base_score = 30 + (bullish_count * 10)
        elif bearish_count > bullish_count:
            sentiment = "bearish"
            base_score = -30 - (bearish_count * 10)
        else:
            sentiment = "neutral"
            base_score = 0
        
        # Apply weight
        final_score = base_score * account.impact_weight
        
        # Detect affected assets
        affected_assets = []
        asset_map = {
            'bitcoin': 'BTC', 'btc': 'BTC',
            'ethereum': 'ETH', 'eth': 'ETH',
            'doge': 'DOGE', 'dogecoin': 'DOGE',
            'solana': 'SOL', 'sol': 'SOL',
            'xrp': 'XRP', 'ripple': 'XRP',
            'bnb': 'BNB', 'binance': 'BNB',
        }
        
        for keyword, asset in asset_map.items():
            if keyword in text and asset not in affected_assets:
                affected_assets.append(asset)
        
        # If no specific asset but crypto mentioned
        if not affected_assets and any(w in text for w in ['crypto', 'cryptocurrency']):
            affected_assets = ['BTC', 'ETH']  # Major cryptos
        
        return {
            "sentiment": sentiment,
            "score": min(max(final_score, -100), 100),
            "affected_assets": affected_assets,
            "urgency": "immediate" if abs(final_score) > 50 else "short-term"
        }
    
    async def process_manual_post(self, author: str, text: str) -> Optional[Dict]:
        """Process a manually submitted post"""
        post = {
            "author": author,
            "text": text,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Try to find account
        for acc in INFLUENTIAL_ACCOUNTS:
            if acc.name.lower() in author.lower() or acc.username.lower() in author.lower():
                post["author"] = acc.username.lower()
                break
        
        return await self.analyze_post(post)
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        logger.info("X/Twitter Monitor stopped")


# Singleton
_monitor: Optional[XTwitterMonitor] = None


def get_x_monitor() -> XTwitterMonitor:
    """Get global monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = XTwitterMonitor()
    return _monitor


async def analyze_tweet(author: str, text: str) -> Optional[Dict]:
    """Analyze a tweet for market impact"""
    monitor = get_x_monitor()
    return await monitor.process_manual_post(author, text)
