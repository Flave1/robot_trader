from typing import List, Literal, Union, Dict, Any, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel
from typing import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from langgraph.graph import MessagesState
from pydantic.v1 import Field

class ChatInputType(BaseModel):
    input: List[Union[HumanMessage, AIMessage, SystemMessage]]

    class Config:
        arbitrary_types_allowed = True


class AppState(MessagesState):
    next: str

class GenerativeUIState(TypedDict, total=False):
    class Config:
       arbitrary_types_allowed = True
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: str
    messages: Annotated[list, add_messages]
    """Plain text response if no tool was used."""
    result: Optional[str]
    """A list of parsed tool calls."""
    tool_calls: Optional[List[dict]]
    """The result of a tool call."""
    tool_result: Optional[dict]
