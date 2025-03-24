from langchain_core.messages import HumanMessage
from typing import Literal
from bot.tools.helper import make_supervisor_node
from bot.custom_types import GenerativeUIState
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from bot.trade_team.tools.forext_account_tools import validate_account
llm = ChatOpenAI(model="gpt-4o")

request_account_information_agent = create_react_agent(llm, tools=[validate_account])
def request_account_information_and_validate_node(state: GenerativeUIState, config: RunnableConfig) -> Command[Literal["trade_supervisor"]]:
    result = request_account_information_agent.invoke(state, config)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="request_account_information_and_validate",)
            ]
        },
        # We want our workers to ALWAYS "report back" to the supervisor when done
        goto="trade_supervisor",
    )

trade_supervisor_node = make_supervisor_node(llm, ["request_account_information_and_validate"])