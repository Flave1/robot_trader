from typing import Dict, Any
from src.infrastructure.oanda_api.oanda_api_service import OandaApiService
from src.users.trader_account_service import TraderAccountService, TraderAccountsTradesService
from src.users.models import TraderAccountsTradesCreate
from langchain_core.tools import tool
import asyncio

# ============================================================================
# ORDER MANAGEMENT TOOLS
# ============================================================================

@tool
def list_orders_tool(input: dict) -> Dict[str, Any]:
    """
    List orders for a trader account.
    
    Args:
        input (dict):
            - trader_account_id (int): The trader's account ID
            - state (str, optional): Order state filter (PENDING, FILLED, CANCELLED, etc.)
            - count (int, optional): Number of orders to retrieve (default: 50)
            - instrument (str, optional): Filter by instrument/symbol
    
    Returns:
        dict: List of orders and status
    """
    try:
        trader_account_id = input['trader_account_id']
        state = input.get('state', 'PENDING')
        count = input.get('count', 50)
        instrument = input.get('instrument')
        
        # Get Oanda credentials
        async def _get_credentials():
            from src.database import get_db
            async for db in get_db():
                return await TraderAccountService.get_oanda_credentials_by_account_id(db, trader_account_id)
        
        api_token, oanda_account_id, oanda_api_url, account_type = asyncio.run(_get_credentials())
        
        if not api_token or not oanda_account_id:
            return {'status': 'error', 'message': 'Oanda credentials not found for this account.'}
        
        oanda_service = OandaApiService(api_token=api_token, trader_account_id=oanda_account_id, oanda_api_url=oanda_api_url, account_type=account_type)
        orders = oanda_service.list_orders(state=state, count=count, instrument=instrument)
        
        return {
            'status': 'success',
            'orders': orders,
            'count': len(orders),
            'state': state
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@tool
def get_order_tool(input: dict) -> Dict[str, Any]:
    """
    Get specific order details.
    
    Args:
        input (dict):
            - trader_account_id (int): The trader's account ID
            - order_id (str): The order ID to retrieve
    
    Returns:
        dict: Order details and status
    """
    try:
        trader_account_id = input['trader_account_id']
        order_id = input['order_id']
        
        # Get Oanda credentials
        async def _get_credentials():
            from src.database import get_db
            async for db in get_db():
                return await TraderAccountService.get_oanda_credentials_by_account_id(db, trader_account_id)
        
        api_token, oanda_account_id, oanda_api_url, account_type = asyncio.run(_get_credentials())
        
        if not api_token or not oanda_account_id:
            return {'status': 'error', 'message': 'Oanda credentials not found for this account.'}
        
        oanda_service = OandaApiService(api_token=api_token, trader_account_id=oanda_account_id, oanda_api_url=oanda_api_url, account_type=account_type)
        order = oanda_service.get_order(order_id)
        
        return {
            'status': 'success',
            'order': order
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@tool
def cancel_order_tool(input: dict) -> Dict[str, Any]:
    """
    Cancel a specific order.
    
    Args:
        input (dict):
            - trader_account_id (int): The trader's account ID
            - order_id (str): The order ID to cancel
    
    Returns:
        dict: Cancellation status and details
    """
    try:
        trader_account_id = input['trader_account_id']
        order_id = input['order_id']
        
        # Get Oanda credentials
        async def _get_credentials():
            from src.database import get_db
            async for db in get_db():
                return await TraderAccountService.get_oanda_credentials_by_account_id(db, trader_account_id)
        
        api_token, oanda_account_id, oanda_api_url, account_type = asyncio.run(_get_credentials())
        
        if not api_token or not oanda_account_id:
            return {'status': 'error', 'message': 'Oanda credentials not found for this account.'}
        
        oanda_service = OandaApiService(api_token=api_token, trader_account_id=oanda_account_id, oanda_api_url=oanda_api_url, account_type=account_type)
        result = oanda_service.cancel_order(order_id)
        
        return {
            'status': 'success',
            'cancellation_result': result,
            'order_id': order_id
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@tool
def replace_order_tool(input: dict) -> Dict[str, Any]:
    """
    Replace an existing order.
    
    Args:
        input (dict):
            - trader_account_id (int): The trader's account ID
            - order_id (str): The order ID to replace
            - new_order_data (dict): New order data
    
    Returns:
        dict: Replacement status and details
    """
    try:
        trader_account_id = input['trader_account_id']
        order_id = input['order_id']
        new_order_data = input['new_order_data']
        
        # Get Oanda credentials
        async def _get_credentials():
            from src.database import get_db
            async for db in get_db():
                return await TraderAccountService.get_oanda_credentials_by_account_id(db, trader_account_id)
        
        api_token, oanda_account_id, oanda_api_url, account_type = asyncio.run(_get_credentials())
        
        if not api_token or not oanda_account_id:
            return {'status': 'error', 'message': 'Oanda credentials not found for this account.'}
        
        oanda_service = OandaApiService(api_token=api_token, trader_account_id=oanda_account_id, oanda_api_url=oanda_api_url, account_type=account_type)
        result = oanda_service.replace_order(order_id, new_order_data)
        
        return {
            'status': 'success',
            'replacement_result': result,
            'order_id': order_id
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@tool
def create_order_tool(input: dict) -> Dict[str, Any]:
    """
    Create a new order (market, limit, or stop).
    
    Args:
        input (dict):
            - trader_account_id (int): The trader's account ID
            - symbol (str): The trading symbol (e.g., 'EUR_USD')
            - units (float): Positive for buy, negative for sell
            - order_type (str): 'MARKET', 'LIMIT', or 'STOP'
            - price (float, optional): Price for limit/stop orders
            - take_profit (float, optional): Take profit price
            - stop_loss (float, optional): Stop loss price
    
    Returns:
        dict: Order creation status and details
    """
    try:
        trader_account_id = input['trader_account_id']
        symbol = input['symbol']
        units = input['units']
        order_type = input.get('order_type', 'MARKET')
        price = input.get('price')
        take_profit = input.get('take_profit')
        stop_loss = input.get('stop_loss')
        
        # Get Oanda credentials
        async def _get_credentials():
            from src.database import get_db
            async for db in get_db():
                return await TraderAccountService.get_oanda_credentials_by_account_id(db, trader_account_id)
        
        api_token, oanda_account_id, oanda_api_url, account_type = asyncio.run(_get_credentials())
        
        if not api_token or not oanda_account_id:
            return {'status': 'error', 'message': 'Oanda credentials not found for this account.'}
        
        oanda_service = OandaApiService(api_token=api_token, trader_account_id=oanda_account_id, oanda_api_url=oanda_api_url, account_type=account_type)
        
        if order_type == 'MARKET':
            result = oanda_service.create_market_order(symbol, units, take_profit, stop_loss)
        elif order_type == 'LIMIT':
            if not price:
                return {'status': 'error', 'message': 'Price is required for limit orders.'}
            result = oanda_service.create_limit_order(symbol, units, price, take_profit, stop_loss)
        elif order_type == 'STOP':
            if not price:
                return {'status': 'error', 'message': 'Price is required for stop orders.'}
            result = oanda_service.create_stop_order(symbol, units, price, take_profit, stop_loss)
        else:
            return {'status': 'error', 'message': f'Unsupported order type: {order_type}'}
        
        # Log the trade if successful
        logged_trade_id = None
        if "orderFillTransaction" in result or "orderCreateTransaction" in result:
            try:
                async def _log_trade():
                    from src.database import get_db
                    async for db in get_db():
                        trade_data = TraderAccountsTradesCreate(
                            trader_account_id=trader_account_id,
                            symbol=symbol,
                            trade_type="buy" if units > 0 else "sell",
                            units=abs(units),
                            entry_price=price or 0,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            oanda_order_id=str(result.get('orderCreateTransaction', {}).get('id', '')),
                            oanda_position_id=None
                        )
                        return await TraderAccountsTradesService.create_trade(db, trade_data)
                
                logged_trade = asyncio.run(_log_trade())
                logged_trade_id = logged_trade.id if logged_trade else None
            except Exception as db_error:
                print(f"Failed to log trade: {db_error}")
        
        return {
            'status': 'success',
            'order_result': result,
            'logged_trade_id': logged_trade_id,
            'order_type': order_type,
            'symbol': symbol,
            'units': units
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@tool
def trade_execution_tool(input: dict) -> Dict[str, Any]:
    """
    Execute a market trade (legacy function for backward compatibility).
    
    Args:
        input (dict):
            - trader_account_id (int): The trader's account ID
            - symbol (str): The trading symbol
            - units (float): Positive for buy, negative for sell
            - take_profit (float, optional): Take profit price
            - stop_loss (float, optional): Stop loss price
    
    Returns:
        dict: Trade execution status and details
    """
    # Redirect to create_order_tool with MARKET order type
    input['order_type'] = 'MARKET'
    return create_order_tool(input)

# ============================================================================
# POSITION/TRADE MANAGEMENT TOOLS
# ============================================================================

@tool
def list_trades_tool(input: dict) -> Dict[str, Any]:
    """
    List trades for a trader account.
    
    Args:
        input (dict):
            - trader_account_id (int): The trader's account ID
            - state (str, optional): Trade state filter (OPEN, CLOSED, etc.)
            - count (int, optional): Number of trades to retrieve (default: 50)
            - instrument (str, optional): Filter by instrument/symbol
    
    Returns:
        dict: List of trades and status
    """
    try:
        trader_account_id = input['trader_account_id']
        state = input.get('state', 'OPEN')
        count = input.get('count', 50)
        instrument = input.get('instrument')
        
        # Get Oanda credentials
        async def _get_credentials():
            from src.database import get_db
            async for db in get_db():
                return await TraderAccountService.get_oanda_credentials_by_account_id(db, trader_account_id)
        
        api_token, oanda_account_id, oanda_api_url, account_type = asyncio.run(_get_credentials())
        
        if not api_token or not oanda_account_id:
            return {'status': 'error', 'message': 'Oanda credentials not found for this account.'}
        
        oanda_service = OandaApiService(api_token=api_token, trader_account_id=oanda_account_id, oanda_api_url=oanda_api_url, account_type=account_type)
        trades = oanda_service.list_trades(state=state, count=count, instrument=instrument)
        
        return {
            'status': 'success',
            'trades': trades,
            'count': len(trades),
            'state': state
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@tool
def get_trade_tool(input: dict) -> Dict[str, Any]:
    """
    Get specific trade details.
    
    Args:
        input (dict):
            - trader_account_id (int): The trader's account ID
            - trade_id (str): The trade ID to retrieve
    
    Returns:
        dict: Trade details and status
    """
    try:
        trader_account_id = input['trader_account_id']
        trade_id = input['trade_id']
        
        # Get Oanda credentials
        async def _get_credentials():
            from src.database import get_db
            async for db in get_db():
                return await TraderAccountService.get_oanda_credentials_by_account_id(db, trader_account_id)
        
        api_token, oanda_account_id, oanda_api_url, account_type = asyncio.run(_get_credentials())
        
        if not api_token or not oanda_account_id:
            return {'status': 'error', 'message': 'Oanda credentials not found for this account.'}
        
        oanda_service = OandaApiService(api_token=api_token, trader_account_id=oanda_account_id, oanda_api_url=oanda_api_url, account_type=account_type)
        trade = oanda_service.get_trade(trade_id)
        
        return {
            'status': 'success',
            'trade': trade
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@tool
def close_trade_tool(input: dict) -> Dict[str, Any]:
    """
    Close a trade (partial or full).
    
    Args:
        input (dict):
            - trader_account_id (int): The trader's account ID
            - trade_id (str): The trade ID to close
            - units (str, optional): Number of units to close ("ALL" for full close, or specific number)
    
    Returns:
        dict: Close status and details
    """
    try:
        trader_account_id = input['trader_account_id']
        trade_id = input['trade_id']
        units = input.get('units', 'ALL')
        
        # Get Oanda credentials
        async def _get_credentials():
            from src.database import get_db
            async for db in get_db():
                return await TraderAccountService.get_oanda_credentials_by_account_id(db, trader_account_id)
        
        api_token, oanda_account_id, oanda_api_url, account_type = asyncio.run(_get_credentials())
        
        if not api_token or not oanda_account_id:
            return {'status': 'error', 'message': 'Oanda credentials not found for this account.'}
        
        oanda_service = OandaApiService(api_token=api_token, trader_account_id=oanda_account_id, oanda_api_url=oanda_api_url, account_type=account_type)
        result = oanda_service.close_trade(trade_id, units)
        
        return {
            'status': 'success',
            'close_result': result,
            'trade_id': trade_id,
            'units_closed': units
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@tool
def update_trade_orders_tool(input: dict) -> Dict[str, Any]:
    """
    Set or update stop loss and take profit for a trade.
    
    Args:
        input (dict):
            - trader_account_id (int): The trader's account ID
            - trade_id (str): The trade ID to update
            - stop_loss (float, optional): New stop loss price (None to remove)
            - take_profit (float, optional): New take profit price (None to remove)
    
    Returns:
        dict: Update status and details
    """
    try:
        trader_account_id = input['trader_account_id']
        trade_id = input['trade_id']
        stop_loss = input.get('stop_loss')
        take_profit = input.get('take_profit')
        
        # Get Oanda credentials
        async def _get_credentials():
            from src.database import get_db
            async for db in get_db():
                return await TraderAccountService.get_oanda_credentials_by_account_id(db, trader_account_id)
        
        api_token, oanda_account_id, oanda_api_url, account_type = asyncio.run(_get_credentials())
        
        if not api_token or not oanda_account_id:
            return {'status': 'error', 'message': 'Oanda credentials not found for this account.'}
        
        oanda_service = OandaApiService(api_token=api_token, trader_account_id=oanda_account_id, oanda_api_url=oanda_api_url, account_type=account_type)
        result = oanda_service.update_trade_orders(trade_id, stop_loss, take_profit)
        
        return {
            'status': 'success',
            'update_result': result,
            'trade_id': trade_id,
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@tool
def get_active_positions_tool(input: dict) -> Dict[str, Any]:
    """
    Get all active positions for a trader account.
    
    Args:
        input (dict):
            - trader_account_id (int): The trader's account ID
    
    Returns:
        dict: Active positions and status
    """
    try:
        print("get_active_positions_tool_input", input)
        trader_account_id = input['trader_account_id']
        
        # Get Oanda credentials
        async def _get_credentials():
            from src.database import get_db
            async for db in get_db():
                return await TraderAccountService.get_oanda_credentials_by_account_id(db, trader_account_id)
        
        api_token, oanda_account_id, oanda_api_url, account_type = asyncio.run(_get_credentials())
        
        if not api_token or not oanda_account_id:
            return {'status': 'error', 'message': 'Oanda credentials not found for this account.'}
        
        oanda_service = OandaApiService(api_token=api_token, trader_account_id=oanda_account_id, oanda_api_url=oanda_api_url, account_type=account_type)
        positions = oanda_service.get_active_positions()
        
        return {
            'status': 'success',
            'positions': positions,
            'count': len(positions)
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)} 