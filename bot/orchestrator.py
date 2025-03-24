from bot.custom_types import GenerativeUIState
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langgraph.graph import StateGraph, START, END
from langgraph.graph.graph import CompiledGraph
from typing import Literal
from bot.tools.helper import make_supervisor_node
from bot.research_team.team_graph import research_graph
from langchain_core.messages import HumanMessage
from bot.document_writing_team.team_graph import paper_writing_graph
from bot.trade_team.team_graph import trading_graph
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

teams_supervisor_node = make_supervisor_node(llm, ["research_team", "writing_team", "trade_team"])

def call_research_team(state: GenerativeUIState, config: RunnableConfig) -> Command[Literal["teams_supervisor"]]:
    response = research_graph.invoke({"messages": [state["messages"][-1]]}, config)
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=response["messages"][-1].content, name="research_team"
                )
            ]
        },
        goto="teams_supervisor",
    )


def call_paper_writing_team(state: GenerativeUIState, config: RunnableConfig) -> Command[Literal["teams_supervisor"]]:
    response = paper_writing_graph.invoke({"messages": [state["messages"][-1]]}, config)
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=response["messages"][-1].content, name="writing_team"
                )
            ]
        },
        goto="teams_supervisor",
    )

def call_trade_team(state: GenerativeUIState, config: RunnableConfig) -> Command[Literal["teams_supervisor"]]:
    response =  trading_graph.invoke({"messages": state["messages"][-1]}, config)
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=response["messages"][-1].content, name="trade_team"
                )
            ]
        },
        goto="teams_supervisor",
    )

def create_graph() -> CompiledGraph:
    super_builder = StateGraph(GenerativeUIState)
    super_builder.add_node("teams_supervisor", teams_supervisor_node)
    super_builder.add_node("research_team", call_research_team)
    super_builder.add_node("writing_team", call_paper_writing_team)
    super_builder.add_node("trade_team", call_trade_team)
    super_builder.add_edge(START, "teams_supervisor")
    super_builder.add_edge("research_team", END)
    super_builder.add_edge("writing_team", END)
    super_builder.add_edge("trade_team", END)
    memory = MemorySaver()
    super_graph = super_builder.compile(checkpointer=memory)
    return super_graph

graph = create_graph()
