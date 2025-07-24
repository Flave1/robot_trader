from typing import Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
# from src.bot.node.common_nodes import reminder_node, weather_node
from src.core.bot_memory import get_memory
# from mcp_servers.oanda import get_active_positions, place_trade
# from src.bot.node.account_nodes import account_validation_node
# from src.bot.tools.currency_api import search_currency_price_node
from src.bot.tools.common_tools import create_reminder_tool, placetrade_tool, search_tavily_tool, weather_tool, search_currency_tool
from src.bot.custom_types import State
from langgraph.types import Send
from langgraph.checkpoint.memory import MemorySaver


load_dotenv()


async def chatbot(state: State):
    prompt = """
    You are a specialized trading assistant with roles:

    TRADING EXPERTISE:
    - Your primary function is to help users manage and execute trades across forex, crypto, and stock markets
    - You can engage in detailed trading-related conversations, provide market analysis, and assist with trade execution
    - You understand trading terminology, market dynamics, and can explain complex trading concepts
    - You can help with portfolio management, risk assessment, and trading strategy development
    IMPORTANT:
    - Stay focused on trading-related topics and market operations
    - Never engage in non-trading related discussions
    - Maintain professional trading expertise in all responses
    - If a query is not trading-related, politely redirect to trading topics
    """
    thread_id = state.get("thread_id")
    memory = get_memory(thread_id)
    history = memory.load_memory_variables({}).get("chat_history", [])
    messages = [{"role": "system", "content": prompt}] + history + state["messages"]
    llm = ChatOpenAI(
        model="gpt-4o-mini").bind_tools([weather_tool, create_reminder_tool, 
                                         search_tavily_tool, search_currency_tool, 
                                         placetrade_tool])
    # brokerage_validation_tool
    response = await llm.ainvoke(messages)
    # Save the latest user and AI message to memory
    if state["messages"]:
        memory.save_context(
            {"input": state["messages"][-1]["content"]},
            {"output": response["content"]}
        )
    return {"messages": [response]}



# Chatbot node router. Based on tool calls, creates the list of the next parallel nodes.
# def assign_tool(state: State) -> Literal["weather", "reminder", "search_internet", "search_currency_price", "brokerage_validation", "get_active_positions", "place_trade", "__end__"]:
#     messages = state["messages"]
#     last_message = messages[-1]
#     if last_message.tool_calls:
#         send_list = []
#         for tool in last_message.tool_calls:
#             if tool["name"] == 'weather_tool':
#                 send_list.append(Send('weather', {'location': tool['args']['query'], 'tool_call_id': tool['id']}))
#             elif tool["name"] == 'create_reminder_tool':
#                 send_list.append(Send('reminder', tool))
#             elif tool["name"] == 'search_tavily_tool':
#                 send_list.append(Send('search_internet', tool))
#             elif tool["name"] == 'search_currency_tool':
#                 send_list.append(Send('search_currency_price', tool))
#             elif tool["name"] == 'brokerage_validation_tool':
#                 send_list.append(Send('brokerage_validation', tool))
#             elif tool["name"] == 'get_active_positions':
#                 send_list.append(Send('get_active_positions', tool))
#             elif tool["name"] == 'place_trade':
#                 send_list.append(Send('place_trade', tool))
#         return send_list if len(send_list) > 0 else "__end__"
#     return "__end__"



builder = StateGraph(State)

# builder.add_node("chatbot", chatbot)
# builder.add_node("weather", weather_node)
# builder.add_node("reminder", reminder_node)
# builder.add_node("search_internet", tavily_search_node)
# builder.add_node("search_currency_price", search_currency_price_node)
# builder.add_node("brokerage_validation", account_validation_node)
# builder.add_node("get_active_positions", get_active_positions_node)
# builder.add_node("place_trade", place_trade_node)
# builder.add_edge(START, "chatbot")
# builder.add_conditional_edges("chatbot", assign_tool)
# builder.add_edge("weather", "chatbot")
# builder.add_edge("reminder", "chatbot")
# builder.add_edge("search_internet", "chatbot")
# builder.add_edge("search_currency_price", END)
# builder.add_edge("brokerage_validation", "chatbot")
# builder.add_edge("get_active_positions", "chatbot")
# builder.add_edge("place_trade", "chatbot")
# builder.add_edge("chatbot", END)

memory = MemorySaver()
# graph = builder.compile(checkpointer=memory)
