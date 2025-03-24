
from bot.custom_types import GenerativeUIState
from langgraph.graph import StateGraph, START, END
from bot.trade_team.worker_nodes import request_account_information_and_validate_node, trade_supervisor_node

trade_builder = StateGraph(GenerativeUIState)
trade_builder.add_node("trade_supervisor", trade_supervisor_node)
trade_builder.add_node("request_account_information_and_validate", request_account_information_and_validate_node)

trade_builder.add_edge(START, "trade_supervisor")
trade_builder.add_edge("request_account_information_and_validate", END)

trading_graph = trade_builder.compile()