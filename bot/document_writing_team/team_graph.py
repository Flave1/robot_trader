
from bot.custom_types import GenerativeUIState
from langgraph.graph import StateGraph, START
from bot.document_writing_team.worker_nodes import doc_writing_supervisor_node, doc_writing_node, note_taking_node, chart_generating_node
# Create the graph here
paper_writing_builder = StateGraph(GenerativeUIState)
paper_writing_builder.add_node("doc_writing_supervisor", doc_writing_supervisor_node)
paper_writing_builder.add_node("doc_writer", doc_writing_node)
paper_writing_builder.add_node("note_taker", note_taking_node)
paper_writing_builder.add_node("chart_generator", chart_generating_node)

paper_writing_builder.add_edge(START, "doc_writing_supervisor")
paper_writing_graph = paper_writing_builder.compile()