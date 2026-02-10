"""
Universal Signal Parser for Trading AI
Parses trading signals from various text formats using regex patterns.
"""
import re
from typing import List, Optional
import logging

from models.signals import ParsedSignal

logger = logging.getLogger(__name__)


class SignalParser:
    """Universal signal parser for multiple formats"""
    
    def __init__(self):
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> dict:
        return {
            # Asset patterns
            'crypto': re.compile(r'\b([A-Z]{2,6})[/\-]?(USDT|USDC|BUSD|BTC|ETH)\b', re.IGNORECASE),
            'forex': re.compile(r'\b([A-Z]{6})\b'),
            'stock': re.compile(r'\b([A-Z]{1,5})\b'),
            
            # Action patterns
            'long': re.compile(r'\b(LONG|BUY|📈|🟢|KAUFEN)\b', re.IGNORECASE),
            'short': re.compile(r'\b(SHORT|SELL|📉|🔴|VERKAUFEN)\b', re.IGNORECASE),
            
            # Price patterns
            'entry': re.compile(r'(?:entry|open|price|einstieg|@)[:\s]*([0-9,.]+)', re.IGNORECASE),
            'stop_loss': re.compile(r'(?:sl|stop\s*loss|stoploss)[:\s]*([0-9,.]+)', re.IGNORECASE),
            'take_profit': re.compile(r'(?:tp|take\s*profit|target|ziel)\d*[:\s]+([0-9,.]+)', re.IGNORECASE),
            'tp_multi': re.compile(r'(?:tp|target|ziel)\d*[:\s]+([0-9,.\s]+)', re.IGNORECASE),
            
            # Leverage
            'leverage': re.compile(r'(?:leverage|lev|hebel)[:\s]*([0-9]+)x?', re.IGNORECASE),
            
            # Timeframe
            'timeframe': re.compile(r'\b(1m|5m|15m|30m|1h|4h|1d|1w)\b', re.IGNORECASE),
        }
    
    def parse(self, text: str) -> ParsedSignal:
        """Parse signal from text"""
        result = ParsedSignal(raw_text=text)
        
        try:
            result.asset = self._extract_asset(text)
            result.action = self._extract_action(text)
            result.entry = self._extract_entry(text)
            result.stop_loss = self._extract_stop_loss(text)
            result.take_profits = self._extract_take_profits(text)
            result.leverage = self._extract_leverage(text)
            result.timeframe = self._extract_timeframe(text)
            result.confidence = self._calculate_confidence(result)
            
            logger.debug(f"Parsed signal: {result.asset} {result.action}")
            
        except Exception as e:
            result.errors.append(f"Parsing error: {e}")
            logger.error(f"Failed to parse signal: {e}")
        
        return result
    
    def _extract_asset(self, text: str) -> Optional[str]:
        match = self.patterns['crypto'].search(text)
        if match:
            base = match.group(1)
            quote = match.group(2)
            return f"{base}/{quote}".upper()
        
        match = self.patterns['forex'].search(text)
        if match:
            return match.group(1).upper()
        
        words = text.upper().split()
        for word in words:
            if len(word) >= 2 and len(word) <= 5 and word.isalpha():
                return word
        
        return None
    
    def _extract_action(self, text: str) -> Optional[str]:
        if self.patterns['long'].search(text):
            return "long"
        elif self.patterns['short'].search(text):
            return "short"
        return None
    
    def _extract_entry(self, text: str) -> Optional[float]:
        match = self.patterns['entry'].search(text)
        if match:
            return self._parse_number(match.group(1))
        
        numbers = self._extract_all_numbers(text)
        if numbers:
            return numbers[0]
        
        return None
    
    def _extract_stop_loss(self, text: str) -> Optional[float]:
        match = self.patterns['stop_loss'].search(text)
        if match:
            return self._parse_number(match.group(1))
        return None
    
    def _extract_take_profits(self, text: str) -> List[float]:
        tps = []
        
        for match in self.patterns['take_profit'].finditer(text):
            num = self._parse_number(match.group(1))
            if num and num not in tps:
                tps.append(num)
        
        if not tps:
            match = self.patterns['tp_multi'].search(text)
            if match:
                tp_text = match.group(1)
                tp_parts = re.split(r'[,\s]+', tp_text.strip())
                for part in tp_parts:
                    num = self._parse_number(part)
                    if num:
                        tps.append(num)
        
        return sorted(set(tps))
    
    def _extract_leverage(self, text: str) -> Optional[int]:
        match = self.patterns['leverage'].search(text)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_timeframe(self, text: str) -> Optional[str]:
        match = self.patterns['timeframe'].search(text)
        if match:
            return match.group(1).lower()
        return None
    
    def _extract_all_numbers(self, text: str) -> List[float]:
        numbers = []
        for match in re.finditer(r'([0-9]+(?:[.,][0-9]+)?)', text):
            num = self._parse_number(match.group(1))
            if num:
                numbers.append(num)
        return numbers
    
    def _parse_number(self, text: str) -> Optional[float]:
        if not text:
            return None
        
        try:
            text = text.strip()
            
            if ',' in text and '.' in text:
                if text.rfind(',') > text.rfind('.'):
                    text = text.replace('.', '').replace(',', '.')
                else:
                    text = text.replace(',', '')
            elif ',' in text:
                if text.count(',') == 1 and len(text.split(',')[1]) == 2:
                    text = text.replace(',', '.')
                else:
                    text = text.replace(',', '')
            
            return float(text)
        except (ValueError, AttributeError):
            return None
    
    def _calculate_confidence(self, parsed: ParsedSignal) -> float:
        score = 0.0
        max_score = 10.0
        
        if parsed.asset:
            score += 2.0
        if parsed.action:
            score += 2.0
        if parsed.entry:
            score += 2.0
        if parsed.stop_loss:
            score += 2.0
        if parsed.take_profits:
            score += 1.0
            if len(parsed.take_profits) >= 2:
                score += 0.5
        if parsed.leverage:
            score += 0.5
        
        # Consistency checks
        if parsed.entry and parsed.stop_loss:
            if parsed.action == "long" and parsed.stop_loss < parsed.entry:
                score += 0.5
            elif parsed.action == "short" and parsed.stop_loss > parsed.entry:
                score += 0.5
        
        if parsed.entry and parsed.take_profits:
            if parsed.action == "long":
                if all(tp > parsed.entry for tp in parsed.take_profits):
                    score += 0.5
            elif parsed.action == "short":
                if all(tp < parsed.entry for tp in parsed.take_profits):
                    score += 0.5
        
        return min(score / max_score, 1.0)


# Singleton instance
signal_parser = SignalParser()
