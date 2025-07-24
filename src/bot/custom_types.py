import operator
from typing import Dict, List, Union, Any, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import pandas as pd
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
    symbol: str

class ToolNodeArgs(TypedDict):
    name: str
    args: dict[str, Any]
    id: str

class CurrencyPair(BaseModel):
    base_currency: str = Field(..., description="The first currency in a forex pair.")
    target_currency: str = Field(..., description="The second currency in a forex pair.")
    search_status: str
    result: str

class CommonUpdateType(BaseModel):
    label: str
    status: str
    result: str

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

class PipelineState(MessagesState):
    market_state: str

class WeatherInput(TypedDict):
    location: str
    tool_call_id: str


class ToolNodeArgs(TypedDict):
    name: str
    args: dict[str, Any]
    id: str


class InputQuery(BaseModel):
    query: str = Field(..., description="The query to search on the internet")


class FullPipelineRequest(BaseModel):
    symbol: str
    timeframe: str = 'M1'
    trader_account_id: int  # Add trader account ID
    account_balance: float
    risk_pct: float = 0.02
    units: float = None  # Optional, can be calculated
    sl: float = None
    tp: float = None
    price: float = None
    retries: int = 3
    use_llm: bool = False


class FeatureEngineerData(TypedDict):
    market_df: list[dict] = Field(..., description="market_df is the market data as a list of dicts")
    news_df:  list[dict] = Field(..., description="news_df is the news data as a list of dicts")    
    timeframe: str = Field(..., description="timeframe is the time frame for analysis")


class AnalysisInputModel(TypedDict):
    symbol: str = Field(..., description="Symbol/Currency Pair to be analysed")
    timeframe: str = Field(..., description="Time frame for analysis")
    tool_call_id: str

class MarketStateClassifierInput(BaseModel):
    features_df: list[dict] = Field(..., description="features_df is the features data as a list of dicts")


class PricePredictionInputData(TypedDict):
    features_df: list[dict] = Field(..., description="features_df is the feature data as a list of dicts")
    market_state: str = Field(..., description="market_state classfified market state")    

class RiskManagementInputData(TypedDict):
    features_df: list[dict] = Field(..., description="features_df is the feature data as a list of dicts")
    prediction_result: Dict = Field(..., description="prediction_result is the predicted result")
    account_id: int = Field(..., description="trader_account_id is the trader account Id")


class ActiveTradesInput(TypedDict):
    account_id: int
    tool_call_id: str
