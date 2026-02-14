"""
Twitter RSS Monitor for Trading AI
Monitors Twitter via RSS feeds (Nitter instances).
Note: Nitter instances are often unreliable.
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Callable, Set

logger = logging.getLogger(__name__)


@dataclass
class Tweet:
    """Tweet data"""
    id: str
    author: str
    username: str
    text: str
    timestamp: datetime
    url: str


@dataclass
class RSSSource:
    """RSS source configuration"""
    name: str
    username: str
    category: str
    impact_weight: float


class TwitterRSSMonitor:
    """Monitor Twitter via RSS feeds"""
    
    NITTER_INSTANCES = [
        "nitter.net",
        "nitter.it",
        "nitter.cz",
    ]
    
    def __init__(self, callback: Callable = None):
        self.callback = callback
        self.accounts: List[RSSSource] = []
        self.seen_tweets: Set[str] = set()
        self.running = False
        self.working_nitter: Optional[str] = None
        
        logger.info("TwitterRSSMonitor initialized")
    
    def add_account(self, name: str, username: str, category: str = "crypto", impact_weight: float = 1.0):
        """Add account to monitor"""
        self.accounts.append(RSSSource(
            name=name,
            username=username,
            category=category,
            impact_weight=impact_weight
        ))
        logger.info(f"Added @{username} to Twitter monitoring")
    
    def remove_account(self, username: str):
        """Remove account from monitoring"""
        self.accounts = [a for a in self.accounts if a.username.lower() != username.lower()]
    
    def get_accounts(self) -> List[dict]:
        """Get list of monitored accounts"""
        return [
            {
                "name": a.name,
                "username": a.username,
                "category": a.category,
                "impact_weight": a.impact_weight
            }
            for a in self.accounts
        ]
    
    async def check_all_accounts(self) -> List[Tweet]:
        """Check all accounts for new tweets"""
        # Note: This is a stub - real implementation would use RSS feeds
        logger.info("Checking Twitter RSS feeds (stub)")
        return []
    
    async def start_monitoring(self, interval: int = 300):
        """Start monitoring loop"""
        self.running = True
        logger.info(f"Starting Twitter RSS monitoring (interval: {interval}s)")
        
        while self.running:
            try:
                tweets = await self.check_all_accounts()
                for tweet in tweets:
                    if self.callback:
                        account = next((a for a in self.accounts if a.username.lower() == tweet.username.lower()), None)
                        if account:
                            await self.callback(tweet, account)
            except Exception as e:
                logger.error(f"Twitter RSS check error: {e}")
            
            await asyncio.sleep(interval)
    
    async def stop(self):
        """Stop monitoring"""
        self.running = False
        logger.info("Twitter RSS monitoring stopped")


# Global instance
_monitor_instance: Optional[TwitterRSSMonitor] = None


def get_twitter_rss_monitor() -> Optional[TwitterRSSMonitor]:
    """Get global monitor instance"""
    return _monitor_instance


async def init_twitter_rss_monitor(callback: Callable = None) -> TwitterRSSMonitor:
    """Initialize Twitter RSS monitor"""
    global _monitor_instance
    
    _monitor_instance = TwitterRSSMonitor(callback)
    
    # Add default accounts
    default_accounts = [
        ("Elon Musk", "elonmusk", "tech_leader", 1.0),
        ("Donald Trump", "realDonaldTrump", "political", 0.9),
        ("Vitalik Buterin", "VitalikButerin", "crypto", 0.8),
        ("Michael Saylor", "saylor", "crypto", 0.7),
        ("CZ Binance", "cz_binance", "crypto", 0.7),
    ]
    
    for name, username, category, weight in default_accounts:
        _monitor_instance.add_account(name, username, category, weight)
    
    return _monitor_instance
