"""
AI Signal Analyzer for Trading AI
Uses GPT to analyze trading signals, social media posts, and market sentiment.
"""
import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)


class SignalQuality(str, Enum):
    EXCELLENT = "excellent"  # 90-100% - Execute immediately
    GOOD = "good"           # 70-89% - Execute with standard size
    MODERATE = "moderate"   # 50-69% - Execute with reduced size
    POOR = "poor"           # 30-49% - Skip or manual review
    REJECT = "reject"       # 0-29% - Do not execute


@dataclass
class SignalAnalysis:
    """Result of AI signal analysis"""
    quality: SignalQuality
    score: float  # 0-100
    should_execute: bool
    reasoning: str
    risk_assessment: str
    suggested_position_size: float  # Multiplier (0.5 = half size, 1.0 = full, 1.5 = 1.5x)
    market_sentiment: str
    warnings: List[str]


@dataclass
class SocialMediaAnalysis:
    """Result of social media post analysis"""
    impact_score: float  # -100 to +100 (negative = bearish, positive = bullish)
    affected_assets: List[str]
    sentiment: str  # bullish, bearish, neutral
    urgency: str  # immediate, short-term, long-term
    trading_opportunity: bool
    suggested_action: str  # long, short, wait
    reasoning: str
    confidence: float


class AISignalAnalyzer:
    """
    AI-powered signal and market analyzer using GPT.
    """
    
    SYSTEM_PROMPT = """Du bist ein erfahrener Trading-Analyst und Risk Manager. 
Deine Aufgabe ist es, Trading-Signale zu analysieren und deren Qualität zu bewerten.

Bewerte Signale basierend auf:
1. Risk/Reward Ratio (mindestens 1:1.5 für gute Signale)
2. Klarheit der Entry, Stop-Loss und Take-Profit Levels
3. Marktkontext und aktuelle Bedingungen
4. Technische Validität der Levels

Antworte IMMER im folgenden JSON-Format:
{
    "score": 0-100,
    "quality": "excellent|good|moderate|poor|reject",
    "should_execute": true/false,
    "reasoning": "Kurze Begründung",
    "risk_assessment": "Risikobewertung",
    "position_size_multiplier": 0.5-1.5,
    "warnings": ["Warnung 1", "Warnung 2"]
}"""

    SOCIAL_MEDIA_PROMPT = """Du bist ein Marktanalyst spezialisiert auf Social Media Sentiment.
Analysiere Posts von einflussreichen Personen (Trump, Elon Musk, etc.) auf potenzielle Marktauswirkungen.

Bewerte:
1. Welche Assets könnten betroffen sein (Crypto, Aktien, etc.)
2. Richtung der Auswirkung (bullish/bearish)
3. Stärke und Dringlichkeit
4. Trading-Möglichkeit

Antworte IMMER im JSON-Format:
{
    "impact_score": -100 bis +100,
    "affected_assets": ["BTC", "DOGE", etc.],
    "sentiment": "bullish|bearish|neutral",
    "urgency": "immediate|short-term|long-term",
    "trading_opportunity": true/false,
    "suggested_action": "long|short|wait",
    "reasoning": "Analyse",
    "confidence": 0-100
}"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get('EMERGENT_LLM_KEY')
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY not set")
        
        logger.info("AI Signal Analyzer initialized")
    
    async def analyze_signal(self, signal: Dict[str, Any]) -> SignalAnalysis:
        """Analyze a trading signal using AI"""
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"signal_analysis_{datetime.now().timestamp()}",
                system_message=self.SYSTEM_PROMPT
            ).with_model("openai", "gpt-5.2")
            
            # Build signal description
            signal_text = f"""
Analysiere dieses Trading-Signal:

Asset: {signal.get('asset', 'Unknown')}
Aktion: {signal.get('action', 'Unknown')}
Entry: ${signal.get('entry', 0):,.2f}
Stop Loss: ${signal.get('stop_loss', 0):,.2f}
Take Profits: {signal.get('take_profits', [])}
Leverage: {signal.get('leverage', 1)}x
Quelle: {signal.get('source', 'Unknown')}
Confidence (Parser): {signal.get('confidence', 0)*100:.0f}%

Original Text:
{signal.get('original_text', 'N/A')[:500]}
"""
            
            user_message = UserMessage(text=signal_text)
            response = await chat.send_message(user_message)
            
            # Parse response
            import json
            try:
                # Extract JSON from response
                json_str = response
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    json_str = response.split("```")[1].split("```")[0]
                
                data = json.loads(json_str.strip())
            except:
                # Default response if parsing fails
                data = {
                    "score": signal.get('confidence', 0.5) * 100,
                    "quality": "moderate",
                    "should_execute": signal.get('confidence', 0) >= 0.6,
                    "reasoning": "AI Analyse nicht verfügbar",
                    "risk_assessment": "Standard",
                    "position_size_multiplier": 1.0,
                    "warnings": []
                }
            
            # Map quality
            quality_map = {
                "excellent": SignalQuality.EXCELLENT,
                "good": SignalQuality.GOOD,
                "moderate": SignalQuality.MODERATE,
                "poor": SignalQuality.POOR,
                "reject": SignalQuality.REJECT
            }
            
            return SignalAnalysis(
                quality=quality_map.get(data.get('quality', 'moderate'), SignalQuality.MODERATE),
                score=data.get('score', 50),
                should_execute=data.get('should_execute', False),
                reasoning=data.get('reasoning', ''),
                risk_assessment=data.get('risk_assessment', ''),
                suggested_position_size=data.get('position_size_multiplier', 1.0),
                market_sentiment=data.get('market_sentiment', 'neutral'),
                warnings=data.get('warnings', [])
            )
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            # Return default analysis
            return SignalAnalysis(
                quality=SignalQuality.MODERATE,
                score=signal.get('confidence', 0.5) * 100,
                should_execute=signal.get('confidence', 0) >= 0.7,
                reasoning=f"Fallback: Parser confidence {signal.get('confidence', 0)*100:.0f}%",
                risk_assessment="Nicht analysiert",
                suggested_position_size=1.0,
                market_sentiment="unknown",
                warnings=["AI Analyse fehlgeschlagen"]
            )
    
    async def analyze_social_post(self, post: Dict[str, Any]) -> SocialMediaAnalysis:
        """Analyze a social media post for market impact"""
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"social_analysis_{datetime.now().timestamp()}",
                system_message=self.SOCIAL_MEDIA_PROMPT
            ).with_model("openai", "gpt-5.2")
            
            post_text = f"""
Analysiere diesen Social Media Post:

Autor: {post.get('author', 'Unknown')}
Plattform: {post.get('platform', 'X/Twitter')}
Zeitpunkt: {post.get('timestamp', 'Unknown')}
Follower: {post.get('followers', 'Unknown')}

Post-Inhalt:
{post.get('text', '')}

Kontext: {post.get('context', 'Keine zusätzlichen Informationen')}
"""
            
            user_message = UserMessage(text=post_text)
            response = await chat.send_message(user_message)
            
            # Parse response
            import json
            try:
                json_str = response
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    json_str = response.split("```")[1].split("```")[0]
                
                data = json.loads(json_str.strip())
            except:
                data = {
                    "impact_score": 0,
                    "affected_assets": [],
                    "sentiment": "neutral",
                    "urgency": "long-term",
                    "trading_opportunity": False,
                    "suggested_action": "wait",
                    "reasoning": "Analyse nicht verfügbar",
                    "confidence": 0
                }
            
            return SocialMediaAnalysis(
                impact_score=data.get('impact_score', 0),
                affected_assets=data.get('affected_assets', []),
                sentiment=data.get('sentiment', 'neutral'),
                urgency=data.get('urgency', 'long-term'),
                trading_opportunity=data.get('trading_opportunity', False),
                suggested_action=data.get('suggested_action', 'wait'),
                reasoning=data.get('reasoning', ''),
                confidence=data.get('confidence', 0)
            )
            
        except Exception as e:
            logger.error(f"Social media analysis failed: {e}")
            return SocialMediaAnalysis(
                impact_score=0,
                affected_assets=[],
                sentiment="neutral",
                urgency="long-term",
                trading_opportunity=False,
                suggested_action="wait",
                reasoning=f"Fehler: {e}",
                confidence=0
            )
    
    async def quick_score(self, signal: Dict[str, Any]) -> float:
        """Quick scoring without full AI analysis"""
        score = 0.0
        
        # Base confidence from parser
        score += signal.get('confidence', 0) * 40
        
        # Risk/Reward check
        entry = signal.get('entry', 0)
        sl = signal.get('stop_loss', 0)
        tps = signal.get('take_profits', [])
        
        if entry and sl and tps:
            risk = abs(entry - sl)
            reward = abs(tps[0] - entry) if tps else 0
            
            if risk > 0:
                rr_ratio = reward / risk
                if rr_ratio >= 2.0:
                    score += 30
                elif rr_ratio >= 1.5:
                    score += 20
                elif rr_ratio >= 1.0:
                    score += 10
        
        # Source bonus
        source = signal.get('source', '')
        if 'evening' in source.lower() or 'fat pig' in source.lower():
            score += 15  # Known good sources
        
        # Completeness bonus
        if all([entry, sl, tps]):
            score += 15
        
        return min(score, 100)


# Singleton instance
_analyzer: Optional[AISignalAnalyzer] = None


def get_ai_analyzer() -> Optional[AISignalAnalyzer]:
    """Get global analyzer instance"""
    global _analyzer
    if _analyzer is None:
        try:
            _analyzer = AISignalAnalyzer()
        except Exception as e:
            logger.error(f"Failed to init AI analyzer: {e}")
    return _analyzer


async def analyze_signal(signal: Dict) -> SignalAnalysis:
    """Convenience function to analyze a signal"""
    analyzer = get_ai_analyzer()
    if analyzer:
        return await analyzer.analyze_signal(signal)
    return None


async def analyze_social_post(post: Dict) -> SocialMediaAnalysis:
    """Convenience function to analyze social media"""
    analyzer = get_ai_analyzer()
    if analyzer:
        return await analyzer.analyze_social_post(post)
    return None
