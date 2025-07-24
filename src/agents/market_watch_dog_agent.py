from typing import Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from src.bot.node.trade_nodes import classify_market_state_node, data_acquisition_node, engineer_features_node, price_prediction_node, risk_management_node, get_active_trades_node
from src.agents.laa import engineer_features_tool
from src.agents.msc import classify_market_state_tool
from src.agents.pp import price_prediction_tool
from src.agents.rm import risk_management_tool
from src.agents.dap import data_acquisition_tool
from src.bot.tools.common_tools import get_active_trades_tool
from src.bot.custom_types import AppState
from langgraph.types import Send
from langgraph.checkpoint.memory import MemorySaver
from src.core.bot_memory import get_memory


load_dotenv()

async def chatbot(state: AppState, use_memory: bool = False):
    prompt = """
    You are an Expert Forex Trader AI Agent. Your role is majorly on checking the state a provided currency pair by using this workflow
    data_acquisition->engineer_features->classify_market_state->price_prediction->risk_management
    to manage and optimize active trades based on real-time market analysis and intelligent decision-making. Your core responsibilities include:
    Monitoring Active Trades: Constantly track open positions, including entry price, current price, volume, stop loss, and take profit levels.
    Trade Actions:
    Decide whether to hold, cancel, or execute trades based on live data, risk exposure, trend analysis, and trade objectives.
    Opportunity Detection:
    Continuously scan the forex market to identify profitable trading opportunities using strategies such as scalping, swing trading, or trend following.
    Trade Advisory:
    Based on current economic news, technical indicators, and price movements, advise whether to:
    Cancel a risky or unprofitable open trade.
    Hold a trade that's in motion but not yet reached its target.
    Execute a new trade with parameters (pair, direction, volume, stop loss, take profit).
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
        model="gpt-4o-mini").bind_tools([data_acquisition_tool, 
                                     engineer_features_tool, 
                                     classify_market_state_tool, 
                                     price_prediction_tool, 
                                     risk_management_tool, 
                                     get_active_trades_tool])
    
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


# Chatbot node router. Based on tool calls, creates the list of the next parallel nodes.
def assign_tool(state: AppState) -> Literal["data_acquisition_node", 
                                            "engineer_features_node", 
                                            "classify_market_state_node",
                                            "price_prediction_node",
                                            "risk_management_node", 
                                            "get_active_trades_node", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]
    if last_message.tool_calls:
        send_list = []
        for tool in last_message.tool_calls:
            if tool["name"] == 'data_acquisition_tool':
                send_list.append(Send('data_acquisition_node', tool))
            elif tool["name"] == 'engineer_features_tool':
                send_list.append(Send('engineer_features_node', tool))
            elif tool["name"] == 'classify_market_state_tool':
                send_list.append(Send('classify_market_state_node', tool))
            elif tool["name"] == 'price_prediction_tool':
                send_list.append(Send('price_prediction_node', tool))
            elif tool["name"] == 'risk_management_tool':
                send_list.append(Send('risk_management_node', tool))
            elif tool["name"] == 'get_active_trades_tool':
                  send_list.append(Send('get_active_trades_node', {'account_id': tool['args']['account_id'], 'tool_call_id': tool['id']}))
        return send_list if len(send_list) > 0 else "__end__"
    return "__end__"


builder = StateGraph(AppState)

builder.add_node("chatbot", chatbot)
builder.add_node("data_acquisition_node", data_acquisition_node)
builder.add_node("engineer_features_node", engineer_features_node)
builder.add_node("classify_market_state_node", classify_market_state_node)
builder.add_node("price_prediction_node", price_prediction_node)
builder.add_node("risk_management_node", risk_management_node)
builder.add_node("get_active_trades_node", get_active_trades_node)
builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", assign_tool)
builder.add_edge("data_acquisition_node", "chatbot")
builder.add_edge("engineer_features_node", "classify_market_state_node")
builder.add_edge("classify_market_state_node", "price_prediction_node")
builder.add_edge("price_prediction_node", "chatbot")
builder.add_edge("risk_management_node", "chatbot")
builder.add_edge("get_active_trades_node", "chatbot")
builder.add_edge("chatbot", END)

memory = MemorySaver()
market_watch_dog_agent = builder.compile(checkpointer=memory)
