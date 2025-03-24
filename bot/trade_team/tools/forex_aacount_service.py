import asyncio
import logging
from datetime import datetime
from bot.trade_team.tools.account_manager import AccountManager, MarketDataNode, TradingNode
from bot.trade_team.tools.forex_trade import ForexTrader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TeamGraph')

class ForexAccountService:
    def __init__(self, token=None):
        self.token = token
        self.forex_trader = ForexTrader(token=token)
        self.account_manager = None
        self.market_data_node = None
        self.trading_node = None
        self.running = False
        self.task = None
    
    async def initialize(self, account_id=None, symbols=None):
        """Initialize the trading team graph"""
        # Create account manager node
        self.account_manager = AccountManager(self.forex_trader)
        
        # If no account_id provided, try to get one
        if not account_id:
            accounts = await self.forex_trader.get_accounts()
            if accounts:
                account_id = accounts[0].id
                logger.info(f"Using account ID: {account_id}")
            else:
                logger.warning("No accounts found. Some nodes may not initialize properly.")
        
        # Create market data node
        self.market_data_node = MarketDataNode(
            self.forex_trader, 
            account_id=account_id,
            symbols=symbols
        )
        
        # Create trading node
        self.trading_node = TradingNode(
            self.forex_trader,
            account_id=account_id
        )
        
        logger.info("Trading team graph initialized")
    
    async def start(self):
        """Start all nodes in the trading team graph"""
        if self.running:
            return
        
        self.running = True
        
        # Start account manager
        await self.account_manager.start()
        logger.info("Account manager node started")
        
        # Start market data node
        await self.market_data_node.start()
        logger.info("Market data node started")
        
        # Start trading node
        await self.trading_node.start()
        logger.info("Trading node started")
        
        # Create monitoring task
        self.task = asyncio.create_task(self.monitor())
        
        logger.info("Trading team graph started")
    
    async def stop(self):
        """Stop all nodes in the trading team graph"""
        self.running = False
        
        # Cancel monitoring task
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        # Stop all nodes
        if self.trading_node:
            await self.trading_node.stop()
        
        if self.market_data_node:
            await self.market_data_node.stop()
        
        if self.account_manager:
            await self.account_manager.stop()
        
        logger.info("Trading team graph stopped")
    
    async def monitor(self):
        """Monitor the trading team graph"""
        while self.running:
            try:
                # Log status every hour
                if datetime.now().minute == 0 and datetime.now().second == 0:
                    logger.info("Trading team graph is running")
                    
                    # Get account info if trading node is available
                    if self.trading_node and self.trading_node.connection:
                        account_info = await self.trading_node.get_account_info()
                        logger.info(f"Account balance: {account_info['balance']}, Equity: {account_info['equity']}")
                
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in team graph monitor: {str(e)}")
                await asyncio.sleep(60)
    
    async def execute_trade(self, trade_type, symbol, volume, price=None, stop_loss=None, take_profit=None, options=None):
        """Execute a trade using the trading node"""
        if not self.trading_node:
            raise ValueError("Trading node not initialized")
        
        # Get current price if not provided and needed
        if trade_type in ['LIMIT_BUY', 'LIMIT_SELL'] and price is None:
            if not self.market_data_node:
                raise ValueError("Market data node not initialized")
            price_data = await self.market_data_node.get_price(symbol)
            if trade_type == 'LIMIT_BUY':
                price = price_data['ask'] * 0.99  # 1% below current ask
            else:
                price = price_data['bid'] * 1.01  # 1% above current bid
        
        # Execute the trade
        result = await self.trading_node.execute_trade(
            trade_type, symbol, volume, price, stop_loss, take_profit, options
        )
        
        return result
    
    async def get_market_data(self, symbol):
        """Get market data for a symbol"""
        if not self.market_data_node:
            raise ValueError("Market data node not initialized")
        
        return await self.market_data_node.get_price(symbol)
    
    async def get_account_info(self):
        """Get account information"""
        if not self.trading_node:
            raise ValueError("Trading node not initialized")
        
        return await self.trading_node.get_account_info()
    
    async def create_account(self, name, login, password, server, server_dat_file=None):
        """Create a new MetaTrader account with provisioning profile"""
        if not self.account_manager:
            raise ValueError("Account manager not initialized")
        
        # Check if profile exists for this server
        profiles = await self.account_manager.load_profiles()
        profile_id = None
        
        for profile in profiles.values():
            if profile.name == server:
                profile_id = profile.id
                break
        
        # Create profile if it doesn't exist
        if not profile_id:
            profile = await self.account_manager.create_profile(server, server_dat_file=server_dat_file)
            profile_id = profile.id
        
        # Create account
        account = await self.account_manager.create_account(
            name, login, password, server, profile_id
        )
        
        return account
    
    async def deploy_account(self, account_id):
        """Deploy a MetaTrader account"""
        if not self.account_manager:
            raise ValueError("Account manager not initialized")
        
        return await self.account_manager.deploy_account(account_id)
    
    async def undeploy_account(self, account_id):
        """Undeploy a MetaTrader account"""
        if not self.account_manager:
            raise ValueError("Account manager not initialized")
        
        return await self.account_manager.undeploy_account(account_id)



