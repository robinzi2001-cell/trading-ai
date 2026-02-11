"""
Trading AI Backend Tests - Iteration 3
Tests: Execute Order, Trade Close, Auto-Execute Status, Twitter RSS, AI Analysis, Telegram Bot
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndStatus:
    """Basic health and status tests"""
    
    def test_api_root(self):
        """Test API root endpoint returns operational status"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'operational'
        assert 'Trading AI' in data['message']
        print(f"SUCCESS: API root - {data['message']}")
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'services' in data
        print(f"SUCCESS: Health check - {data['status']}")


class TestAutoExecuteStatus:
    """Auto-Execute status and configuration tests"""
    
    def test_get_auto_execute_status(self):
        """Test GET /api/auto-execute/status returns use_binance and broker fields"""
        response = requests.get(f"{BASE_URL}/api/auto-execute/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert 'enabled' in data
        assert 'use_binance' in data
        assert 'broker' in data
        assert 'min_ai_score' in data
        assert 'min_confidence' in data
        assert 'ai_analyzer_available' in data
        
        print(f"SUCCESS: Auto-Execute Status - enabled={data['enabled']}, broker={data['broker']}, use_binance={data['use_binance']}")
    
    def test_update_auto_execute_config(self):
        """Test PUT /api/auto-execute/config updates settings"""
        # Get current status
        current = requests.get(f"{BASE_URL}/api/auto-execute/status").json()
        
        # Toggle use_binance
        new_use_binance = not current['use_binance']
        response = requests.put(f"{BASE_URL}/api/auto-execute/config?use_binance={str(new_use_binance).lower()}")
        assert response.status_code == 200
        data = response.json()
        assert data['use_binance'] == new_use_binance
        
        # Restore original value
        requests.put(f"{BASE_URL}/api/auto-execute/config?use_binance={str(current['use_binance']).lower()}")
        
        print(f"SUCCESS: Auto-Execute Config Update - toggled use_binance to {new_use_binance}")


class TestTwitterRSS:
    """Twitter RSS monitoring tests"""
    
    def test_get_twitter_rss_status(self):
        """Test GET /api/twitter/rss/status shows accounts and configured=true"""
        response = requests.get(f"{BASE_URL}/api/twitter/rss/status")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert 'configured' in data
        assert data['configured'] == True
        assert 'accounts' in data
        assert len(data['accounts']) > 0
        
        # Verify accounts have required fields
        for account in data['accounts']:
            assert 'username' in account
            assert 'name' in account
            assert 'category' in account
        
        print(f"SUCCESS: Twitter RSS Status - configured={data['configured']}, accounts={len(data['accounts'])}")
        print(f"  Accounts: {[a['username'] for a in data['accounts'][:3]]}...")
    
    def test_check_twitter_rss(self):
        """Test POST /api/twitter/rss/check returns tweets (may be 0 if Nitter down)"""
        response = requests.post(f"{BASE_URL}/api/twitter/rss/check")
        assert response.status_code == 200
        data = response.json()
        
        assert 'success' in data
        assert data['success'] == True
        assert 'tweets_found' in data
        assert 'tweets' in data
        
        print(f"SUCCESS: Twitter RSS Check - tweets_found={data['tweets_found']}")


class TestTelegramBot:
    """Telegram bot status tests"""
    
    def test_telegram_bot_status(self):
        """Test GET /api/telegram/bot/status shows running=true"""
        response = requests.get(f"{BASE_URL}/api/telegram/bot/status")
        assert response.status_code == 200
        data = response.json()
        
        assert 'configured' in data
        assert 'running' in data
        
        if data['running']:
            assert 'bot_username' in data
            print(f"SUCCESS: Telegram Bot - running={data['running']}, username={data.get('bot_username')}")
        else:
            print(f"INFO: Telegram Bot - running=False (may not be configured)")


class TestAIAnalysis:
    """AI analysis endpoints tests"""
    
    def test_ai_analyze_signal(self):
        """Test POST /api/ai/analyze-signal returns score, quality, should_execute"""
        # First create a test signal
        signal_data = {
            "asset": "TEST_AI/USDT",
            "action": "long",
            "entry": 100.0,
            "stop_loss": 95.0,
            "take_profits": [105.0, 110.0],
            "leverage": 2,
            "confidence": 0.8,
            "source": "manual",
            "original_text": "TEST AI Signal"
        }
        create_response = requests.post(f"{BASE_URL}/api/signals", json=signal_data)
        assert create_response.status_code == 200
        signal = create_response.json()
        signal_id = signal['id']
        
        # Analyze the signal
        response = requests.post(f"{BASE_URL}/api/ai/analyze-signal?signal_id={signal_id}")
        assert response.status_code == 200
        data = response.json()
        
        # Verify AI analysis fields
        assert 'score' in data
        assert 'quality' in data
        assert 'should_execute' in data
        assert 'reasoning' in data
        assert isinstance(data['score'], (int, float))
        assert data['quality'] in ['excellent', 'good', 'moderate', 'poor', 'risky']
        assert isinstance(data['should_execute'], bool)
        
        print(f"SUCCESS: AI Signal Analysis - score={data['score']}, quality={data['quality']}, should_execute={data['should_execute']}")
        
        # Cleanup - dismiss the signal
        requests.delete(f"{BASE_URL}/api/signals/{signal_id}")
    
    def test_ai_analyze_tweet(self):
        """Test POST /api/ai/analyze-tweet returns impact_score and suggested_action"""
        tweet_data = {
            "author": "Elon Musk",
            "text": "Bitcoin is the future! $BTC will go to $200,000 this year!"
        }
        
        response = requests.post(f"{BASE_URL}/api/ai/analyze-tweet", json=tweet_data)
        assert response.status_code == 200
        data = response.json()
        
        assert 'author' in data
        assert data['author'] == "Elon Musk"
        
        # Check AI analysis
        if data.get('ai_analysis'):
            ai = data['ai_analysis']
            assert 'impact_score' in ai
            assert 'sentiment' in ai
            assert 'suggested_action' in ai
            print(f"SUCCESS: AI Tweet Analysis - impact={ai['impact_score']}, sentiment={ai['sentiment']}, action={ai['suggested_action']}")
        else:
            print(f"INFO: AI Tweet Analysis - no AI analysis returned (may be limited)")


class TestTradeExecution:
    """Trade execution and close tests"""
    
    def test_execute_order(self):
        """Test POST /api/trades/execute creates trade and opens position"""
        # Create a test signal
        signal_data = {
            "asset": "TEST_EXEC/USDT",
            "action": "long",
            "entry": 50.0,
            "stop_loss": 45.0,
            "take_profits": [55.0, 60.0],
            "leverage": 2,
            "confidence": 0.85,
            "source": "manual",
            "original_text": "TEST Execute Order Signal"
        }
        create_response = requests.post(f"{BASE_URL}/api/signals", json=signal_data)
        assert create_response.status_code == 200
        signal = create_response.json()
        signal_id = signal['id']
        
        # Execute the trade
        execute_data = {
            "signal_id": signal_id,
            "quantity": 1.0
        }
        response = requests.post(f"{BASE_URL}/api/trades/execute", json=execute_data)
        assert response.status_code == 200
        trade = response.json()
        
        # Verify trade fields
        assert 'id' in trade
        assert trade['symbol'] == "TEST_EXEC/USDT"
        assert trade['side'] == "long"
        assert trade['status'] == "open"
        assert 'entry_price' in trade
        assert 'stop_loss' in trade
        
        print(f"SUCCESS: Execute Order - trade_id={trade['id']}, symbol={trade['symbol']}, status={trade['status']}")
        
        # Store trade_id for close test
        self.__class__.test_trade_id = trade['id']
    
    def test_close_trade(self):
        """Test POST /api/trades/close closes position with P&L"""
        trade_id = getattr(self.__class__, 'test_trade_id', None)
        
        if not trade_id:
            pytest.skip("No trade to close (execute test may have failed)")
        
        # Close the trade
        close_data = {
            "trade_id": trade_id,
            "exit_reason": "manual"
        }
        response = requests.post(f"{BASE_URL}/api/trades/close", json=close_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data['success'] == True
        assert 'trade' in data
        trade = data['trade']
        
        # Verify closed trade fields
        assert trade['status'] == 'closed'
        assert trade['exit_reason'] == 'manual'
        assert 'exit_price' in trade
        assert 'realized_pnl' in trade
        assert 'realized_pnl_percent' in trade
        
        print(f"SUCCESS: Trade Close - exit_price={trade['exit_price']:.2f}, pnl={trade['realized_pnl']:.4f}")


class TestPositionsAndPortfolio:
    """Positions and portfolio tests"""
    
    def test_get_open_trades(self):
        """Test GET /api/trades/open returns open trades"""
        response = requests.get(f"{BASE_URL}/api/trades/open")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Get Open Trades - count={len(data)}")
    
    def test_get_positions(self):
        """Test GET /api/positions returns positions"""
        response = requests.get(f"{BASE_URL}/api/positions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Get Positions - count={len(data)}")
    
    def test_get_portfolio(self):
        """Test GET /api/portfolio returns portfolio"""
        response = requests.get(f"{BASE_URL}/api/portfolio")
        assert response.status_code == 200
        data = response.json()
        
        assert 'initial_balance' in data
        assert 'current_balance' in data
        print(f"SUCCESS: Get Portfolio - balance=${data['current_balance']:,.2f}")


class TestSignals:
    """Signal management tests"""
    
    def test_get_signals(self):
        """Test GET /api/signals returns signals list"""
        response = requests.get(f"{BASE_URL}/api/signals?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Get Signals - count={len(data)}")
    
    def test_create_and_dismiss_signal(self):
        """Test signal create and dismiss flow"""
        # Create
        signal_data = {
            "asset": "TEST_DISMISS/USDT",
            "action": "short",
            "entry": 100.0,
            "stop_loss": 110.0,
            "take_profits": [90.0],
            "leverage": 1,
            "confidence": 0.6,
            "source": "manual"
        }
        create_response = requests.post(f"{BASE_URL}/api/signals", json=signal_data)
        assert create_response.status_code == 200
        signal = create_response.json()
        
        # Dismiss
        dismiss_response = requests.delete(f"{BASE_URL}/api/signals/{signal['id']}")
        assert dismiss_response.status_code == 200
        
        print(f"SUCCESS: Signal Create & Dismiss - id={signal['id']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
