"""
Alpaca Broker Integration for Trading AI
Supports Paper Trading and Live Trading for Stocks and Crypto.
"""
import asyncio
import os
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class AlpacaNetwork(str, Enum):
    PAPER = "paper"
    LIVE = "live"


@dataclass
class AlpacaConfig:
    """Alpaca API configuration"""
    api_key: str
    secret_key: str
    network: AlpacaNetwork = AlpacaNetwork.PAPER
    
    @property
    def base_url(self) -> str:
        if self.network == AlpacaNetwork.PAPER:
            return "https://paper-api.alpaca.markets"
        return "https://api.alpaca.markets"
    
    @property
    def data_url(self) -> str:
        return "https://data.alpaca.markets"
    
    @property
    def is_paper(self) -> bool:
        return self.network == AlpacaNetwork.PAPER


class AlpacaAPIError(Exception):
    """Alpaca API error"""
    def __init__(self, message: str, code: int = None):
        self.message = message
        self.code = code
        super().__init__(f"[{code}] {message}" if code else message)


class AlpacaBroker:
    """
    Alpaca broker for stocks and crypto trading.
    
    Features:
    - Paper and Live trading
    - Stocks (US markets)
    - Crypto (24/7)
    - Fractional shares
    - No pattern day trading restrictions on paper
    """
    
    def __init__(self, config: AlpacaConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'APCA-API-KEY-ID': config.api_key,
                'APCA-API-SECRET-KEY': config.secret_key,
                'Content-Type': 'application/json'
            }
        )
        
        logger.info(f"AlpacaBroker initialized ({config.network.value})")
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict = None,
        data: dict = None,
        use_data_api: bool = False
    ) -> dict:
        """Make API request"""
        base = self.config.data_url if use_data_api else self.config.base_url
        url = f"{base}{endpoint}"
        
        try:
            if method == 'GET':
                response = await self.client.get(url, params=params)
            elif method == 'POST':
                response = await self.client.post(url, json=data)
            elif method == 'DELETE':
                response = await self.client.delete(url, params=params)
            elif method == 'PATCH':
                response = await self.client.patch(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code == 204:  # No content
                return {}
            
            result = response.json()
            
            if response.status_code >= 400:
                error_msg = result.get('message', str(result))
                raise AlpacaAPIError(error_msg, response.status_code)
            
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            raise AlpacaAPIError(str(e))
        except Exception as e:
            if isinstance(e, AlpacaAPIError):
                raise
            logger.error(f"Request failed: {e}")
            raise AlpacaAPIError(str(e))
    
    # ==================== Account ====================
    
    async def get_account(self) -> dict:
        """Get account information"""
        return await self._request('GET', '/v2/account')
    
    async def get_balance(self) -> dict:
        """Get account balance"""
        account = await self.get_account()
        
        return {
            'total': float(account.get('equity', 0)),
            'available': float(account.get('cash', 0)),
            'buying_power': float(account.get('buying_power', 0)),
            'portfolio_value': float(account.get('portfolio_value', 0)),
            'currency': account.get('currency', 'USD'),
            'account_status': account.get('status'),
            'pattern_day_trader': account.get('pattern_day_trader', False),
            'trading_blocked': account.get('trading_blocked', False),
            'account_number': account.get('account_number')
        }
    
    async def get_positions(self) -> List[dict]:
        """Get all open positions"""
        positions = await self._request('GET', '/v2/positions')
        
        return [
            {
                'symbol': pos['symbol'],
                'side': 'long' if float(pos['qty']) > 0 else 'short',
                'quantity': abs(float(pos['qty'])),
                'entry_price': float(pos['avg_entry_price']),
                'current_price': float(pos['current_price']),
                'market_value': float(pos['market_value']),
                'unrealized_pnl': float(pos['unrealized_pl']),
                'unrealized_pnl_percent': float(pos['unrealized_plpc']) * 100,
                'asset_class': pos.get('asset_class', 'us_equity'),
                'exchange': pos.get('exchange', '')
            }
            for pos in positions
        ]
    
    async def get_position(self, symbol: str) -> Optional[dict]:
        """Get position for a specific symbol"""
        try:
            pos = await self._request('GET', f'/v2/positions/{symbol}')
            return {
                'symbol': pos['symbol'],
                'side': 'long' if float(pos['qty']) > 0 else 'short',
                'quantity': abs(float(pos['qty'])),
                'entry_price': float(pos['avg_entry_price']),
                'current_price': float(pos['current_price']),
                'market_value': float(pos['market_value']),
                'unrealized_pnl': float(pos['unrealized_pl']),
                'unrealized_pnl_percent': float(pos['unrealized_plpc']) * 100
            }
        except AlpacaAPIError as e:
            if e.code == 404:
                return None
            raise
    
    # ==================== Trading ====================
    
    async def place_market_order(
        self,
        symbol: str,
        side: str,  # 'buy' or 'sell'
        quantity: float = None,
        notional: float = None,  # Dollar amount instead of quantity
        time_in_force: str = 'day'
    ) -> dict:
        """
        Place market order.
        
        Args:
            symbol: Asset symbol (e.g., 'AAPL', 'BTC/USD')
            side: 'buy' or 'sell'
            quantity: Number of shares/units
            notional: Dollar amount (alternative to quantity)
            time_in_force: 'day', 'gtc', 'ioc', 'fok'
        """
        order_data = {
            'symbol': symbol.replace('/', ''),
            'side': side.lower(),
            'type': 'market',
            'time_in_force': time_in_force
        }
        
        if notional:
            order_data['notional'] = str(notional)
        elif quantity:
            order_data['qty'] = str(quantity)
        else:
            raise ValueError("Either quantity or notional must be provided")
        
        result = await self._request('POST', '/v2/orders', data=order_data)
        
        logger.info(f"Market order placed: {symbol} {side} {quantity or notional}")
        return self._format_order_result(result)
    
    async def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        limit_price: float,
        time_in_force: str = 'gtc'
    ) -> dict:
        """Place limit order"""
        order_data = {
            'symbol': symbol.replace('/', ''),
            'side': side.lower(),
            'type': 'limit',
            'qty': str(quantity),
            'limit_price': str(limit_price),
            'time_in_force': time_in_force
        }
        
        result = await self._request('POST', '/v2/orders', data=order_data)
        
        logger.info(f"Limit order placed: {symbol} {side} {quantity} @ {limit_price}")
        return self._format_order_result(result)
    
    async def place_stop_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float,
        time_in_force: str = 'gtc'
    ) -> dict:
        """Place stop order (stop loss)"""
        order_data = {
            'symbol': symbol.replace('/', ''),
            'side': side.lower(),
            'type': 'stop',
            'qty': str(quantity),
            'stop_price': str(stop_price),
            'time_in_force': time_in_force
        }
        
        result = await self._request('POST', '/v2/orders', data=order_data)
        
        logger.info(f"Stop order placed: {symbol} {side} @ {stop_price}")
        return self._format_order_result(result)
    
    async def place_stop_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float,
        limit_price: float,
        time_in_force: str = 'gtc'
    ) -> dict:
        """Place stop-limit order"""
        order_data = {
            'symbol': symbol.replace('/', ''),
            'side': side.lower(),
            'type': 'stop_limit',
            'qty': str(quantity),
            'stop_price': str(stop_price),
            'limit_price': str(limit_price),
            'time_in_force': time_in_force
        }
        
        result = await self._request('POST', '/v2/orders', data=order_data)
        
        logger.info(f"Stop-limit order placed: {symbol} {side} stop@{stop_price} limit@{limit_price}")
        return self._format_order_result(result)
    
    async def place_bracket_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        take_profit_price: float,
        stop_loss_price: float,
        limit_price: float = None  # Optional: makes entry a limit order
    ) -> dict:
        """
        Place bracket order with take profit and stop loss.
        This is perfect for trading signals with TP and SL!
        """
        order_data = {
            'symbol': symbol.replace('/', ''),
            'side': side.lower(),
            'qty': str(quantity),
            'time_in_force': 'gtc',
            'order_class': 'bracket',
            'take_profit': {
                'limit_price': str(take_profit_price)
            },
            'stop_loss': {
                'stop_price': str(stop_loss_price)
            }
        }
        
        if limit_price:
            order_data['type'] = 'limit'
            order_data['limit_price'] = str(limit_price)
        else:
            order_data['type'] = 'market'
        
        result = await self._request('POST', '/v2/orders', data=order_data)
        
        logger.info(f"Bracket order placed: {symbol} {side} TP@{take_profit_price} SL@{stop_loss_price}")
        return self._format_order_result(result)
    
    async def place_oco_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        take_profit_price: float,
        stop_loss_price: float
    ) -> dict:
        """Place OCO (One-Cancels-Other) order for exits"""
        order_data = {
            'symbol': symbol.replace('/', ''),
            'side': side.lower(),
            'qty': str(quantity),
            'time_in_force': 'gtc',
            'order_class': 'oco',
            'take_profit': {
                'limit_price': str(take_profit_price)
            },
            'stop_loss': {
                'stop_price': str(stop_loss_price)
            }
        }
        
        result = await self._request('POST', '/v2/orders', data=order_data)
        
        logger.info(f"OCO order placed: {symbol} {side} TP@{take_profit_price} SL@{stop_loss_price}")
        return self._format_order_result(result)
    
    async def get_orders(self, status: str = 'open') -> List[dict]:
        """Get orders by status ('open', 'closed', 'all')"""
        params = {'status': status}
        orders = await self._request('GET', '/v2/orders', params=params)
        
        return [self._format_order_result(order) for order in orders]
    
    async def get_order(self, order_id: str) -> dict:
        """Get order by ID"""
        result = await self._request('GET', f'/v2/orders/{order_id}')
        return self._format_order_result(result)
    
    async def cancel_order(self, order_id: str) -> dict:
        """Cancel an order"""
        await self._request('DELETE', f'/v2/orders/{order_id}')
        logger.info(f"Order cancelled: {order_id}")
        return {'success': True, 'order_id': order_id}
    
    async def cancel_all_orders(self) -> dict:
        """Cancel all open orders"""
        result = await self._request('DELETE', '/v2/orders')
        logger.info("All orders cancelled")
        return {'success': True, 'cancelled': len(result) if result else 0}
    
    async def close_position(self, symbol: str) -> Optional[dict]:
        """Close position for a symbol"""
        try:
            result = await self._request('DELETE', f'/v2/positions/{symbol}')
            logger.info(f"Position closed: {symbol}")
            return self._format_order_result(result)
        except AlpacaAPIError as e:
            if e.code == 404:
                logger.warning(f"No position found for {symbol}")
                return None
            raise
    
    async def close_all_positions(self) -> dict:
        """Close all positions"""
        result = await self._request('DELETE', '/v2/positions')
        logger.info("All positions closed")
        return {'success': True, 'closed': len(result) if result else 0}
    
    # ==================== Market Data ====================
    
    async def get_quote(self, symbol: str) -> dict:
        """Get latest quote for a symbol"""
        # Check if it's crypto
        if '/' in symbol or symbol.endswith('USD'):
            endpoint = f'/v1beta3/crypto/us/latest/quotes'
            params = {'symbols': symbol.replace('/', '')}
        else:
            endpoint = f'/v2/stocks/{symbol}/quotes/latest'
            params = {}
        
        result = await self._request('GET', endpoint, params=params, use_data_api=True)
        
        # Parse based on response format
        if 'quotes' in result:
            # Crypto response
            quote = list(result['quotes'].values())[0] if result['quotes'] else {}
            return {
                'symbol': symbol,
                'bid': float(quote.get('bp', 0)),
                'ask': float(quote.get('ap', 0)),
                'price': (float(quote.get('bp', 0)) + float(quote.get('ap', 0))) / 2
            }
        else:
            # Stock response
            quote = result.get('quote', result)
            return {
                'symbol': symbol,
                'bid': float(quote.get('bp', 0)),
                'ask': float(quote.get('ap', 0)),
                'price': (float(quote.get('bp', 0)) + float(quote.get('ap', 0))) / 2
            }
    
    async def get_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        quote = await self.get_quote(symbol)
        return quote['price']
    
    async def get_bars(
        self,
        symbol: str,
        timeframe: str = '1Day',
        limit: int = 100
    ) -> List[dict]:
        """Get historical bars"""
        if '/' in symbol or symbol.endswith('USD'):
            endpoint = f'/v1beta3/crypto/us/bars'
            params = {
                'symbols': symbol.replace('/', ''),
                'timeframe': timeframe,
                'limit': limit
            }
        else:
            endpoint = f'/v2/stocks/{symbol}/bars'
            params = {
                'timeframe': timeframe,
                'limit': limit
            }
        
        result = await self._request('GET', endpoint, params=params, use_data_api=True)
        
        bars = result.get('bars', {})
        if isinstance(bars, dict):
            bars = list(bars.values())[0] if bars else []
        
        return [
            {
                'timestamp': bar.get('t'),
                'open': float(bar.get('o', 0)),
                'high': float(bar.get('h', 0)),
                'low': float(bar.get('l', 0)),
                'close': float(bar.get('c', 0)),
                'volume': float(bar.get('v', 0))
            }
            for bar in bars
        ]
    
    async def get_clock(self) -> dict:
        """Get market clock (is market open?)"""
        result = await self._request('GET', '/v2/clock')
        return {
            'is_open': result.get('is_open', False),
            'next_open': result.get('next_open'),
            'next_close': result.get('next_close')
        }
    
    # ==================== Assets ====================
    
    async def get_asset(self, symbol: str) -> dict:
        """Get asset information"""
        result = await self._request('GET', f'/v2/assets/{symbol}')
        return {
            'symbol': result.get('symbol'),
            'name': result.get('name'),
            'exchange': result.get('exchange'),
            'asset_class': result.get('class'),
            'tradable': result.get('tradable', False),
            'fractionable': result.get('fractionable', False),
            'min_order_size': result.get('min_order_size'),
            'price_increment': result.get('price_increment')
        }
    
    async def search_assets(self, query: str, asset_class: str = None) -> List[dict]:
        """Search for assets"""
        params = {'status': 'active'}
        if asset_class:
            params['asset_class'] = asset_class
        
        assets = await self._request('GET', '/v2/assets', params=params)
        
        # Filter by query
        query_lower = query.lower()
        filtered = [
            a for a in assets 
            if query_lower in a.get('symbol', '').lower() 
            or query_lower in a.get('name', '').lower()
        ]
        
        return [
            {
                'symbol': a.get('symbol'),
                'name': a.get('name'),
                'exchange': a.get('exchange'),
                'asset_class': a.get('class'),
                'tradable': a.get('tradable', False)
            }
            for a in filtered[:20]  # Limit results
        ]
    
    # ==================== Helpers ====================
    
    def _format_order_result(self, result: dict) -> dict:
        """Format order result"""
        return {
            'order_id': result.get('id'),
            'client_order_id': result.get('client_order_id'),
            'symbol': result.get('symbol'),
            'side': result.get('side'),
            'type': result.get('type'),
            'status': result.get('status'),
            'quantity': float(result.get('qty', 0) or 0),
            'filled_quantity': float(result.get('filled_qty', 0) or 0),
            'limit_price': float(result.get('limit_price', 0) or 0),
            'stop_price': float(result.get('stop_price', 0) or 0),
            'avg_fill_price': float(result.get('filled_avg_price', 0) or 0),
            'time_in_force': result.get('time_in_force'),
            'order_class': result.get('order_class'),
            'created_at': result.get('created_at'),
            'filled_at': result.get('filled_at'),
            'legs': result.get('legs', [])
        }
    
    async def close(self):
        """Close the client"""
        await self.client.aclose()


# Factory function
def create_alpaca_broker(
    api_key: str = None,
    secret_key: str = None,
    paper: bool = True
) -> AlpacaBroker:
    """Create Alpaca broker instance"""
    config = AlpacaConfig(
        api_key=api_key or os.environ.get('ALPACA_API_KEY', ''),
        secret_key=secret_key or os.environ.get('ALPACA_SECRET_KEY', ''),
        network=AlpacaNetwork.PAPER if paper else AlpacaNetwork.LIVE
    )
    
    return AlpacaBroker(config)


# Test function
async def test_alpaca():
    """Test Alpaca connection"""
    broker = create_alpaca_broker(paper=True)
    
    try:
        # Get account
        print("Testing Alpaca Paper Trading...")
        balance = await broker.get_balance()
        print(f"Account: {balance['account_number']}")
        print(f"Equity: ${balance['total']:,.2f}")
        print(f"Cash: ${balance['available']:,.2f}")
        print(f"Buying Power: ${balance['buying_power']:,.2f}")
        
        # Get market clock
        clock = await broker.get_clock()
        print(f"Market Open: {clock['is_open']}")
        
        # Get positions
        positions = await broker.get_positions()
        print(f"Open Positions: {len(positions)}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await broker.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_alpaca())
