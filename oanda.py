import asyncio
from typing import Any, Dict
from mcp.server.fastmcp import FastMCP
from src.bot.tools.common_nodes import simple_search
from src.bot.tools.trade_tools import place_trade, get_active_positions
from src.application.services.oanda_trading_app_service import OandaTradingAppService

mcp = FastMCP("trade2")

@mcp.tool()
def search_tavily_tool(query: str):
    """
    Use this for real-time internet search.

    Args:
        query (str): The search query.

    """
    return simple_search(query)

@mcp.tool()
def place_trade_tool(symbol: str, units: float, take_profit: float = None, stop_loss: float = None) -> Dict[str, Any]:
    """
        Place a trade order
        :param symbol: The trading symbol (e.g., "EUR_USD")
        :param units: Positive for buy, negative for sell
        :param take_profit: Optional take profit price
        :param stop_loss: Optional stop loss price
        :return: Order response
    """
    result = place_trade(symbol, units, take_profit, stop_loss)
    print("Trade Result:", result)
    return result

@mcp.tool()
def get_active_positions_tool() -> Any:
    """
    Get active trading positions.
    :return: List of active positions
    """
    positions = get_active_positions()
    print("Active Positions:", positions)
    return positions

@mcp.tool()
def monitor_market(symbols: list) -> None:
    """
    Monitor the market for a list of trading symbols.
    :param symbols: List of trading symbols (e.g., ["EUR_USD", "GBP_USD"])
    """
    trading_service = OandaTradingAppService()
    trading_service.monitor_market(symbols)

if __name__ == "__main__":
    # place_trade_tool("EUR_USD", -100, 1.082, 1.097)
    # search_tavily_tool("Price of BTCUSD")
    print("Starting")
    mcp.run(transport='stdio')