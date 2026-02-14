"""
Telegram Signal Parser - Parses trading signals from various Telegram channels.
"""
import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    CRYPTO = "crypto"
    FOREX = "forex"
    STOCKS = "stocks"


@dataclass
class ChannelInfo:
    """Information about a known signal channel"""
    name: str
    username: str
    signal_type: SignalType
    format_hints: List[str]


# Known trading channels
KNOWN_CHANNELS = {
    "evening_trader": ChannelInfo(
        name="Evening Trader",
        username="eveningtrader",
        signal_type=SignalType.CRYPTO,
        format_hints=["ASSET ACTION", "Entry: X", "SL: X", "TP: X"]
    ),
    "fat_pig_signals": ChannelInfo(
        name="Fat Pig Signals",
        username="fatpigsignals",
        signal_type=SignalType.CRYPTO,
        format_hints=["🐷", "ASSET", "Entry Zone", "Targets"]
    ),
}


class TelegramSignalParser:
    """Parser for various Telegram signal formats"""
    
    @staticmethod
    def parse_evening_trader(text: str) -> dict:
        """Parse Evening Trader format signals"""
        result = {
            "asset": None,
            "action": None,
            "entry": None,
            "stop_loss": None,
            "take_profits": [],
            "leverage": 1,
            "confidence": 0.0
        }
        
        text_upper = text.upper()
        lines = text.strip().split('\n')
        
        # Find asset
        asset_patterns = [
            r'([A-Z]{2,10})[/\s]?(USDT|USD|BTC|ETH)',
            r'#([A-Z]{2,10})',
            r'\$([A-Z]{2,10})',
        ]
        
        for pattern in asset_patterns:
            match = re.search(pattern, text_upper)
            if match:
                asset = match.group(1)
                suffix = match.group(2) if len(match.groups()) > 1 else 'USDT'
                result["asset"] = f"{asset}/{suffix}"
                break
        
        # Find action
        if any(x in text_upper for x in ['LONG', 'BUY', 'BULLISH', '🟢', '📈']):
            result["action"] = "long"
        elif any(x in text_upper for x in ['SHORT', 'SELL', 'BEARISH', '🔴', '📉']):
            result["action"] = "short"
        
        # Extract numbers
        numbers = re.findall(r'[\d,]+\.?\d*', text)
        numbers = [float(n.replace(',', '')) for n in numbers if n]
        
        # Find entry
        entry_patterns = [
            r'ENTRY[:\s]*\$?([\d,]+\.?\d*)',
            r'EINSTIEG[:\s]*\$?([\d,]+\.?\d*)',
            r'@[:\s]*([\d,]+\.?\d*)',
            r'PREIS[:\s]*\$?([\d,]+\.?\d*)',
        ]
        
        for pattern in entry_patterns:
            match = re.search(pattern, text_upper)
            if match:
                result["entry"] = float(match.group(1).replace(',', ''))
                break
        
        # Find stop loss
        sl_patterns = [
            r'SL[:\s]*\$?([\d,]+\.?\d*)',
            r'STOP[:\s]*\$?([\d,]+\.?\d*)',
            r'STOPLOSS[:\s]*\$?([\d,]+\.?\d*)',
        ]
        
        for pattern in sl_patterns:
            match = re.search(pattern, text_upper)
            if match:
                result["stop_loss"] = float(match.group(1).replace(',', ''))
                break
        
        # Find take profits
        tp_patterns = [
            r'TP\d?[:\s]*\$?([\d,]+\.?\d*)',
            r'TARGET\d?[:\s]*\$?([\d,]+\.?\d*)',
            r'ZIEL\d?[:\s]*\$?([\d,]+\.?\d*)',
        ]
        
        for pattern in tp_patterns:
            matches = re.findall(pattern, text_upper)
            for m in matches:
                tp = float(m.replace(',', ''))
                if tp not in result["take_profits"]:
                    result["take_profits"].append(tp)
        
        # Find leverage
        lev_match = re.search(r'(\d+)[Xx]|LEVERAGE[:\s]*(\d+)', text_upper)
        if lev_match:
            result["leverage"] = int(lev_match.group(1) or lev_match.group(2))
        
        # Calculate confidence
        confidence = 0.0
        if result["asset"]:
            confidence += 0.25
        if result["action"]:
            confidence += 0.25
        if result["entry"]:
            confidence += 0.25
        if result["stop_loss"]:
            confidence += 0.15
        if result["take_profits"]:
            confidence += 0.10
        
        result["confidence"] = min(confidence, 1.0)
        
        return result
    
    @staticmethod
    def parse_fat_pig_signals(text: str) -> dict:
        """Parse Fat Pig Signals format"""
        # Similar structure to evening_trader
        return TelegramSignalParser.parse_evening_trader(text)
    
    @staticmethod
    def parse_generic(text: str) -> dict:
        """Generic signal parser - works for most formats"""
        return TelegramSignalParser.parse_evening_trader(text)
