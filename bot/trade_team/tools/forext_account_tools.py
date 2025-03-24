import os
import asyncio
import logging
from bot.trade_team.tools.forex_aacount_service import ForexAccountService
from langchain_core.tools import tool
# from typing import TypedDict
from typing_extensions import TypedDict
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Account')


class ForexAccountCredentials(TypedDict):
    """The credentials for a forex account"""

    account_id: str
    account_password: str
    account_server: str

@tool()
async def validate_account(account_credentials: ForexAccountCredentials) -> ForexAccountCredentials:
    """
    Validates a MetaTrader account using the provided credentials.

    # Request credentials one by one
    print("Please provide your MetaTrader account credentials.")
    
    account_id = input("Enter your MetaTrader account ID: ")
    if not account_id:
        raise ValueError("Account ID is required")
        
    account_password = input("Enter your MetaTrader password: ")
    if not account_password:
        raise ValueError("Password is required")
        
    account_server = input("Enter your MetaTrader server: ")
    if not account_server:
        raise ValueError("Server is required")
        
    account_credentials = {
        "account_id": account_id,
        "account_password": account_password, 
        "account_server": account_server
    }
    Args:
        login: The MetaTrader login ID
        password: The MetaTrader password
        server: The MetaTrader server
    Returns:
        A account credentials indicating whether the account was validated successfully or raises an error
    """
    # Get token from environment variable
    token = os.getenv('META_API_TOKEN')
    if not token:
        logger.error("META_API_TOKEN environment variable not set")
        return
    # Validate required credentials
    if not account_credentials.get('account_id'):
        raise ValueError("account_id is required but was not provided")
    
    if not account_credentials.get('account_password'):
        raise ValueError("account_password is required but was not provided")
        
    if not account_credentials.get('account_server'):
        raise ValueError("account_server is required but was not provided")
    # Create trading team graph
    service = ForexAccountService(token=token)
    
    try:
        # Initialize with default account and symbols
        await service.initialize(symbols=['EURUSD', 'GBPUSD', 'USDJPY'])
        
        # Start the team
        await service.start()
        logger.info("Trading team started")
        
        # Get market data
        eurusd_price = await service.get_market_data('EURUSD')
        logger.info(f"EURUSD price: {eurusd_price}")
        
        # Get account info
        account_info = await service.get_account_info()
        logger.info(f"Account balance: {account_info['balance']}, Equity: {account_info['equity']}")
        
        # Execute a trade (uncomment to actually execute)
        # result = await team.execute_trade(
        #     'LIMIT_BUY', 'EURUSD', 0.01, 
        #     price=eurusd_price['ask'] * 0.99,  # 1% below current price
        #     stop_loss=eurusd_price['ask'] * 0.98,  # 2% below current price
        #     take_profit=eurusd_price['ask'] * 1.02,  # 2% above current price
        #     options={'comment': 'Example trade', 'clientId': 'example-trade-1'}
        # )
        # logger.info(f"Trade result: {result}")
        
        # Keep running for 5 minutes
        logger.info("Running for 5 minutes...")
        await asyncio.sleep(300)
        return ForexAccountCredentials(
            account_id=account_credentials['account_id'],
            account_password=account_credentials['account_password'],
            account_server=account_credentials['account_server']
        )
    except Exception as e:
        logger.error(f"Error in example: {str(e)}")
    finally:
        # Stop the team
        await service.stop()
        logger.info("Trading team stopped")
