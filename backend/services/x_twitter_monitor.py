"""
X/Twitter Monitor for Trading AI
Analyzes tweets from influential accounts for market impact.
"""
import logging
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class InfluentialAccount:
    """Influential account to monitor"""
    username: str
    name: str
    category: str
    impact_weight: float
    keywords: List[str]


# Pre-configured influential accounts
INFLUENTIAL_ACCOUNTS = [
    InfluentialAccount(
        username="elonmusk",
        name="Elon Musk",
        category="tech_leader",
        impact_weight=1.0,
        keywords=["bitcoin", "crypto", "doge", "tesla"]
    ),
    InfluentialAccount(
        username="realDonaldTrump",
        name="Donald Trump",
        category="political",
        impact_weight=0.9,
        keywords=["market", "economy", "trade"]
    ),
    InfluentialAccount(
        username="VitalikButerin",
        name="Vitalik Buterin",
        category="crypto_founder",
        impact_weight=0.8,
        keywords=["ethereum", "eth", "crypto", "defi"]
    ),
    InfluentialAccount(
        username="cabordeaux",
        name="CZ Binance",
        category="crypto_exchange",
        impact_weight=0.7,
        keywords=["bnb", "binance", "crypto"]
    ),
]


class XTwitterMonitor:
    """Monitor X/Twitter for market-moving tweets"""
    
    def __init__(self):
        self.accounts = INFLUENTIAL_ACCOUNTS
        logger.info(f"XTwitterMonitor initialized with {len(self.accounts)} accounts")
    
    def get_account(self, username: str) -> Optional[InfluentialAccount]:
        """Get account by username"""
        username_lower = username.lower().replace("@", "")
        for acc in self.accounts:
            if acc.username.lower() == username_lower:
                return acc
        return None
    
    def analyze_tweet_impact(self, author: str, text: str) -> dict:
        """Analyze potential market impact of a tweet"""
        account = self.get_account(author)
        
        if not account:
            return {
                "author": author,
                "preliminary_impact": "unknown",
                "impact_weight": 0.5,
                "relevant_keywords": []
            }
        
        text_lower = text.lower()
        relevant_keywords = [kw for kw in account.keywords if kw in text_lower]
        
        # Calculate preliminary impact
        if len(relevant_keywords) >= 2:
            impact = "high"
        elif len(relevant_keywords) >= 1:
            impact = "medium"
        else:
            impact = "low"
        
        return {
            "author": account.name,
            "username": account.username,
            "category": account.category,
            "preliminary_impact": impact,
            "impact_weight": account.impact_weight,
            "relevant_keywords": relevant_keywords
        }


# Global instance
_monitor_instance: Optional[XTwitterMonitor] = None


def get_x_monitor() -> Optional[XTwitterMonitor]:
    """Get global monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = XTwitterMonitor()
    return _monitor_instance


async def analyze_tweet(author: str, text: str) -> dict:
    """Analyze a tweet for market impact"""
    monitor = get_x_monitor()
    return monitor.analyze_tweet_impact(author, text)
