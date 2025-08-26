from langchain_core.tools import tool
import asyncio
from src.infrastructure.oanda_api.oanda_api_service import OandaApiService
from src.database import get_db
from src.users.trader_account_service import TraderAccountService
from src.bot.custom_types import ActiveTradesInput



# @tool("search_currency_tool", args_schema=CurrencyPair, return_direct=True)
# def get_active_trades_tool(currencyPair: CurrencyPair):
#     """
#     Use this for real-time currency check on the internet.

#     Args:
#         query (str): The search query.

#     """
#     return search_currency_price_node(currencyPair)

@tool
def get_active_trades_tool(trader_account_id: int):
    """
    Get all active trades for a specific trader account.
    
    Args:
        trader_account_id (int): The trader account ID to get active trades for.
    
    Returns:
        List of active trades with details like symbol, trade_type, units, entry_price, etc.
    """
  
    print("trader_account_id", trader_account_id)
    async def fetch_active_trades():
        async for db in get_db():
            api_token, oanda_account_id, oanda_api_url, account_type = await TraderAccountService.get_oanda_credentials_by_account_id(db, trader_account_id)
            if not api_token or not oanda_account_id:
                return []
            oanda_service = OandaApiService(api_token=api_token, trader_account_id=oanda_account_id, oanda_api_url=oanda_api_url, account_type=account_type)
            oanda_positions = oanda_service.get_active_positions()
            break
        return oanda_positions
    
    try:
        # Run the async function in a synchronous context
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, create a new event loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, fetch_active_trades())
                return future.result()
        else:
            return asyncio.run(fetch_active_trades())
    except Exception as e:
        return f"Error fetching active trades: {str(e)}" 