import asyncio
import os
import random
from langchain_core.messages import ToolMessage
from src.bot.custom_types import ToolNodeArgs, WeatherInput
from langgraph.types import StreamWriter, interrupt, Send
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from src.bot.tools.trade_tools import place_trade, get_active_positions


async def weather_node(input: WeatherInput, writer: StreamWriter):
    location = input["location"]
    tool_call_id = input["tool_call_id"]

    # Send custom event to the client. It will update the state of the last checkpoint and all child nodes.
    # Note: if there are multiple child nodes (e.g. parallel nodes), the state will be updated for all of them.
    writer({"weather_forecast": [
           {"location": location, "search_status": f"Checking weather in {location}"}]})

    await asyncio.sleep(4)
    weather = random.choice(["Sunny", "Cloudy", "Rainy", "Snowy"])
    return {"messages": [ToolMessage(content=weather, tool_call_id=tool_call_id)], "weather_forecast": [{"location": location, "search_status": "", "result": weather}]}


async def reminder_node(input: ToolNodeArgs):
    res = interrupt(input['args']['reminder_text'])

    tool_answer = "Reminder created." if res == 'approve' else "Reminder creation cancelled by user."

    return {"messages": [ToolMessage(content=tool_answer, tool_call_id=input["id"])]}


def simple_search(query: str):
     api_key = os.getenv("TAVILY_API_KEY")
     if not api_key:
        api_key = "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"
     
     tavily_search = TavilySearchResults(tavily_api_key=api_key, return_direct=True)
     results = tavily_search.run(query)
     return results

async def tavily_search_node(input: ToolNodeArgs):
    """Search the internet using Tavily API"""
    query = input["args"]["query"]
    tool_call_id = input["id"]
    
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY is not set in the environment variables.")
    
    try:
        tavily_search = TavilySearchResults(api_key=api_key, return_direct=True)
        results = tavily_search.run(query)
        
        # Return in the correct format expected by the graph
        return {
            "messages": [
                ToolMessage(
                    content=str(results),
                    tool_call_id=tool_call_id
                )
            ]
        }
    except Exception as ex:
        return {
            "messages": [
                ToolMessage(
                    content=f"An error occurred: {ex}",
                    tool_call_id=tool_call_id
                )
            ]
        }

async def place_trade_node(input: ToolNodeArgs, writer: StreamWriter):
    args = input["args"]
    tool_call_id = input["id"]

    # Extract parameters
    symbol = args.get("symbol")
    units = args.get("units")
    take_profit = args.get("take_profit")
    stop_loss = args.get("stop_loss")

    # Call the place_trade tool
    result = place_trade(symbol, units, take_profit, stop_loss)

    # Optionally, send an update to the client
    writer({"trade_status": [
        {"symbol": symbol, "status": "Trade placed", "result": result}
    ]})

    return {
        "messages": [
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call_id
            )
        ],
        "trade_status": [
            {"symbol": symbol, "status": "Trade placed", "result": result}
        ]
    }

async def get_active_positions_node(input: ToolNodeArgs, writer: StreamWriter):
    tool_call_id = input["id"]

    # Call the get_active_positions tool
    result = get_active_positions()

    # Optionally, send an update to the client
    writer({"positions_status": [
        {"status": "Positions fetched", "result": result}
    ]})

    return {
        "messages": [
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call_id
            )
        ],
        "positions_status": [
            {"status": "Positions fetched", "result": result}
        ]
    }
    