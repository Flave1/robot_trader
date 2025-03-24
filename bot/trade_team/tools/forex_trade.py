import os
import asyncio
from metaapi_cloud_sdk import MetaApi
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ForexTrader')

class ForexTrader:
    def __init__(self, token=None):
        self.token = token or os.getenv('META_API_TOKEN')
        if not self.token:
            raise ValueError("MetaAPI token is required. Set META_API_TOKEN environment variable or pass token to constructor.")
        self.api = MetaApi(self.token)
        self.accounts = {}
        self.connections = {}
    
    async def get_accounts(self):
        """Retrieve all MetaTrader accounts"""
        try:
            accounts = await self.api.metatrader_account_api.get_accounts_with_infinite_scroll_pagination()
            return accounts
        except Exception as err:
            logger.error(f"Failed to get accounts: {self.api.format_error(err)}")
            raise
    
    async def get_provisioning_profiles(self):
        """Get all provisioning profiles"""
        try:
            profiles = await self.api.provisioning_profile_api.get_provisioning_profiles_with_infinite_scroll_pagination()
            return profiles
        except Exception as err:
            logger.error(f"Failed to get provisioning profiles: {self.api.format_error(err)}")
            raise
    
    async def create_provisioning_profile(self, name, version=5, server_dat_file=None):
        """Create a new provisioning profile"""
        try:
            profile = await self.api.provisioning_profile_api.create_provisioning_profile(
                {'name': name, 'version': version, 'brokerTimezone': 'EET', 'brokerDSTSwitchTimezone': 'EET'}
            )
            
            if server_dat_file and os.path.exists(server_dat_file):
                await profile.upload_file('servers.dat', server_dat_file)
                
            return profile
        except Exception as err:
            logger.error(f"Failed to create provisioning profile: {self.api.format_error(err)}")
            raise
    
    async def create_account(self, name, login, password, server, profile_id, account_type='cloud', magic=1000):
        """Create a new MetaTrader account"""
        try:
            account = await self.api.metatrader_account_api.create_account(
                {
                    'name': name,
                    'type': account_type,
                    'login': login,
                    'password': password,
                    'server': server,
                    'provisioningProfileId': profile_id,
                    'magic': magic,
                }
            )
            self.accounts[login] = account
            return account
        except Exception as err:
            logger.error(f"Failed to create account: {self.api.format_error(err)}")
            raise
    
    async def deploy_account(self, account_id=None, login=None):
        """Deploy a MetaTrader account"""
        try:
            account = None
            if account_id:
                account = await self.api.metatrader_account_api.get_account(account_id)
            elif login and login in self.accounts:
                account = self.accounts[login]
            else:
                raise ValueError("Either account_id or a valid login must be provided")
            
            await account.deploy()
            await account.wait_connected()
            return account
        except Exception as err:
            logger.error(f"Failed to deploy account: {self.api.format_error(err)}")
            raise
    
    async def undeploy_account(self, account_id=None, login=None):
        """Undeploy a MetaTrader account"""
        try:
            account = None
            if account_id:
                account = await self.api.metatrader_account_api.get_account(account_id)
            elif login and login in self.accounts:
                account = self.accounts[login]
            else:
                raise ValueError("Either account_id or a valid login must be provided")
            
            await account.undeploy()
            return True
        except Exception as err:
            logger.error(f"Failed to undeploy account: {self.api.format_error(err)}")
            raise
    
    async def get_connection(self, account_id=None, login=None, connection_type='rpc'):
        """Get a connection to a MetaTrader account"""
        try:
            account = None
            if account_id:
                account = await self.api.metatrader_account_api.get_account(account_id)
            elif login and login in self.accounts:
                account = self.accounts[login]
            else:
                raise ValueError("Either account_id or a valid login must be provided")
            
            connection_key = f"{account.id}_{connection_type}"
            if connection_key not in self.connections:
                if connection_type == 'rpc':
                    connection = account.get_rpc_connection()
                else:
                    connection = account.get_streaming_connection()
                
                await connection.connect()
                self.connections[connection_key] = connection
            
            return self.connections[connection_key]
        except Exception as err:
            logger.error(f"Failed to get connection: {self.api.format_error(err)}")
            raise
    
    async def wait_synchronized(self, connection, timeout=600):
        """Wait for the connection to synchronize with the terminal state"""
        try:
            if hasattr(connection, 'wait_synchronized'):
                await connection.wait_synchronized({'timeoutInSeconds': timeout})
            else:
                await connection.wait_synchronized()
            return True
        except Exception as err:
            logger.error(f"Failed to synchronize: {self.api.format_error(err)}")
            raise
    
    async def get_account_information(self, connection):
        """Get account information"""
        try:
            return await connection.get_account_information()
        except Exception as err:
            logger.error(f"Failed to get account information: {self.api.format_error(err)}")
            raise
    
    async def get_positions(self, connection):
        """Get open positions"""
        try:
            return await connection.get_positions()
        except Exception as err:
            logger.error(f"Failed to get positions: {self.api.format_error(err)}")
            raise
    
    async def get_orders(self, connection):
        """Get open orders"""
        try:
            return await connection.get_orders()
        except Exception as err:
            logger.error(f"Failed to get orders: {self.api.format_error(err)}")
            raise
    
    async def get_symbol_price(self, connection, symbol):
        """Get current price for a symbol"""
        try:
            if hasattr(connection, 'get_symbol_price'):
                return await connection.get_symbol_price(symbol)
            else:
                # For streaming connection
                await connection.subscribe_to_market_data(symbol)
                return connection.terminal_state.price(symbol)
        except Exception as err:
            logger.error(f"Failed to get symbol price: {self.api.format_error(err)}")
            raise
    
    async def execute_trade(self, connection, trade_type, symbol, volume, price=None, stop_loss=None, take_profit=None, options=None):
        """Execute a trade"""
        try:
            options = options or {}
            
            if trade_type == 'LIMIT_BUY':
                if not price:
                    raise ValueError("Price is required for limit orders")
                result = await connection.create_limit_buy_order(
                    symbol, volume, price, stop_loss, take_profit, options
                )
            elif trade_type == 'LIMIT_SELL':
                if not price:
                    raise ValueError("Price is required for limit orders")
                result = await connection.create_limit_sell_order(
                    symbol, volume, price, stop_loss, take_profit, options
                )
            elif trade_type == 'MARKET_BUY':
                result = await connection.create_market_buy_order(
                    symbol, volume, stop_loss, take_profit, options
                )
            elif trade_type == 'MARKET_SELL':
                result = await connection.create_market_sell_order(
                    symbol, volume, stop_loss, take_profit, options
                )
            else:
                raise ValueError(f"Unsupported trade type: {trade_type}")
            
            return result
        except Exception as err:
            logger.error(f"Failed to execute trade: {self.api.format_error(err)}")
            raise
    
    async def calculate_margin(self, connection, symbol, order_type, volume, price):
        """Calculate margin required for a trade"""
        try:
            return await connection.calculate_margin({
                'symbol': symbol,
                'type': order_type,
                'volume': volume,
                'openPrice': price
            })
        except Exception as err:
            logger.error(f"Failed to calculate margin: {self.api.format_error(err)}")
            raise
    
    async def close_connection(self, connection):
        """Close a connection"""
        try:
            await connection.close()
            # Remove from connections dict
            for key, conn in list(self.connections.items()):
                if conn == connection:
                    del self.connections[key]
            return True
        except Exception as err:
            logger.error(f"Failed to close connection: {self.api.format_error(err)}")
            raise 