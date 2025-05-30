from langchain_core.tools import tool

from src.bot.tools.currency_api import search_currency_price_node
from src.bot.custom_types import CurrencyPair, InputQuery
from src.bot.tools.common_nodes import tavily_search_node



@tool
async def weather_tool(query: str) -> str:
    """Call to get current weather"""
    return "Sunny"


@tool
async def create_reminder_tool(reminder_text: str) -> str:
    """Call to create a reminder"""
    return "Reminder created"

@tool
async def placetrade_tool(placetrade_text: str) -> str:
    """Call to place a trade"""
    return "Trade Placed"


@tool("search_tavily_tool", args_schema=InputQuery, return_direct=True)
def search_tavily_tool(query: str):
    """
    Use this for real-time internet search.

    Args:
        query (str): The search query.

    """
    return tavily_search_node(query)

@tool("search_currency_tool", args_schema=CurrencyPair, return_direct=True)
def search_currency_tool(currencyPair: CurrencyPair):
    """
    Use this for real-time currency check on the internet.

    Args:
        query (str): The search query.

    """
    return search_currency_price_node(currencyPair)