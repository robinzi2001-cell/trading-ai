"""
Trading AI Backend Tests - Telegram Channel Management & Alpaca Broker
Tests for: 
- Health check
- Telegram Channel CRUD (list, add, delete, toggle)
- Alpaca Broker endpoints (balance, positions, config)
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_health_check_returns_healthy(self, api_client):
        """Test GET /api/health returns healthy status"""
        response = api_client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "services" in data
        assert data["services"]["database"] == "connected"
        assert data["services"]["trading_engine"] == "operational"
        assert data["services"]["signal_parser"] == "ready"
        print("✓ Health check returns healthy status with all services operational")


class TestTelegramChannelManagement:
    """Telegram Channel CRUD endpoint tests"""
    
    def test_list_channels_returns_list(self, api_client):
        """Test GET /api/telegram/channels/list returns channel list"""
        response = api_client.get(f"{BASE_URL}/api/telegram/channels/list")
        assert response.status_code == 200
        
        data = response.json()
        assert "channels" in data
        assert "count" in data
        assert isinstance(data["channels"], list)
        print(f"✓ Channel list returned {data['count']} channels")
    
    def test_add_channel_success(self, api_client):
        """Test POST /api/telegram/channels/add creates new channel"""
        test_username = f"test_pytest_{uuid.uuid4().hex[:8]}"
        
        response = api_client.post(
            f"{BASE_URL}/api/telegram/channels/add",
            json={
                "username": test_username,
                "name": "PyTest Channel",
                "enabled": True
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "message" in data
        assert "channel" in data
        assert data["channel"]["username"] == test_username
        assert data["channel"]["name"] == "PyTest Channel"
        assert data["channel"]["enabled"] == True
        print(f"✓ Channel @{test_username} added successfully")
        
        # Cleanup - delete the channel
        cleanup_response = api_client.delete(f"{BASE_URL}/api/telegram/channels/{test_username}")
        assert cleanup_response.status_code == 200
        print(f"✓ Cleanup: Channel @{test_username} deleted")
    
    def test_add_channel_duplicate_fails(self, api_client):
        """Test POST /api/telegram/channels/add fails for duplicate channel"""
        test_username = f"test_dup_{uuid.uuid4().hex[:8]}"
        
        # First add
        response1 = api_client.post(
            f"{BASE_URL}/api/telegram/channels/add",
            json={"username": test_username, "enabled": True}
        )
        assert response1.status_code == 200
        
        # Second add - should fail
        response2 = api_client.post(
            f"{BASE_URL}/api/telegram/channels/add",
            json={"username": test_username, "enabled": True}
        )
        assert response2.status_code == 400
        
        data = response2.json()
        assert "detail" in data
        assert "existiert bereits" in data["detail"]
        print(f"✓ Duplicate channel @{test_username} correctly rejected")
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/telegram/channels/{test_username}")
    
    def test_add_channel_empty_username_fails(self, api_client):
        """Test POST /api/telegram/channels/add fails for empty username"""
        response = api_client.post(
            f"{BASE_URL}/api/telegram/channels/add",
            json={"username": "", "enabled": True}
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        print("✓ Empty username correctly rejected")
    
    def test_delete_channel_success(self, api_client):
        """Test DELETE /api/telegram/channels/{username} removes channel"""
        test_username = f"test_del_{uuid.uuid4().hex[:8]}"
        
        # First add a channel
        api_client.post(
            f"{BASE_URL}/api/telegram/channels/add",
            json={"username": test_username, "enabled": True}
        )
        
        # Now delete it
        response = api_client.delete(f"{BASE_URL}/api/telegram/channels/{test_username}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "entfernt" in data["message"]
        print(f"✓ Channel @{test_username} deleted successfully")
        
        # Verify it's gone
        list_response = api_client.get(f"{BASE_URL}/api/telegram/channels/list")
        channels = list_response.json()["channels"]
        usernames = [ch["username"] for ch in channels]
        assert test_username not in usernames
        print(f"✓ Verified channel @{test_username} no longer in list")
    
    def test_delete_nonexistent_channel_fails(self, api_client):
        """Test DELETE /api/telegram/channels/{username} returns 404 for nonexistent channel"""
        response = api_client.delete(f"{BASE_URL}/api/telegram/channels/nonexistent_channel_xyz123")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "nicht gefunden" in data["detail"]
        print("✓ Delete nonexistent channel correctly returns 404")
    
    def test_toggle_channel_success(self, api_client):
        """Test PUT /api/telegram/channels/{username}/toggle toggles enabled status"""
        test_username = f"test_toggle_{uuid.uuid4().hex[:8]}"
        
        # First add a channel (enabled=True)
        api_client.post(
            f"{BASE_URL}/api/telegram/channels/add",
            json={"username": test_username, "enabled": True}
        )
        
        # Toggle to disable
        response1 = api_client.put(f"{BASE_URL}/api/telegram/channels/{test_username}/toggle")
        assert response1.status_code == 200
        
        data1 = response1.json()
        assert data1["success"] == True
        assert data1["enabled"] == False
        assert "deaktiviert" in data1["message"]
        print(f"✓ Channel @{test_username} toggled to disabled")
        
        # Toggle back to enable
        response2 = api_client.put(f"{BASE_URL}/api/telegram/channels/{test_username}/toggle")
        assert response2.status_code == 200
        
        data2 = response2.json()
        assert data2["success"] == True
        assert data2["enabled"] == True
        assert "aktiviert" in data2["message"]
        print(f"✓ Channel @{test_username} toggled back to enabled")
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/telegram/channels/{test_username}")
    
    def test_toggle_nonexistent_channel_fails(self, api_client):
        """Test PUT /api/telegram/channels/{username}/toggle returns 404 for nonexistent channel"""
        response = api_client.put(f"{BASE_URL}/api/telegram/channels/nonexistent_toggle_xyz123/toggle")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "nicht gefunden" in data["detail"]
        print("✓ Toggle nonexistent channel correctly returns 404")


class TestAlpacaBroker:
    """Alpaca Broker endpoint tests"""
    
    def test_broker_config_returns_status(self, api_client):
        """Test GET /api/broker/config returns broker configuration"""
        response = api_client.get(f"{BASE_URL}/api/broker/config")
        assert response.status_code == 200
        
        data = response.json()
        assert data["broker"] == "alpaca"
        assert data["configured"] == True
        assert data["paper"] == True
        assert data["network"] == "paper"
        assert "features" in data
        assert data["features"]["stocks"] == True
        assert data["features"]["crypto"] == True
        print("✓ Broker config shows Alpaca configured for paper trading")
    
    def test_broker_balance_returns_account_info(self, api_client):
        """Test GET /api/broker/balance returns account balance"""
        response = api_client.get(f"{BASE_URL}/api/broker/balance")
        assert response.status_code == 200
        
        data = response.json()
        assert "total" in data
        assert "available" in data
        assert "buying_power" in data
        assert "portfolio_value" in data
        assert "currency" in data
        assert data["currency"] == "USD"
        assert data["account_status"] == "ACTIVE"
        assert isinstance(data["total"], (int, float))
        assert data["total"] > 0
        print(f"✓ Broker balance: ${data['total']:.2f} (buying power: ${data['buying_power']:.2f})")
    
    def test_broker_positions_returns_list(self, api_client):
        """Test GET /api/broker/positions returns positions list"""
        response = api_client.get(f"{BASE_URL}/api/broker/positions")
        assert response.status_code == 200
        
        data = response.json()
        assert "positions" in data
        assert isinstance(data["positions"], list)
        
        if len(data["positions"]) > 0:
            position = data["positions"][0]
            assert "symbol" in position
            assert "side" in position
            assert "quantity" in position
            assert "entry_price" in position
            assert "current_price" in position
            assert "unrealized_pnl" in position
            print(f"✓ Broker positions: {len(data['positions'])} positions found")
            for p in data["positions"]:
                print(f"  - {p['symbol']}: {p['quantity']} @ ${p['current_price']:.2f} (P&L: ${p['unrealized_pnl']:.2f})")
        else:
            print("✓ Broker positions: No open positions")


class TestTelegramChannelStatus:
    """Telegram Channel Monitor Status tests"""
    
    def test_channel_status_returns_info(self, api_client):
        """Test GET /api/telegram/channels/status returns monitor status"""
        response = api_client.get(f"{BASE_URL}/api/telegram/channels/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "configured" in data
        assert "saved_channels" in data
        
        print(f"✓ Channel monitor status:")
        print(f"  - Configured: {data.get('configured')}")
        print(f"  - Authorized: {data.get('authorized')}")
        print(f"  - Running: {data.get('running')}")
        print(f"  - Saved channels: {len(data.get('saved_channels', []))}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
