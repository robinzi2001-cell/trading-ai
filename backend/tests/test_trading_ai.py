"""
Trading AI Backend Tests
Tests for Auto-Execute, Signal Parser, AI Analysis, Trade Execution, 
Telegram Bot, Channel Monitor, and Notifications
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAutoExecute:
    """Auto-Execute Status and Config tests"""
    
    def test_auto_execute_status(self):
        """Test GET /api/auto-execute/status returns correct status"""
        response = requests.get(f"{BASE_URL}/api/auto-execute/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "enabled" in data
        assert "use_binance" in data
        assert "broker" in data
        assert "ai_analyzer_available" in data
        assert "daily_trades" in data
        assert "max_daily_trades" in data
        
        # Auto-execute should be enabled (as per requirement)
        assert data["enabled"] == True
        print(f"Auto-Execute Status: enabled={data['enabled']}, broker={data['broker']}")
    
    def test_auto_execute_toggle_use_binance(self):
        """Test PUT /api/auto-execute/config toggles use_binance correctly"""
        # First, toggle to Binance
        response = requests.put(f"{BASE_URL}/api/auto-execute/config?use_binance=true")
        assert response.status_code == 200
        data = response.json()
        assert data["use_binance"] == True
        assert data["broker"] == "binance_testnet"
        print("Toggled to Binance Testnet")
        
        # Then, toggle back to Paper
        response = requests.put(f"{BASE_URL}/api/auto-execute/config?use_binance=false")
        assert response.status_code == 200
        data = response.json()
        assert data["use_binance"] == False
        assert data["broker"] == "paper"
        print("Toggled to Paper Trading")
    
    def test_auto_execute_update_min_ai_score(self):
        """Test updating min_ai_score"""
        response = requests.put(f"{BASE_URL}/api/auto-execute/config?min_ai_score=70")
        assert response.status_code == 200
        data = response.json()
        assert data["min_ai_score"] == 70
        
        # Reset to default
        response = requests.put(f"{BASE_URL}/api/auto-execute/config?min_ai_score=60")
        assert response.status_code == 200
        print("Min AI Score update test passed")
    
    def test_auto_execute_update_min_confidence(self):
        """Test updating min_confidence"""
        response = requests.put(f"{BASE_URL}/api/auto-execute/config?min_confidence=0.7")
        assert response.status_code == 200
        data = response.json()
        assert data["min_confidence"] == 0.7
        
        # Reset to default
        response = requests.put(f"{BASE_URL}/api/auto-execute/config?min_confidence=0.6")
        assert response.status_code == 200
        print("Min Confidence update test passed")


class TestTelegramBot:
    """Telegram Bot Status tests"""
    
    def test_telegram_bot_status(self):
        """Test GET /api/telegram/bot/status returns running=true"""
        response = requests.get(f"{BASE_URL}/api/telegram/bot/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "configured" in data
        assert "running" in data
        
        # Bot should be running
        assert data["configured"] == True
        assert data["running"] == True
        
        if "bot_username" in data:
            print(f"Telegram Bot: {data['bot_username']} - Running: {data['running']}")


class TestChannelMonitor:
    """Channel Monitor Status tests"""
    
    def test_channel_monitor_status(self):
        """Test GET /api/telegram/channels/status shows channels"""
        response = requests.get(f"{BASE_URL}/api/telegram/channels/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "configured" in data
        assert "running" in data
        assert "channels" in data
        
        # Should have at least 2 channels (Evening Trader, Fat Pig Signals)
        channels = data.get("channels", [])
        assert len(channels) >= 2
        
        # Verify expected channels
        channel_usernames = [ch.get("username") for ch in channels]
        assert "eveningtrader" in channel_usernames or "fatpigsignals" in channel_usernames
        
        print(f"Channel Monitor: Running={data['running']}, Channels={len(channels)}")


class TestSignalParser:
    """Signal Parser tests for Evening Trader format"""
    
    def test_parse_evening_trader_signal(self):
        """Test parsing Evening Trader signal format"""
        signal_text = """🚀 BTC/USDT LONG
Entry: 97500
SL: 95000
TP1: 100000
TP2: 103000
TP3: 105000
Leverage: 5x"""
        
        response = requests.post(
            f"{BASE_URL}/api/telegram/parse?channel=evening_trader",
            json={"text": signal_text}
        )
        assert response.status_code == 200
        
        data = response.json()
        parsed = data.get("parsed", {})
        
        assert parsed.get("asset") == "BTC/USDT"
        assert parsed.get("action") == "long"
        assert parsed.get("entry") == 97500.0
        assert parsed.get("stop_loss") == 95000.0
        assert len(parsed.get("take_profits", [])) >= 2
        assert parsed.get("leverage") == 5
        
        print(f"Parsed Signal: {parsed.get('asset')} {parsed.get('action')}")
    
    def test_parse_short_signal(self):
        """Test parsing SHORT signal"""
        signal_text = """📉 ETH/USDT SHORT
Entry: 3500
SL: 3650
TP1: 3300
TP2: 3100
Leverage: 3x"""
        
        response = requests.post(
            f"{BASE_URL}/api/telegram/parse?channel=evening_trader",
            json={"text": signal_text}
        )
        assert response.status_code == 200
        
        data = response.json()
        parsed = data.get("parsed", {})
        
        assert parsed.get("asset") == "ETH/USDT"
        assert parsed.get("action") == "short"
        assert parsed.get("stop_loss") == 3650.0
        
        print(f"Short Signal Parsed: {parsed.get('asset')} {parsed.get('action')}")


class TestAIAnalysis:
    """AI Signal Analysis tests"""
    
    def test_ai_analyze_signal(self):
        """Test POST /api/ai/analyze-signal returns score and should_execute"""
        # First get a valid signal ID
        signals_response = requests.get(f"{BASE_URL}/api/signals?executed=false&limit=10")
        assert signals_response.status_code == 200
        
        signals = signals_response.json()
        if not signals:
            pytest.skip("No signals available for AI analysis")
        
        signal_id = signals[0]["id"]
        
        # Analyze the signal
        response = requests.post(f"{BASE_URL}/api/ai/analyze-signal?signal_id={signal_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "score" in data
        assert "should_execute" in data
        assert "quality" in data
        assert "reasoning" in data
        
        # Score should be between 0-100
        assert 0 <= data["score"] <= 100
        # should_execute should be boolean
        assert isinstance(data["should_execute"], bool)
        
        print(f"AI Analysis: Score={data['score']}, Quality={data['quality']}, Execute={data['should_execute']}")
    
    def test_ai_analyze_tweet(self):
        """Test POST /api/ai/analyze-tweet for social media analysis"""
        response = requests.post(
            f"{BASE_URL}/api/ai/analyze-tweet",
            json={
                "author": "Elon Musk",
                "text": "To the moon! 🚀 #Bitcoin"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "author" in data
        
        if data.get("ai_analysis"):
            analysis = data["ai_analysis"]
            assert "impact_score" in analysis
            assert "sentiment" in analysis
            assert "suggested_action" in analysis
            print(f"Tweet Analysis: Sentiment={analysis.get('sentiment')}, Impact={analysis.get('impact_score')}")


class TestTradeExecution:
    """Trade Execution tests"""
    
    def test_execute_trade_from_signal(self):
        """Test POST /api/trades/execute creates a trade"""
        # First create a new signal
        signal_data = {
            "asset": "TEST_LINK/USDT",
            "action": "long",
            "entry": 15.0,
            "stop_loss": 13.5,
            "take_profits": [16.5, 18.0],
            "leverage": 2,
            "confidence": 0.8
        }
        
        create_response = requests.post(f"{BASE_URL}/api/signals", json=signal_data)
        assert create_response.status_code == 200
        
        signal = create_response.json()
        signal_id = signal["id"]
        
        # Execute trade
        response = requests.post(
            f"{BASE_URL}/api/trades/execute",
            json={"signal_id": signal_id, "quantity": 1.0}
        )
        assert response.status_code == 200
        
        trade = response.json()
        assert "id" in trade
        assert trade["symbol"] == "TEST_LINK/USDT"
        assert trade["side"] == "long"
        assert trade["status"] == "open"
        
        print(f"Trade Executed: {trade['id']} - {trade['symbol']} {trade['side']}")
        
        # Cleanup - dismiss signal
        requests.delete(f"{BASE_URL}/api/signals/{signal_id}")
    
    def test_get_open_trades(self):
        """Test GET /api/trades/open returns open trades"""
        response = requests.get(f"{BASE_URL}/api/trades/open")
        assert response.status_code == 200
        
        trades = response.json()
        assert isinstance(trades, list)
        
        for trade in trades:
            assert trade.get("status") == "open"
        
        print(f"Open Trades: {len(trades)}")


class TestNotifications:
    """Notification tests"""
    
    def test_send_test_notification(self):
        """Test POST /api/notifications/test sends notification"""
        chat_id = 8202282349  # User Chat-ID from context
        
        response = requests.post(f"{BASE_URL}/api/notifications/test?chat_id={chat_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") == True
        
        print(f"Test Notification sent to chat_id: {chat_id}")
    
    def test_subscribe_notification(self):
        """Test POST /api/notifications/subscribe"""
        chat_id = 8202282349
        
        response = requests.post(f"{BASE_URL}/api/notifications/subscribe?chat_id={chat_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") == True
        
        print("Notification subscription successful")


class TestPositionsAndPortfolio:
    """Positions and Portfolio tests"""
    
    def test_get_positions(self):
        """Test GET /api/positions returns open positions"""
        response = requests.get(f"{BASE_URL}/api/positions")
        assert response.status_code == 200
        
        positions = response.json()
        assert isinstance(positions, list)
        
        print(f"Open Positions: {len(positions)}")
        for pos in positions:
            print(f"  - {pos.get('symbol')}: {pos.get('side')} @ ${pos.get('entry_price', 0):,.2f}")
    
    def test_get_portfolio(self):
        """Test GET /api/portfolio returns portfolio overview"""
        response = requests.get(f"{BASE_URL}/api/portfolio")
        assert response.status_code == 200
        
        data = response.json()
        assert "current_balance" in data
        assert "initial_balance" in data
        
        print(f"Portfolio: Balance=${data.get('current_balance', 0):,.2f}")


class TestHealthAndStatus:
    """Health check and status tests"""
    
    def test_health_check(self):
        """Test GET /api/health returns healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "healthy"
        assert data.get("services", {}).get("database") == "connected"
        
        print("Health check passed")
    
    def test_root_status(self):
        """Test GET /api/ returns operational"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "operational"
        
        print("Root status check passed")


class TestInfluentialAccounts:
    """Influential Accounts tests"""
    
    def test_get_influential_accounts(self):
        """Test GET /api/ai/influential-accounts returns account list"""
        response = requests.get(f"{BASE_URL}/api/ai/influential-accounts")
        assert response.status_code == 200
        
        data = response.json()
        assert "accounts" in data
        
        accounts = data["accounts"]
        assert len(accounts) > 0
        
        # Check structure
        for acc in accounts:
            assert "username" in acc
            assert "name" in acc
            assert "category" in acc
        
        print(f"Influential Accounts: {len(accounts)}")


class TestKnownChannels:
    """Known Telegram Channels tests"""
    
    def test_get_known_channels(self):
        """Test GET /api/telegram/channels returns channel list"""
        response = requests.get(f"{BASE_URL}/api/telegram/channels")
        assert response.status_code == 200
        
        data = response.json()
        assert "channels" in data
        
        channels = data["channels"]
        # Should have at least Evening Trader and Fat Pig Signals
        assert len(channels) >= 2
        
        channel_names = [ch.get("name", "").lower() for ch in channels]
        print(f"Known Channels: {[ch.get('name') for ch in channels]}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
