from mcp.server.fastmcp import FastMCP
from src.infrastructure.meta_api.meta_api_service import MetaApiService
from application.services.meta_trading_app_service import MetaTradingAppService
from src.model_types.common import MarketData

mcp = FastMCP("trade")

# @mcp.tool()
async def get_active_positions():
    """
    Retrieve currently active (open) trading positions from the MetaTrader account.

    This function initializes the MetaApi service, connects to the trading account, 
    and fetches all open positions using the TradingAppService. It's designed to be 
    used as an MCP tool that provides visibility into the user's current trading activity.

    Workflow:
    1. Initialize and authenticate with the MetaTrader account via MetaApiService.
    2. Use TradingAppService to retrieve active/open positions.
    3. Print the retrieved positions for inspection or debugging purposes.
    4. Handle and log any exceptions that may occur.
    5. Cleanly close the MetaApi connection and undeploy the account.

    Assumptions:
    - `MetaApiService` provides async methods: `initialize()`, `connection.close()`, and `account.undeploy()`.
    - `TradingAppService` has an async method `get_active_positions()` that returns a list of current open trades.

    This tool is useful for monitoring live trades or debugging strategy performance.
    """
    meta_api_service = MetaApiService()
    await meta_api_service.initialize()
    trading_service = MetaTradingAppService(meta_api_service)

    try:
        # Fetch and print active trading positions
        positions = await trading_service.get_active_positions()
        print(f"Current positions: {positions}")

    except Exception as e:
        print(f"Error occurred: {str(e)}")

    finally:
        # Cleanup resources
        if meta_api_service.connection:
            await meta_api_service.connection.close()
        if meta_api_service.account:
            await meta_api_service.account.undeploy()

# @mcp.tool()
async def monitor_market(market_data: MarketData):
    """
        Monitors live market data for a given trading symbol using MetaApi.

        Args:
            market_data (MarketData): Contains the trading symbol (e.g., "GBPUSD").

        Steps:
        1. Initializes MetaApiService and connects to MetaTrader.
        2. Uses TradingAppService to fetch live market data for the symbol.
        3. Prints the current data or logs any errors.
        4. Cleans up by closing the connection and undeploying the account.

        Note: Requires async support in both MetaApiService and TradingAppService.
    """

    # Initialize services
    meta_api_service = MetaApiService()
    await meta_api_service.initialize()
    trading_service = MetaTradingAppService(meta_api_service)

    try:
        # Monitor market
        market_data = await trading_service.monitor_market(market_data.symbol)
        print(f"Current market data for GBPUSD: {market_data}")

    except Exception as e:
        print(f"Error occurred: {str(e)}")

    finally:
        # Cleanup
        if meta_api_service.connection:
            await meta_api_service.connection.close()
        if meta_api_service.account:
            await meta_api_service.account.undeploy()

# @mcp.tool()
async def place_trade():
    """
    Asynchronously places a trade using the MetaApi and TradingAppService.

    This function performs the following steps:
    1. Initializes the MetaApiService to set up connection to the MetaTrader account.
    2. Creates a TradingAppService instance using the initialized MetaApiService.
    3. Attempts to place a trade with the specified parameters:
        - Symbol: "GBPUSD"
        - Trade type: Buy order ("ORDER_TYPE_BUY")
        - Volume: 0.1 lots
        - Entry price: 1.1
        - Stop Loss: 1.05
        - Take Profit: 1.15
    4. Prints the result of the trade if successful.
    5. If an exception occurs, prints the error message.
    6. Finally, ensures proper cleanup by:
        - Closing the connection to MetaTrader.
        - Undeploying the MetaTrader account instance.

    Note:
        This function assumes that the `MetaApiService` and `TradingAppService` 
        are correctly implemented and support async operations such as `initialize`, 
        `place_trade`, `close`, and `undeploy`.
    """
    # Initialize services
    meta_api_service = MetaApiService()

    await meta_api_service.initialize()
    trading_service = MetaTradingAppService(meta_api_service)

    try:
        # Place a trade
        trade_result = await trading_service.place_trade(
            symbol="GBPUSD",
            trade_type="ORDER_TYPE_BUY",
            volume=0.1,
            price=1.1,
            stop_loss=1.05,
            take_profit=1.15
        )
        print(f"Trade executed: {trade_result}")

    except Exception as e:
        print(f"Error occurred: {str(e)}")

    finally:
        # Cleanup
        if meta_api_service.connection:
            await meta_api_service.connection.close()
        if meta_api_service.account:
            await meta_api_service.account.undeploy()


if __name__ == "__main__":
    # Initialize and run the server
    print("Starting server...")
    # mcp.run(transport='stdio')


