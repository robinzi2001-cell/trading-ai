"""
Twitter/X RSS Monitor for Trading AI
Monitors influential accounts via RSS feeds (Nitter, RSS.app, etc.)
No API key required!
"""
import asyncio
import os
import logging
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class RSSSource:
    """Configuration for an RSS source"""
    name: str
    username: str
    rss_url: str
    source_type: str  # nitter, rss_app, fivefilters
    category: str  # crypto, politics, business
    impact_weight: float = 1.0


# Nitter instances that are currently working (as of 2025)
NITTER_INSTANCES = [
    "nitter.net",
    "nitter.privacydev.net",
    "nitter.poast.org",
    "nitter.1d4.us",
]

# Default accounts to monitor
DEFAULT_ACCOUNTS = [
    RSSSource(
        name="Elon Musk",
        username="elonmusk",
        rss_url="",  # Will be generated
        source_type="nitter",
        category="crypto",
        impact_weight=2.0
    ),
    RSSSource(
        name="Donald Trump",
        username="realDonaldTrump",
        rss_url="",  # Note: Trump mainly uses Truth Social now
        source_type="nitter",
        category="politics",
        impact_weight=2.0
    ),
    RSSSource(
        name="CZ Binance",
        username="caborai",
        rss_url="",
        source_type="nitter",
        category="crypto",
        impact_weight=1.5
    ),
    RSSSource(
        name="Vitalik Buterin",
        username="VitalikButerin",
        rss_url="",
        source_type="nitter",
        category="crypto",
        impact_weight=1.5
    ),
    RSSSource(
        name="Michael Saylor",
        username="saylor",
        rss_url="",
        source_type="nitter",
        category="crypto",
        impact_weight=1.5
    ),
]


@dataclass
class Tweet:
    """Parsed tweet from RSS"""
    id: str
    author: str
    username: str
    text: str
    timestamp: datetime
    url: str
    source: str


class TwitterRSSMonitor:
    """
    Monitors Twitter/X accounts via RSS feeds.
    Uses Nitter instances or RSS.app for feed generation.
    """
    
    def __init__(
        self,
        accounts: List[RSSSource] = None,
        callback: Callable = None,
        check_interval: int = 60  # Check every 60 seconds
    ):
        self.accounts = accounts or DEFAULT_ACCOUNTS
        self.callback = callback
        self.check_interval = check_interval
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        self.running = False
        self.seen_tweets: set = set()  # Track seen tweet IDs
        self.working_nitter: Optional[str] = None
        
        # Generate RSS URLs for accounts
        self._generate_rss_urls()
        
        logger.info(f"TwitterRSSMonitor initialized for {len(self.accounts)} accounts")
    
    def _generate_rss_urls(self):
        """Generate RSS URLs for each account"""
        for account in self.accounts:
            if account.source_type == "nitter" and not account.rss_url:
                # Will be set when we find a working instance
                pass
            elif account.source_type == "rss_app":
                # RSS.app format
                account.rss_url = f"https://rss.app/feeds/twitter/{account.username}.xml"
    
    async def find_working_nitter(self) -> Optional[str]:
        """Find a working Nitter instance"""
        for instance in NITTER_INSTANCES:
            try:
                url = f"https://{instance}/elonmusk/rss"
                response = await self.client.get(url)
                if response.status_code == 200 and "<?xml" in response.text[:100]:
                    logger.info(f"Found working Nitter instance: {instance}")
                    return instance
            except Exception as e:
                logger.debug(f"Nitter instance {instance} failed: {e}")
                continue
        
        logger.warning("No working Nitter instance found")
        return None
    
    async def fetch_rss(self, account: RSSSource) -> List[Tweet]:
        """Fetch and parse RSS feed for an account"""
        tweets = []
        
        try:
            # Build URL based on source type
            if account.source_type == "nitter":
                if not self.working_nitter:
                    self.working_nitter = await self.find_working_nitter()
                
                if not self.working_nitter:
                    return tweets
                
                url = f"https://{self.working_nitter}/{account.username}/rss"
            else:
                url = account.rss_url
            
            if not url:
                return tweets
            
            response = await self.client.get(url)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch RSS for {account.username}: {response.status_code}")
                return tweets
            
            # Parse RSS XML
            root = ET.fromstring(response.text)
            
            # Find all items (tweets)
            for item in root.findall(".//item"):
                try:
                    tweet = self._parse_rss_item(item, account)
                    if tweet and tweet.id not in self.seen_tweets:
                        tweets.append(tweet)
                except Exception as e:
                    logger.debug(f"Error parsing item: {e}")
                    continue
            
            logger.debug(f"Fetched {len(tweets)} new tweets from @{account.username}")
            
        except ET.ParseError as e:
            logger.warning(f"XML parse error for {account.username}: {e}")
        except Exception as e:
            logger.error(f"Error fetching RSS for {account.username}: {e}")
        
        return tweets
    
    def _parse_rss_item(self, item: ET.Element, account: RSSSource) -> Optional[Tweet]:
        """Parse a single RSS item into a Tweet"""
        try:
            # Get basic fields
            title = item.find("title")
            link = item.find("link")
            pub_date = item.find("pubDate")
            guid = item.find("guid")
            description = item.find("description")
            
            if title is None or link is None:
                return None
            
            # Parse timestamp
            timestamp = datetime.now(timezone.utc)
            if pub_date is not None and pub_date.text:
                try:
                    # RSS date format: "Tue, 10 Feb 2026 12:00:00 +0000"
                    timestamp = datetime.strptime(
                        pub_date.text, 
                        "%a, %d %b %Y %H:%M:%S %z"
                    )
                except ValueError:
                    pass
            
            # Get tweet ID from GUID or link
            tweet_id = ""
            if guid is not None and guid.text:
                tweet_id = guid.text.split("/")[-1].split("#")[0]
            elif link.text:
                tweet_id = link.text.split("/")[-1].split("#")[0]
            
            # Get text content
            text = ""
            if description is not None and description.text:
                # Clean HTML from description
                text = re.sub(r'<[^>]+>', '', description.text)
                text = text.strip()
            elif title.text:
                text = title.text
            
            return Tweet(
                id=tweet_id,
                author=account.name,
                username=account.username,
                text=text,
                timestamp=timestamp,
                url=link.text if link.text else "",
                source=account.source_type
            )
            
        except Exception as e:
            logger.debug(f"Error parsing RSS item: {e}")
            return None
    
    async def check_all_accounts(self) -> List[Tweet]:
        """Check all accounts for new tweets"""
        all_tweets = []
        
        for account in self.accounts:
            tweets = await self.fetch_rss(account)
            
            for tweet in tweets:
                # Mark as seen
                self.seen_tweets.add(tweet.id)
                all_tweets.append(tweet)
                
                # Call callback for each new tweet
                if self.callback:
                    await self.callback(tweet, account)
        
        return all_tweets
    
    async def start_monitoring(self):
        """Start continuous monitoring"""
        self.running = True
        logger.info("Twitter RSS Monitor started")
        
        # Initial check to find working instance
        await self.find_working_nitter()
        
        while self.running:
            try:
                tweets = await self.check_all_accounts()
                
                if tweets:
                    logger.info(f"Found {len(tweets)} new tweets")
                
            except Exception as e:
                logger.error(f"Monitor error: {e}")
            
            await asyncio.sleep(self.check_interval)
    
    async def stop(self):
        """Stop monitoring"""
        self.running = False
        await self.client.aclose()
        logger.info("Twitter RSS Monitor stopped")
    
    def add_account(self, name: str, username: str, category: str = "crypto", impact: float = 1.0):
        """Add a new account to monitor"""
        account = RSSSource(
            name=name,
            username=username,
            rss_url="",
            source_type="nitter",
            category=category,
            impact_weight=impact
        )
        self.accounts.append(account)
        logger.info(f"Added account to monitor: @{username}")
    
    def remove_account(self, username: str):
        """Remove an account from monitoring"""
        self.accounts = [a for a in self.accounts if a.username != username]
        logger.info(f"Removed account from monitoring: @{username}")
    
    def get_accounts(self) -> List[Dict]:
        """Get list of monitored accounts"""
        return [
            {
                "name": a.name,
                "username": a.username,
                "category": a.category,
                "impact_weight": a.impact_weight,
                "source_type": a.source_type
            }
            for a in self.accounts
        ]


# Global instance
_twitter_monitor: Optional[TwitterRSSMonitor] = None


def get_twitter_rss_monitor() -> Optional[TwitterRSSMonitor]:
    """Get global Twitter RSS monitor"""
    return _twitter_monitor


async def init_twitter_rss_monitor(callback: Callable = None) -> TwitterRSSMonitor:
    """Initialize global Twitter RSS monitor"""
    global _twitter_monitor
    _twitter_monitor = TwitterRSSMonitor(callback=callback)
    return _twitter_monitor


# Test function
async def test_rss_monitor():
    """Test the RSS monitor"""
    async def on_tweet(tweet: Tweet, account: RSSSource):
        print(f"\n🐦 New tweet from @{tweet.username}:")
        print(f"   {tweet.text[:100]}...")
        print(f"   Category: {account.category}, Impact: {account.impact_weight}x")
    
    monitor = TwitterRSSMonitor(callback=on_tweet)
    
    # Find working Nitter
    instance = await monitor.find_working_nitter()
    print(f"Working Nitter instance: {instance}")
    
    # Check all accounts once
    tweets = await monitor.check_all_accounts()
    print(f"\nFound {len(tweets)} tweets total")
    
    await monitor.stop()


if __name__ == "__main__":
    asyncio.run(test_rss_monitor())
