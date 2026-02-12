"""
Binance Broker Integration for Trading AI
Supports Spot Testnet trading (Futures not available in all regions).
"""
import asyncio
import os
import hmac
import hashlib
import time
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class BinanceNetwork(str, Enum):
    SPOT_TESTNET = "spot_testnet"
    SPOT_LIVE = "spot_live"
    FUTURES_TESTNET = "futures_testnet"  # Not available in all regions
    FUTURES_LIVE = "futures_live"


@dataclass
class BinanceConfig:
    """Binance API configuration"""
    api_key: str
    api_secret: str
    network: BinanceNetwork = BinanceNetwork.SPOT_TESTNET
    
    @property
    def base_url(self) -> str:
        urls = {
            BinanceNetwork.SPOT_TESTNET: "https://testnet.binance.vision",
            BinanceNetwork.SPOT_LIVE: "https://api.binance.com",
            BinanceNetwork.FUTURES_TESTNET: "https://testnet.binancefuture.com",
            BinanceNetwork.FUTURES_LIVE: "https://fapi.binance.com",
        }
        return urls.get(self.network, "https://testnet.binance.vision")
    
    @property
    def is_futures(self) -> bool:
        return "futures" in self.network.value
    
    @property
    def is_testnet(self) -> bool:
        return "testnet" in self.network.value


class BinanceBroker:
    """
    Binance Futures broker integration.
    
    Supports:
    - Account info and balance
    - Market and limit orders
    - Position management
    - Price data
    """
    
    def __init__(self, config: BinanceConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=30.0)
        
        logger.info(f"BinanceBroker initialized ({config.network.value})")
    
    def _sign_request(self, params: dict) -> dict:
        """Sign request with HMAC SHA256"""
        params['timestamp'] = int(time.time() * 1000)
        
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        
        signature = hmac.new(
            self.config.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        params['signature'] = signature
        return params
    
    def _get_headers(self) -> dict:
        """Get request headers"""
        return {
            'X-MBX-APIKEY': self.config.api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    
    async def _request(self, method: str, endpoint: str, params: dict = None, signed: bool = False) -> dict:
        """Make API request"""
        url = f"{self.config.base_url}{endpoint}"
        params = params or {}
        
        if signed:
            params = self._sign_request(params)
        
        headers = self._get_headers()
        
        try:
            if method == 'GET':
                response = await self.client.get(url, params=params, headers=headers)
            elif method == 'POST':
                response = await self.client.post(url, data=params, headers=headers)
            elif method == 'DELETE':
                response = await self.client.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.content else {}
            logger.error(f"Binance API error: {error_data}")
            raise BinanceAPIError(error_data.get('msg', str(e)), error_data.get('code'))
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    # ==================== Account ====================
    
    async def get_account_info(self) -> dict:
        """Get account information"""
        if self.config.is_futures:
            return await self._request('GET', '/fapi/v2/account', signed=True)
        else:
            # Spot account
            return await self._request('GET', '/api/v3/account', signed=True)
    
    async def get_balance(self) -> dict:
        """Get account balance"""
        account = await self.get_account_info()
        
        if self.config.is_futures:
            usdt_balance = next(
                (a for a in account.get('assets', []) if a['asset'] == 'USDT'),
                {'walletBalance': '0', 'availableBalance': '0'}
            )
            
            return {
                'total': float(usdt_balance['walletBalance']),
                'available': float(usdt_balance['availableBalance']),
                'unrealized_pnl': float(account.get('totalUnrealizedProfit', 0)),
                'margin_balance': float(account.get('totalMarginBalance', 0))
            }
        else:
            # Spot account - look for USDT balance
            usdt_balance = next(
                (b for b in account.get('balances', []) if b['asset'] == 'USDT'),
                {'free': '0', 'locked': '0'}
            )
            
            total = float(usdt_balance['free']) + float(usdt_balance['locked'])
            
            return {
                'total': total,
                'available': float(usdt_balance['free']),
                'locked': float(usdt_balance['locked']),
                'unrealized_pnl': 0,
                'margin_balance': total
            }
    
    async def get_positions(self) -> List[dict]:
        """Get open positions (Spot: returns open orders as pseudo-positions)"""
        if self.config.is_futures:
            account = await self.get_account_info()
            positions = []
            
            for pos in account.get('positions', []):
                amt = float(pos['positionAmt'])
                if amt != 0:
                    positions.append({
                        'symbol': pos['symbol'],
                        'side': 'long' if amt > 0 else 'short',
                        'quantity': abs(amt),
                        'entry_price': float(pos['entryPrice']),
                        'mark_price': float(pos.get('markPrice', 0)),
                        'unrealized_pnl': float(pos['unrealizedProfit']),
                        'leverage': int(pos.get('leverage', 1)),
                        'margin_type': pos.get('marginType', 'cross')
                    })
            
            return positions
        else:
            # Spot - get balances with non-zero amounts
            account = await self.get_account_info()
            positions = []
            
            for balance in account.get('balances', []):
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                # Skip stablecoins and zero balances
                if total > 0 and balance['asset'] not in ['USDT', 'BUSD', 'USDC', 'USD']:
                    positions.append({
                        'symbol': f"{balance['asset']}USDT",
                        'side': 'long',  # Spot only has long positions
                        'quantity': total,
                        'entry_price': 0,  # Not available in spot
                        'mark_price': 0,
                        'unrealized_pnl': 0,
                        'leverage': 1,
                        'margin_type': 'spot'
                    })
            
            return positions
        
        return positions
    
    # ==================== Trading ====================
    
    async def place_market_order(
        self,
        symbol: str,
        side: str,  # 'BUY' or 'SELL'
        quantity: float,
        reduce_only: bool = False
    ) -> dict:
        """Place market order"""
        params = {
            'symbol': symbol.replace('/', ''),
            'side': side.upper(),
            'type': 'MARKET',
            'quantity': quantity
        }
        
        if reduce_only and self.config.is_futures:
            params['reduceOnly'] = 'true'
        
        # Different endpoints for Spot vs Futures
        endpoint = '/fapi/v1/order' if self.config.is_futures else '/api/v3/order'
        result = await self._request('POST', endpoint, params, signed=True)
        
        logger.info(f"Market order placed: {symbol} {side} {quantity}")
        return self._format_order_result(result)
    
    async def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = 'GTC'
    ) -> dict:
        """Place limit order"""
        params = {
            'symbol': symbol.replace('/', ''),
            'side': side.upper(),
            'type': 'LIMIT',
            'quantity': quantity,
            'price': price,
            'timeInForce': time_in_force
        }
        
        endpoint = '/fapi/v1/order' if self.config.is_futures else '/api/v3/order'
        result = await self._request('POST', endpoint, params, signed=True)
        
        logger.info(f"Limit order placed: {symbol} {side} {quantity} @ {price}")
        return self._format_order_result(result)
    
    async def place_stop_loss(
        self,
        symbol: str,
        side: str,  # Opposite of position side
        quantity: float,
        stop_price: float
    ) -> dict:
        """Place stop loss order"""
        if self.config.is_futures:
            params = {
                'symbol': symbol.replace('/', ''),
                'side': side.upper(),
                'type': 'STOP_MARKET',
                'quantity': quantity,
                'stopPrice': stop_price,
                'closePosition': 'false'
            }
            endpoint = '/fapi/v1/order'
        else:
            # Spot uses STOP_LOSS_LIMIT
            params = {
                'symbol': symbol.replace('/', ''),
                'side': side.upper(),
                'type': 'STOP_LOSS_LIMIT',
                'quantity': quantity,
                'stopPrice': stop_price,
                'price': stop_price * 0.99 if side.upper() == 'SELL' else stop_price * 1.01,  # Slightly worse price
                'timeInForce': 'GTC'
            }
            endpoint = '/api/v3/order'
        
        result = await self._request('POST', endpoint, params, signed=True)
        
        logger.info(f"Stop loss placed: {symbol} {side} @ {stop_price}")
        return self._format_order_result(result)
    
    async def place_take_profit(
        self,
        symbol: str,
        side: str,
        quantity: float,
        take_profit_price: float
    ) -> dict:
        """Place take profit order"""
        if self.config.is_futures:
            params = {
                'symbol': symbol.replace('/', ''),
                'side': side.upper(),
                'type': 'TAKE_PROFIT_MARKET',
                'quantity': quantity,
                'stopPrice': take_profit_price,
                'closePosition': 'false'
            }
            endpoint = '/fapi/v1/order'
        else:
            # Spot uses TAKE_PROFIT_LIMIT
            params = {
                'symbol': symbol.replace('/', ''),
                'side': side.upper(),
                'type': 'TAKE_PROFIT_LIMIT',
                'quantity': quantity,
                'stopPrice': take_profit_price,
                'price': take_profit_price,
                'timeInForce': 'GTC'
            }
            endpoint = '/api/v3/order'
        
        result = await self._request('POST', endpoint, params, signed=True)
        
        logger.info(f"Take profit placed: {symbol} {side} @ {take_profit_price}")
        return self._format_order_result(result)
    
    async def cancel_order(self, symbol: str, order_id: int) -> dict:
        """Cancel an order"""
        params = {
            'symbol': symbol.replace('/', ''),
            'orderId': order_id
        }
        
        endpoint = '/fapi/v1/order' if self.config.is_futures else '/api/v3/order'
        result = await self._request('DELETE', endpoint, params, signed=True)
        
        logger.info(f"Order cancelled: {order_id}")
        return result
    
    async def cancel_all_orders(self, symbol: str) -> dict:
        """Cancel all open orders for a symbol"""
        params = {'symbol': symbol.replace('/', '')}
        
        endpoint = '/fapi/v1/allOpenOrders' if self.config.is_futures else '/api/v3/openOrders'
        result = await self._request('DELETE', endpoint, params, signed=True)
        
        logger.info(f"All orders cancelled for {symbol}")
        return result
    
    async def close_position(self, symbol: str) -> Optional[dict]:
        """Close entire position for a symbol (Futures) or sell all (Spot)"""
        positions = await self.get_positions()
        position = next((p for p in positions if p['symbol'] == symbol.replace('/', '')), None)
        
        if not position:
            logger.warning(f"No position found for {symbol}")
            return None
        
        # Opposite side to close
        close_side = 'SELL' if position['side'] == 'long' else 'BUY'
        
        result = await self.place_market_order(
            symbol=symbol,
            side=close_side,
            quantity=position['quantity'],
            reduce_only=True
        )
        
        logger.info(f"Position closed: {symbol}")
        return result
    
    # ==================== Market Data ====================
    
    async def get_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        params = {'symbol': symbol.replace('/', '')}
        result = await self._request('GET', '/fapi/v1/ticker/price', params)
        return float(result['price'])
    
    async def get_ticker(self, symbol: str) -> dict:
        """Get 24h ticker for a symbol"""
        params = {'symbol': symbol.replace('/', '')}
        result = await self._request('GET', '/fapi/v1/ticker/24hr', params)
        
        return {
            'symbol': symbol,
            'price': float(result['lastPrice']),
            'change_24h': float(result['priceChangePercent']),
            'high_24h': float(result['highPrice']),
            'low_24h': float(result['lowPrice']),
            'volume_24h': float(result['volume'])
        }
    
    async def get_orderbook(self, symbol: str, limit: int = 10) -> dict:
        """Get order book for a symbol"""
        params = {
            'symbol': symbol.replace('/', ''),
            'limit': limit
        }
        result = await self._request('GET', '/fapi/v1/depth', params)
        
        return {
            'bids': [[float(p), float(q)] for p, q in result['bids']],
            'asks': [[float(p), float(q)] for p, q in result['asks']]
        }
    
    # ==================== Settings ====================
    
    async def set_leverage(self, symbol: str, leverage: int) -> dict:
        """Set leverage for a symbol"""
        params = {
            'symbol': symbol.replace('/', ''),
            'leverage': leverage
        }
        
        result = await self._request('POST', '/fapi/v1/leverage', params, signed=True)
        
        logger.info(f"Leverage set: {symbol} -> {leverage}x")
        return result
    
    async def set_margin_type(self, symbol: str, margin_type: str = 'ISOLATED') -> dict:
        """Set margin type for a symbol (ISOLATED or CROSSED)"""
        params = {
            'symbol': symbol.replace('/', ''),
            'marginType': margin_type.upper()
        }
        
        try:
            result = await self._request('POST', '/fapi/v1/marginType', params, signed=True)
            logger.info(f"Margin type set: {symbol} -> {margin_type}")
            return result
        except BinanceAPIError as e:
            if e.code == -4046:  # Already set
                return {'msg': 'No need to change margin type'}
            raise
    
    # ==================== Helpers ====================
    
    def _format_order_result(self, result: dict) -> dict:
        """Format order result"""
        return {
            'order_id': result.get('orderId'),
            'client_order_id': result.get('clientOrderId'),
            'symbol': result.get('symbol'),
            'side': result.get('side'),
            'type': result.get('type'),
            'status': result.get('status'),
            'price': float(result.get('price', 0)),
            'avg_price': float(result.get('avgPrice', 0)),
            'quantity': float(result.get('origQty', 0)),
            'executed_qty': float(result.get('executedQty', 0)),
            'timestamp': datetime.fromtimestamp(result.get('updateTime', 0) / 1000, tz=timezone.utc).isoformat()
        }
    
    async def close(self):
        """Close the client"""
        await self.client.aclose()


class BinanceAPIError(Exception):
    """Binance API error"""
    def __init__(self, message: str, code: int = None):
        self.message = message
        self.code = code
        super().__init__(f"[{code}] {message}" if code else message)


# Factory function
def create_binance_broker(
    api_key: str = None,
    api_secret: str = None,
    testnet: bool = True
) -> BinanceBroker:
    """Create Binance broker instance"""
    config = BinanceConfig(
        api_key=api_key or os.environ.get('BINANCE_API_KEY', ''),
        api_secret=api_secret or os.environ.get('BINANCE_SECRET', ''),
        network=BinanceNetwork.TESTNET if testnet else BinanceNetwork.LIVE
    )
    
    return BinanceBroker(config)


# Test function
async def test_binance():
    """Test Binance connection (testnet)"""
    broker = create_binance_broker(testnet=True)
    
    try:
        # Get price
        price = await broker.get_price('BTCUSDT')
        print(f"BTC price: ${price:,.2f}")
        
        # Get ticker
        ticker = await broker.get_ticker('BTCUSDT')
        print(f"24h change: {ticker['change_24h']}%")
        
        # Get balance (requires valid API keys)
        # balance = await broker.get_balance()
        # print(f"Balance: ${balance['available']:,.2f}")
        
    finally:
        await broker.close()


if __name__ == "__main__":
    asyncio.run(test_binance())
