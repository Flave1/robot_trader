from typing import Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from oanda import get_active_positions, place_trade
from src.bot.tools.account_nodes import account_validation_node
from src.bot.tools.account_tools import brokerage_validation_tool
from src.bot.tools.currency_api import search_currency_price_node
from src.bot.tools.common_nodes import get_active_positions_node, place_trade_node, reminder_node, tavily_search_node, weather_node
from src.bot.tools.common_tools import create_reminder_tool, placetrade_tool, search_tavily_tool, weather_tool, search_currency_tool
from src.bot.custom_types import State
from langgraph.types import Send
from langchain.memory import VectorStoreRetrieverMemory
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import os
from langgraph.checkpoint.memory import MemorySaver


load_dotenv()

# VectorStore-backed Chroma memory integration
def get_memory(thread_id: str):
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    collection_name = f"conversation_{thread_id}"
    embeddings = HuggingFaceEmbeddings()
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_dir
    )
    memory = VectorStoreRetrieverMemory(
        retriever=vectorstore.as_retriever(),
        memory_key="chat_history"
    )
    return memory

# "",
tools = ["weather", "reminder", "search_internet", "search_currency_price", "brokerage_validation", "get_active_positions", "place_trade", "__end__"]
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
                                         placetrade_tool, place_trade, get_active_positions])
    # brokerage_validation_tool
    response = await llm.ainvoke(messages)
    # Save the latest user and AI message to memory
    if state["messages"]:
        memory.save_context(
            {"input": state["messages"][-1]["content"]},
            {"output": response["content"]}
        )
    return {"messages": [response]}


def tool_router(state: State) -> Literal[*tools]:
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        if last_message.tool_calls[0]["name"] == "weather_tool":
            return "weather"
        elif last_message.tool_calls[0]["name"] == "create_reminder_tool":
            return "reminder"
        elif last_message.tool_calls[0]["name"] == "search_tavily_tool":
            return "search_internet"
        elif last_message.tool_calls[0]["name"] == "search_currency_tool":
           return "search_currency_price"
        elif last_message.tool_calls[0]["name"] == "brokerage_validation_tool":
           return "brokerage_validation"
        elif last_message.tool_calls[0]["name"] == "get_active_positions":
           return "get_active_positions"
        elif last_message.tool_calls[0]["name"] == "place_trade":
           return "place_trade"
    return "__end__"


# Chatbot node router. Based on tool calls, creates the list of the next parallel nodes.
def assign_tool(state: State) -> Literal[*tools]:
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        send_list = []
        for tool in last_message.tool_calls:
            if tool["name"] == 'weather_tool':
                send_list.append(Send('weather', {'location': tool['args']['query'], 'tool_call_id': tool['id']}))
            elif tool["name"] == 'create_reminder_tool':
                send_list.append(Send('reminder', tool))
            elif tool["name"] == 'search_tavily_tool':
                send_list.append(Send('search_internet', tool))
            elif tool["name"] == 'search_currency_tool':
                send_list.append(Send('search_currency_price', tool))
            elif tool["name"] == 'brokerage_validation_tool':
                send_list.append(Send('brokerage_validation', tool))
            elif tool["name"] == 'get_active_positions':
                send_list.append(Send('get_active_positions', tool))
            elif tool["name"] == 'place_trade':
                send_list.append(Send('place_trade', tool))
        return send_list if len(send_list) > 0 else "__end__"
    return "__end__"


def hitl_router(state: State) -> Literal["hitl_node", "__end__"]:
    if state["search_results"] == "y":
        return "hitl_node"
    return "__end__"


builder = StateGraph(State)

builder.add_node("chatbot", chatbot)
builder.add_node("weather", weather_node)
builder.add_node("reminder", reminder_node)
builder.add_node("search_internet", tavily_search_node)
builder.add_node("search_currency_price", search_currency_price_node)
builder.add_node("brokerage_validation", account_validation_node)
builder.add_node("get_active_positions", get_active_positions_node)
builder.add_node("place_trade", place_trade_node)
builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", assign_tool)
builder.add_edge("weather", "chatbot")
builder.add_edge("reminder", "chatbot")
builder.add_edge("search_internet", "chatbot")
builder.add_edge("search_currency_price", END)
builder.add_edge("brokerage_validation", "chatbot")
builder.add_edge("get_active_positions", "chatbot")
builder.add_edge("place_trade", "chatbot")
builder.add_edge("chatbot", END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
