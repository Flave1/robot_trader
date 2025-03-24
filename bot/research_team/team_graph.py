
from bot.custom_types import GenerativeUIState
from langgraph.graph import StateGraph, START, END
from bot.research_team.worker_nodes import search_node, web_scraper_node, research_supervisor_node

research_builder = StateGraph(GenerativeUIState)
research_builder.add_node("research_supervisor", research_supervisor_node)
research_builder.add_node("search", search_node)
research_builder.add_node("web_scraper", web_scraper_node)

research_builder.add_edge(START, "research_supervisor")
research_builder.add_edge("search", END)
research_graph = research_builder.compile()