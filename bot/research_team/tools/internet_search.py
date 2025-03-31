import os
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from typing import List, Dict

from bot.custom_types import InputQuery



def tavily_search_wrapper(query: str) -> List[Dict[str, str]]:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY is not set in the environment variables.")
    
    try:
        tavily_search = TavilySearchResults(api_key=api_key, return_direct = True)
        results = tavily_search.run(query)
        return results if isinstance(results, list) else []
    except Exception as ex:
        return [{"url": "", "content": f"An error occurred: {ex}"}]


@tool("search-tavily", args_schema=InputQuery, return_direct=True)
def search_tavily(query: str) -> List[Dict[str, str]]:
    """
    Use this for real-time internet search.

    Args:
        query (str): The search query.

    Returns:
        List[Dict[str, str]]: List of dictionaries containing search results with keys 'url' and 'content'.
    """
    return tavily_search_wrapper(query)


tavily_tool = TavilySearchResults(max_results=5)