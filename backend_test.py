#!/usr/bin/env python3
"""
Trading AI Backend API Testing
Tests all backend APIs to ensure they're functioning correctly.
"""

import requests
import json
import sys
from datetime import datetime
import time

class TradingAPITester:
    def __init__(self, base_url="https://broker-connect-ai.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []
        self.sample_signal_ids = []
        self.trade_ids = []

    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def run_test(self, name, method, endpoint, expected_status=200, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                error_msg = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text[:200]}"
                
                self.failures.append(f"{name}: {error_msg}")
                self.log(f"❌ FAILED - {error_msg}")
                return False, None

        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            self.failures.append(f"{name}: {error_msg}")
            self.log(f"❌ FAILED - {error_msg}")
            return False, None

    def test_health_endpoint(self):
        """Test health check endpoint"""
        return self.run_test("Health Check", "GET", "/health", 200)

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API", "GET", "/", 200)

    def test_get_signals(self):
        """Test get signals endpoint"""
        return self.run_test("Get Signals", "GET", "/signals", 200)

    def test_create_sample_signals(self):
        """Test creating sample signals"""
        success, response = self.run_test("Create Sample Signals", "POST", "/demo/sample-signals", 200)
        if success and response and response.get('created', 0) > 0:
            # Store signal IDs for later use
            signals = response.get('signals', [])
            self.sample_signal_ids = [s['id'] for s in signals[:2]]  # Take first 2
            self.log(f"Created {len(signals)} sample signals")
        return success, response

    def test_get_specific_signal(self):
        """Test get specific signal"""
        if not self.sample_signal_ids:
            self.log("⚠️  No signal IDs available, skipping specific signal test")
            return True, None
        
        signal_id = self.sample_signal_ids[0]
        return self.run_test("Get Specific Signal", "GET", f"/signals/{signal_id}", 200)

    def test_execute_signal(self):
        """Test executing a signal"""
        if not self.sample_signal_ids:
            self.log("⚠️  No signal IDs available, skipping signal execution")
            return True, None
        
        signal_id = self.sample_signal_ids[0]
        trade_data = {
            "signal_id": signal_id,
            "quantity": None  # Use calculated size
        }
        success, response = self.run_test("Execute Signal", "POST", "/trades/execute", 200, trade_data)
        if success and response and response.get('id'):
            self.trade_ids.append(response['id'])
            self.log(f"Created trade: {response['id']}")
        return success, response

    def test_get_trades(self):
        """Test get trades endpoint"""
        return self.run_test("Get Trades", "GET", "/trades", 200)

    def test_get_open_trades(self):
        """Test get open trades endpoint"""
        return self.run_test("Get Open Trades", "GET", "/trades/open", 200)

    def test_get_positions(self):
        """Test get positions endpoint"""
        return self.run_test("Get Positions", "GET", "/positions", 200)

    def test_get_portfolio(self):
        """Test get portfolio endpoint"""
        return self.run_test("Get Portfolio", "GET", "/portfolio", 200)

    def test_get_portfolio_stats(self):
        """Test get portfolio stats endpoint"""
        return self.run_test("Get Portfolio Stats", "GET", "/portfolio/stats", 200)

    def test_get_settings(self):
        """Test get settings endpoint"""
        return self.run_test("Get Settings", "GET", "/settings", 200)

    def test_update_settings(self):
        """Test update settings endpoint"""
        settings_data = {
            "max_risk_per_trade_percent": 1.5,
            "max_open_positions": 10
        }
        return self.run_test("Update Settings", "PUT", "/settings", 200, settings_data)

    def test_close_trade(self):
        """Test closing a trade"""
        if not self.trade_ids:
            self.log("⚠️  No trade IDs available, skipping trade closure")
            return True, None
        
        trade_id = self.trade_ids[0]
        close_data = {
            "trade_id": trade_id,
            "exit_reason": "manual"
        }
        return self.run_test("Close Trade", "POST", "/trades/close", 200, close_data)

    def test_dismiss_signal(self):
        """Test dismissing a signal"""
        if len(self.sample_signal_ids) < 2:
            self.log("⚠️  Not enough signal IDs available, skipping signal dismissal")
            return True, None
        
        signal_id = self.sample_signal_ids[1]  # Use second signal
        return self.run_test("Dismiss Signal", "DELETE", f"/signals/{signal_id}", 200)

    def test_demo_reset(self):
        """Test demo reset endpoint"""
        return self.run_test("Demo Reset", "POST", "/demo/reset", 200)

    def run_all_tests(self):
        """Run all backend tests"""
        self.log("🚀 Starting Trading AI Backend API Tests")
        self.log(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)

        # Core API Tests
        self.test_health_endpoint()
        self.test_root_endpoint()

        # Signal Tests
        self.test_get_signals()
        self.test_create_sample_signals()
        self.test_get_specific_signal()

        # Trading Tests  
        self.test_execute_signal()
        self.test_get_trades()
        self.test_get_open_trades()

        # Position & Portfolio Tests
        self.test_get_positions()
        self.test_get_portfolio()
        self.test_get_portfolio_stats()

        # Settings Tests
        self.test_get_settings()
        self.test_update_settings()

        # Trade Management Tests
        self.test_close_trade()
        self.test_dismiss_signal()

        # Cleanup
        self.test_demo_reset()

        # Print Summary
        print("=" * 60)
        self.log("📊 TEST SUMMARY")
        self.log(f"✅ Tests Passed: {self.tests_passed}/{self.tests_run}")
        
        if self.failures:
            self.log("❌ FAILURES:")
            for failure in self.failures:
                self.log(f"   • {failure}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        self.log(f"📈 Success Rate: {success_rate:.1f}%")

        return success_rate >= 80  # 80% success rate required


def main():
    """Main test runner"""
    tester = TradingAPITester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())