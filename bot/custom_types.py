import operator
from typing import List, Union, Any, Optional

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

class CurrencyPair(BaseModel):
    base_currency: str = Field(..., description="The first currency in a forex pair.")
    target_currency: str = Field(..., description="The second currency in a forex pair.")
    search_status: str
    result: str


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



class Weather(TypedDict):
    location: str
    search_status: str
    result: str

class Currency(TypedDict):
    currency: str
    search_status: str
    result: str


class State(MessagesState):
    weather_forecast: Annotated[list[Weather], operator.add]
    currency_result: Annotated[list[Currency], operator.add]


class WeatherInput(TypedDict):
    location: str
    tool_call_id: str


class ToolNodeArgs(TypedDict):
    name: str
    args: dict[str, Any]
    id: str


class InputQuery(BaseModel):
    query: str = Field(..., description="The query to search on the internet")

