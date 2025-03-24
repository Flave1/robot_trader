from langchain_core.messages import HumanMessage
from typing import Literal
from bot.tools.helper import make_supervisor_node
from bot.research_team.tools.web_scrapper import scrape_webpages
from bot.custom_types import GenerativeUIState
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from bot.research_team.tools.internet_search import tavily_tool
from langchain_core.runnables import RunnableConfig

llm = ChatOpenAI(model="gpt-4o-mini")

search_agent = create_react_agent(llm, tools=[tavily_tool])


def search_node(state: GenerativeUIState, config: RunnableConfig) -> Command[Literal["research_supervisor"]]:
    result = search_agent.invoke(state, config)
    return Command(
        update={
            "messages": [
                HumanMessage(
                    content=result["messages"][-1].content, 
                    name="search",
                    additional_kwargs={"tool_calls": result["messages"][-1].tool_calls}
                )
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="research_supervisor",
    )


web_scraper_agent = create_react_agent(llm, tools=[scrape_webpages])


def web_scraper_node(state: GenerativeUIState, config: RunnableConfig) -> Command[Literal["research_supervisor"]]:
    result = web_scraper_agent.invoke(state, config)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="web_scraper")
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="research_supervisor",
    )


research_supervisor_node = make_supervisor_node(llm, ["search", "web_scraper"])

