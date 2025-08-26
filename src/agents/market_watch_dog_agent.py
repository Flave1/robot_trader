from typing import Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from src.bot.tools.full_pipeline_tool import full_pipeline_tool
from src.bot.custom_types import AppState
from langgraph.types import Send

from src.core.bot_memory import get_memory

# Import all trading tools
from src.bot.tools.trading_tools import (
    list_orders_tool, get_order_tool, cancel_order_tool, replace_order_tool,
    create_order_tool, trade_execution_tool, list_trades_tool, get_trade_tool,
    close_trade_tool, update_trade_orders_tool, get_active_positions_tool
)

# Import all trading nodes
from src.bot.node.trade_nodes import (
    list_orders_node, get_order_node, cancel_order_node, replace_order_node,
    create_order_node, trade_execution_node, list_trades_node, get_trade_node,
    close_trade_node, update_trade_orders_node, get_active_positions_node
)

# Import existing nodes
from src.bot.node.full_pipeline_node import full_pipeline_node

load_dotenv()

async def chatbot(state: AppState, use_memory: bool = False):
    prompt = """
    You are the ARBIX Monitoring Agent—an advanced, modular AI system for autonomous trading and trade management.

    Your core capabilities include:
    - Running the full analysis pipeline for any currency pair, including data acquisition, feature engineering, market state classification, price prediction, and risk management, all in a single, explainable workflow.
    - Executing trades directly via broker APIs, with robust risk controls and automated trade logging.
    - Monitoring and managing active trades in real time, including the ability to fetch, review, and act on open positions.
    - Making intelligent, explainable decisions to open, hold, modify, or close trades based on live market data, risk exposure, and user-defined criteria.
    - Operating as a modular, node-based agent, where each step (analysis, execution, monitoring) is handled by a dedicated, auditable node/tool.

    Available Trading Operations:
    - Order Management: List, get, cancel, replace, and create orders (market, limit, stop)
    - Position Management: List trades, get trade details, close trades, update stop loss/take profit
    - Active Positions: Monitor and manage all open positions
    - Full Pipeline Analysis: Complete market analysis and trade decision pipeline

    Your mission is to maximize trading performance and risk-adjusted returns, while providing transparency, auditability, and continuous improvement in all trading operations.
    """
    
    messages = [{"role": "system", "content": prompt}] + state["messages"]
    
    # Only use memory if explicitly enabled
    if use_memory:
        thread_id = state.get("thread_id", "default_thread_id")
        memory = get_memory(thread_id)
        history = memory.load_memory_variables({"input": ""}).get("chat_history", [])
        if isinstance(history, str):
            history = [{"role": "user", "content": history}] if history.strip() else []
        messages = [{"role": "system", "content": prompt}] + history + state["messages"]

    llm = ChatOpenAI(
        model="gpt-4o-mini").bind_tools([
            # Full pipeline and analysis tools
            full_pipeline_tool,
            
            # Order management tools
            list_orders_tool,
            get_order_tool,
            cancel_order_tool,
            replace_order_tool,
            create_order_tool,
            trade_execution_tool,
            
            # Position/trade management tools
            list_trades_tool,
            get_trade_tool,
            close_trade_tool,
            update_trade_orders_tool,
            get_active_positions_tool
        ])
    
    response = await llm.ainvoke(messages)
    
    # Only save to memory if explicitly enabled and there are no tool calls
    if use_memory and not response.tool_calls and state["messages"]:
        thread_id = state.get("thread_id", "default_thread_id")
        memory = get_memory(thread_id)
        last_message = state["messages"][-1]
        if hasattr(last_message, "content"):
            input_content = last_message.content
        else:
            input_content = last_message["content"]
        memory.save_context(
            {"input": input_content},
            {"output": response.content}
        )
    
    return {"messages": [response]}

def assign_tool(state: AppState) -> Literal[
    "full_pipeline_node",
    "list_orders_node",
    "get_order_node",
    "cancel_order_node",
    "replace_order_node",
    "create_order_node",
    "trade_execution_node",
    "list_trades_node",
    "get_trade_node",
    "close_trade_node",
    "update_trade_orders_node",
    "get_active_positions_node",
    "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        send_list = []
        for tool in last_message.tool_calls:
            if tool["name"] == 'full_pipeline_tool':
                send_list.append(Send('full_pipeline_node', tool))
            elif tool["name"] == 'list_orders_tool':
                send_list.append(Send('list_orders_node', tool))
            elif tool["name"] == 'get_order_tool':
                send_list.append(Send('get_order_node', tool))
            elif tool["name"] == 'cancel_order_tool':
                send_list.append(Send('cancel_order_node', tool))
            elif tool["name"] == 'replace_order_tool':
                send_list.append(Send('replace_order_node', tool))
            elif tool["name"] == 'create_order_tool':
                send_list.append(Send('create_order_node', tool))
            elif tool["name"] == 'trade_execution_tool':
                send_list.append(Send('trade_execution_node', tool))
            elif tool["name"] == 'list_trades_tool':
                send_list.append(Send('list_trades_node', tool))
            elif tool["name"] == 'get_trade_tool':
                send_list.append(Send('get_trade_node', tool))
            elif tool["name"] == 'close_trade_tool':
                send_list.append(Send('close_trade_node', tool))
            elif tool["name"] == 'update_trade_orders_tool':
                send_list.append(Send('update_trade_orders_node', tool))
            elif tool["name"] == 'get_active_positions_tool':
                send_list.append(Send('get_active_positions_node', tool))
        return send_list if len(send_list) > 0 else "__end__"
    return "__end__"

builder = StateGraph(AppState)

# Add chatbot node
builder.add_node("chatbot", chatbot)

# Add analysis nodes
builder.add_node("full_pipeline_node", full_pipeline_node)

# Add order management nodes
builder.add_node("list_orders_node", list_orders_node)
builder.add_node("get_order_node", get_order_node)
builder.add_node("cancel_order_node", cancel_order_node)
builder.add_node("replace_order_node", replace_order_node)
builder.add_node("create_order_node", create_order_node)
builder.add_node("trade_execution_node", trade_execution_node)

# Add position/trade management nodes
builder.add_node("list_trades_node", list_trades_node)
builder.add_node("get_trade_node", get_trade_node)
builder.add_node("close_trade_node", close_trade_node)
builder.add_node("update_trade_orders_node", update_trade_orders_node)
builder.add_node("get_active_positions_node", get_active_positions_node)

# Add edges
builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", assign_tool)

# Analysis node edges
builder.add_edge("full_pipeline_node", "chatbot")

# Order management node edges
builder.add_edge("list_orders_node", "chatbot")
builder.add_edge("get_order_node", "chatbot")
builder.add_edge("cancel_order_node", "chatbot")
builder.add_edge("replace_order_node", "chatbot")
builder.add_edge("create_order_node", "chatbot")
builder.add_edge("trade_execution_node", "chatbot")

# Position/trade management node edges
builder.add_edge("list_trades_node", "chatbot")
builder.add_edge("get_trade_node", "chatbot")
builder.add_edge("close_trade_node", "chatbot")
builder.add_edge("update_trade_orders_node", "chatbot")
builder.add_edge("get_active_positions_node", "chatbot")

builder.add_edge("chatbot", END)

market_watch_dog_agent = builder.compile()
