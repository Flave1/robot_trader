from typing import Dict, Any
from src.infrastructure.oanda_api.oanda_api_service import OandaApiService
from src.users.trader_account_service import TraderAccountService

def trade_execution_tool(input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Trade Execution Tool for ARBIX Monitoring Agent.
    Places, modifies, or cancels trades via broker API (Oanda).

    Args:
        input (dict):
            - trader_account_id (int)
            - symbol (str)
            - units (float)
            - entry (float)
            - stop_loss (float)
            - take_profit (float)
            - action (str): 'buy', 'sell', 'close', 'modify'

    Returns:
        dict: Execution status and details.
    """
    try:
        # Fetch Oanda credentials for the trader account
        api_token, oanda_account_id, oanda_api_url, account_type = TraderAccountService.get_oanda_credentials_by_account_id_sync(input['trader_account_id'])
        oanda_service = OandaApiService(api_token=api_token, account_id=oanda_account_id, oanda_api_url=oanda_api_url, account_type=account_type)
        action = input.get('action', 'buy')
        if action in ['buy', 'sell']:
            result = oanda_service.place_trade(
                symbol=input['symbol'],
                units=input['units'],
                take_profit=input['take_profit'],
                stop_loss=input['stop_loss']
            )
        elif action == 'close':
            result = oanda_service.close_trade(symbol=input['symbol'])
        elif action == 'modify':
            result = oanda_service.modify_trade(
                symbol=input['symbol'],
                units=input['units'],
                take_profit=input['take_profit'],
                stop_loss=input['stop_loss']
            )
        else:
            return {'status': 'error', 'message': f'Unknown action: {action}'}
        return {'status': 'success', 'details': result}
    except Exception as e:
        return {'status': 'error', 'message': str(e)} 