from typing import Literal, List
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
import uuid
from bot.custom_types import GenerativeUIState
from langgraph.graph import END
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage

def make_supervisor_node(llm: ChatOpenAI, team_names: list[str]):
    prompt = """You are a specialized trading assistant with two distinct roles:

1. TRADING EXPERTISE:
- Your primary function is to help users manage and execute trades across forex, crypto, and stock markets
- You can engage in detailed trading-related conversations, provide market analysis, and assist with trade execution
- You understand trading terminology, market dynamics, and can explain complex trading concepts
- You can help with portfolio management, risk assessment, and trading strategy development

2. TEAM COORDINATION BETWEEN {team_names}: OR Respond with "FINISH" when yo are done

IMPORTANT:
- Stay focused on trading-related topics and market operations
- Never engage in non-trading related discussions
- Maintain professional trading expertise in all responses
- If a query is not trading-related, politely redirect to trading topics
- Respond with "FINISH" and include your answer when you are done routing btween {team_names}
"""
    
    options = ["FINISH"] + team_names

    class Router(TypedDict):
        """Worker to route to next. If no workers needed, route to FINISH."""
        next: Literal[*options]
        messages: List[dict]  # Simple list of dictionaries for messages

    def supervisor_node(state: GenerativeUIState, config: RunnableConfig) -> Command[Literal[*team_names, "__end__"]]:
        """An LLM-based router."""
        messages = [
            {"role": "system", "content": prompt},
        ] + state["messages"]
        response = llm.with_structured_output(Router).invoke(messages, config)
        print("response", response)
        
        # Handle missing 'next' key with default value
        goto = response.get("next", "FINISH")
        if goto == "FINISH":
            goto = END
        
        # Extract content from the response messages
        content = ""
        if response.get("messages") and len(response["messages"]) > 0:
            content = response["messages"][0].get("message", "")
        
        print("content", content)
        message = AIMessage(
            content=content,
            tool_calls=[],
            type="ai",
            response_metadata={
                'finish_reason': 'stop',
                'model_name': llm.model_name,  
                'system_fingerprint': config.get('system_fingerprint', 'fp_default')
            },
            id=f'run-{uuid.uuid4()}'
        )
        return Command(goto=goto, update={"messages": [message]})

    return supervisor_node