import asyncio
from typing import Any, Dict
from mcp.server.fastmcp import FastMCP
from bot.tools.common_nodes import simple_search
from src.application.services.oanda_trading_app_service import OandaTradingAppService

mcp = FastMCP("trade")

@mcp.tool()
def search_tavily_tool(query: str):
    """
    Use this for real-time internet search.

    Args:
        query (str): The search query.

    """
    return simple_search(query)

@mcp.tool()
def place_trade(symbol: str, units: float, take_profit: float = None, stop_loss: float = None) -> Dict[str, Any]:
    """
        Place a trade order
        :param symbol: The trading symbol (e.g., "EUR_USD")
        :param units: Positive for buy, negative for sell
        :param take_profit: Optional take profit price
        :param stop_loss: Optional stop loss price
        :return: Order response
    """
    trading_service = OandaTradingAppService()

    # Example 1: Place a trade
    # Buy 100 units of EUR_USD with take profit at 1.15 and stop loss at 1.05
    trade_result = trading_service.place_trade(
        symbol=symbol,
        units=units,
        take_profit=take_profit,
        stop_loss=stop_loss
    )
    print("Trade Result:", trade_result)

    # Example 2: Get active positions
    # positions =  trading_service.get_active_positions()
    # print("Active Positions:", positions)

    # Example 3: Monitor market (this will run continuously)
    # You can modify the symbols list based on what you want to monitor
    # symbols = ["EUR_USD", "GBP_USD", "USD_JPY"]
    # trading_service.monitor_market(symbols)

if __name__ == "__main__":
    # place_trade("EUR_USD", -100, 1.082, 1.097)
    # search_tavily_tool("Price of BTCUSD")
    print("Starting")
    mcp.run(transport='stdio')