import asyncio
import logging
from datetime import datetime, timedelta
from bot.trade_team.tools.forex_trade import ForexTrader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('WorkerNodes')

class BaseWorkerNode:
    def __init__(self, forex_trader=None, token=None):
        self.forex_trader = forex_trader or ForexTrader(token=token)
        self.running = False
        self.task = None
    
    async def start(self):
        """Start the worker node"""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self.run())
    
    async def stop(self):
        """Stop the worker node"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
    
    async def run(self):
        """Main worker loop - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement run()")


class AccountManager(BaseWorkerNode):
    def __init__(self, forex_trader=None, token=None):
        super().__init__(forex_trader, token)
        self.accounts = {}
        self.profiles = {}
    
    async def load_accounts(self):
        """Load all accounts from MetaAPI"""
        accounts = await self.forex_trader.get_accounts()
        for account in accounts:
            self.accounts[account.id] = account
        return self.accounts
    
    async def load_profiles(self):
        """Load all provisioning profiles from MetaAPI"""
        profiles = await self.forex_trader.get_provisioning_profiles()
        for profile in profiles:
            self.profiles[profile.id] = profile
        return self.profiles
    
    async def create_profile(self, name, version=5, server_dat_file=None):
        """Create a new provisioning profile"""
        profile = await self.forex_trader.create_provisioning_profile(name, version, server_dat_file)
        self.profiles[profile.id] = profile
        return profile
    
    async def create_account(self, name, login, password, server, profile_id, account_type='cloud', magic=1000):
        """Create a new MetaTrader account"""
        account = await self.forex_trader.create_account(name, login, password, server, profile_id, account_type, magic)
        self.accounts[account.id] = account
        return account
    
    async def deploy_account(self, account_id):
        """Deploy a MetaTrader account"""
        account = await self.forex_trader.deploy_account(account_id=account_id)
        return account
    
    async def undeploy_account(self, account_id):
        """Undeploy a MetaTrader account"""
        result = await self.forex_trader.undeploy_account(account_id=account_id)
        return result
    
    async def run(self):
        """Main worker loop - periodically check account status"""
        await self.load_accounts()
        await self.load_profiles()
        
        while self.running:
            try:
                # Refresh account list every 5 minutes
                await self.load_accounts()
                logger.info(f"Account manager monitoring {len(self.accounts)} accounts")
                
                # Sleep for 5 minutes
                await asyncio.sleep(300)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in AccountManagerNode: {str(e)}")
                await asyncio.sleep(60)  # Sleep for a minute before retrying


class MarketDataNode(BaseWorkerNode):
    def __init__(self, forex_trader=None, token=None, account_id=None, symbols=None):
        super().__init__(forex_trader, token)
        self.account_id = account_id
        self.symbols = symbols or ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
        self.connection = None
        self.market_data = {}
    
    async def initialize(self):
        """Initialize the market data node"""
        if not self.account_id:
            accounts = await self.forex_trader.get_accounts()
            if not accounts:
                raise ValueError("No accounts available")
            self.account_id = accounts[0].id
        
        self.connection = await self.forex_trader.get_connection(account_id=self.account_id, connection_type='streaming')
        await self.forex_trader.wait_synchronized(self.connection)
        
        # Subscribe to market data for all symbols
        for symbol in self.symbols:
            await self.connection.subscribe_to_market_data(symbol)
        
        logger.info(f"Market data node initialized for {len(self.symbols)} symbols")
    
    async def get_price(self, symbol):
        """Get current price for a symbol"""
        if symbol not in self.symbols:
            self.symbols.append(symbol)
            await self.connection.subscribe_to_market_data(symbol)
        
        price = self.connection.terminal_state.price(symbol)
        self.market_data[symbol] = {
            'time': datetime.now(),
            'price': price
        }
        return price
    
    async def run(self):
        """Main worker loop - continuously update market data"""
        await self.initialize()
        
        while self.running:
            try:
                for symbol in self.symbols:
                    price = self.connection.terminal_state.price(symbol)
                    self.market_data[symbol] = {
                        'time': datetime.now(),
                        'price': price
                    }
                
                # Log some market data every minute
                if datetime.now().second == 0:
                    logger.info(f"Market data updated for {len(self.symbols)} symbols")
                    for symbol in self.symbols[:3]:  # Log first 3 symbols
                        if symbol in self.market_data:
                            logger.info(f"{symbol}: {self.market_data[symbol]['price']}")
                
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in MarketDataNode: {str(e)}")
                await asyncio.sleep(10)  # Sleep for 10 seconds before retrying
    
    async def stop(self):
        """Stop the market data node"""
        await super().stop()
        if self.connection:
            await self.forex_trader.close_connection(self.connection)


class TradingNode(BaseWorkerNode):
    def __init__(self, forex_trader=None, token=None, account_id=None):
        super().__init__(forex_trader, token)
        self.account_id = account_id
        self.connection = None
        self.positions = []
        self.orders = []
    
    async def initialize(self):
        """Initialize the trading node"""
        if not self.account_id:
            accounts = await self.forex_trader.get_accounts()
            if not accounts:
                raise ValueError("No accounts available")
            self.account_id = accounts[0].id
        
        self.connection = await self.forex_trader.get_connection(account_id=self.account_id, connection_type='rpc')
        await self.forex_trader.wait_synchronized(self.connection)
        
        # Get initial positions and orders
        self.positions = await self.forex_trader.get_positions(self.connection)
        self.orders = await self.forex_trader.get_orders(self.connection)
        
        logger.info(f"Trading node initialized with {len(self.positions)} positions and {len(self.orders)} orders")
    
    async def execute_trade(self, trade_type, symbol, volume, price=None, stop_loss=None, take_profit=None, options=None):
        """Execute a trade"""
        result = await self.forex_trader.execute_trade(
            self.connection, trade_type, symbol, volume, price, stop_loss, take_profit, options
        )
        
        # Update positions and orders
        self.positions = await self.forex_trader.get_positions(self.connection)
        self.orders = await self.forex_trader.get_orders(self.connection)
        
        return result
    
    async def calculate_margin(self, symbol, order_type, volume, price):
        """Calculate margin required for a trade"""
        return await self.forex_trader.calculate_margin(self.connection, symbol, order_type, volume, price)
    
    async def get_account_info(self):
        """Get account information"""
        return await self.forex_trader.get_account_information(self.connection)
    
    async def run(self):
        """Main worker loop - monitor positions and orders"""
        await self.initialize()
        
        while self.running:
            try:
                # Update positions and orders
                self.positions = await self.forex_trader.get_positions(self.connection)
                self.orders = await self.forex_trader.get_orders(self.connection)
                
                # Log account status every 5 minutes
                if datetime.now().minute % 5 == 0 and datetime.now().second == 0:
                    account_info = await self.get_account_info()
                    logger.info(f"Account balance: {account_info['balance']}, Equity: {account_info['equity']}")
                    logger.info(f"Open positions: {len(self.positions)}, Open orders: {len(self.orders)}")
                
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in TradingNode: {str(e)}")
                await asyncio.sleep(10)  # Sleep for 10 seconds before retrying
    
    async def stop(self):
        """Stop the trading node"""
        await super().stop()
        if self.connection:
            await self.forex_trader.close_connection(self.connection)
