from langgraph.types import StreamWriter
from src.bot.custom_types import ActiveTradesInput, AnalysisInputModel
from src.agents.dap import data_acquisition_tool
# from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolMessage
from src.agents.laa import FeatureEngineerData, engineer_features_tool
from src.agents.msc import MarketStateClassifierInput, classify_market_state_tool
from src.agents.pp import PricePredictionInputData, price_prediction_tool
from src.agents.rm import RiskManagementInputData, risk_management_tool
from src.bot.tools.common_tools import get_active_trades_tool


# Generic utility to extract fields from possibly nested dicts

def extract_nested_fields(input_obj, field_names):
    """
    Recursively search for the given field_names in a possibly nested dict (under 'input', 'args', etc).
    Returns a dict of found fields.
    """
    found = {}
    if isinstance(input_obj, dict):
        # Check if any field is present at this level
        for field in field_names:
            if field in input_obj:
                found[field] = input_obj[field]
        # If all found, return
        if len(found) == len(field_names):
            return found
        # Otherwise, search nested dicts
        for key in ['input', 'args']:
            if key in input_obj and isinstance(input_obj[key], dict):
                nested_found = extract_nested_fields(input_obj[key], field_names)
                found.update(nested_found)
                if len(found) == len(field_names):
                    return found
    return found


async def data_acquisition_node(input: AnalysisInputModel, writer: StreamWriter):
    extracted = extract_nested_fields(input, ['symbol', 'timeframe', 'id'])
    symbol = extracted.get('symbol')
    timeframe = extracted.get('timeframe')
    tool_call_id = extracted.get('id')

    if not symbol or not timeframe:
        return {
            "messages": [ToolMessage(content=f"Missing required fields: symbol={symbol}, timeframe={timeframe}", tool_call_id=tool_call_id)]
        }

    # writer({"feedback_state": [
    #     {"feedback": extracted, "state": f"Acquiring market data and news to analyse {extracted}"}
    # ]})

    tool_input = {'symbol': symbol, 'timeframe': timeframe, 'tool_call_id': tool_call_id}

    market_data, news_data = data_acquisition_tool({'input': tool_input})

    content = {"type": "json", "market_data": market_data, "news_data": news_data}
    return {
        "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)],
        "data_acquisition": [{"symbol": content, "search_status": "completed", "result": {"market_data": market_data, "news_data": news_data}}]
    }


async def engineer_features_node(input: FeatureEngineerData, writer: StreamWriter):
    extracted = extract_nested_fields(input, ['symbol', 'timeframe', 'features_df', 'tool_call_id'])
    symbol = extracted.get('symbol')
    timeframe = extracted.get('timeframe')
    features_df = extracted.get('features_df')
    tool_call_id = extracted.get('tool_call_id') or extracted.get('id')

    if not symbol or not timeframe or features_df is None:
        return {
            "messages": [ToolMessage(content=f"Missing required fields: symbol={symbol}, timeframe={timeframe}, features_df={features_df}", tool_call_id=tool_call_id)]
        }

    tool_input = {'symbol': symbol, 'timeframe': timeframe, 'features_df': features_df, 'tool_call_id': tool_call_id}
    features_result = engineer_features_tool({'input': tool_input})

    writer({"feedback_state": [
        {"feedback": tool_input, "state": f"Feature engineering"}
    ]})
    return {
        "messages": [ToolMessage(content={"type": "json", "data": features_result}, tool_call_id=tool_call_id)],
        "feature_engineering": [{"search_status": "completed", "result": {"features_data": features_result}}]
    }

async def classify_market_state_node(input: MarketStateClassifierInput, writer: StreamWriter):
    extracted = extract_nested_fields(input, ['symbol', 'timeframe', 'features_df', 'tool_call_id'])
    symbol = extracted.get('symbol')
    timeframe = extracted.get('timeframe')
    features_df = extracted.get('features_df')
    tool_call_id = extracted.get('tool_call_id') or extracted.get('id')

    if not symbol or not timeframe or features_df is None:
        return {
            "messages": [ToolMessage(content=f"Missing required fields: symbol={symbol}, timeframe={timeframe}, features_df={features_df}", tool_call_id=tool_call_id)]
        }

    tool_input = {'symbol': symbol, 'timeframe': timeframe, 'features_df': features_df, 'tool_call_id': tool_call_id}
    market_state = await classify_market_state_tool({'input': tool_input})

    writer({"feedback_state": [
        {"feedback": market_state, "state": f"Classifying market"}
    ]})
    return {
        "messages": [ToolMessage(content={"type": "json", "data": market_state}, tool_call_id=tool_call_id)],
        "market_state_classification": [{"search_status": "completed", "result": {"market_state": market_state}}]
    }


async def price_prediction_node(input: PricePredictionInputData, writer: StreamWriter):
    extracted = extract_nested_fields(input, ['symbol', 'timeframe', 'features_df', 'market_state', 'tool_call_id'])
    symbol = extracted.get('symbol')
    timeframe = extracted.get('timeframe')
    features_df = extracted.get('features_df')
    market_state = extracted.get('market_state')
    tool_call_id = extracted.get('tool_call_id') or extracted.get('id')

    if not symbol or not timeframe or features_df is None or market_state is None:
        return {
            "messages": [ToolMessage(content=f"Missing required fields: symbol={symbol}, timeframe={timeframe}, features_df={features_df}, market_state={market_state}", tool_call_id=tool_call_id)]
        }

    tool_input = {'symbol': symbol, 'timeframe': timeframe, 'features_df': features_df, 'market_state': market_state, 'tool_call_id': tool_call_id}
    prediction_result = price_prediction_tool({'input': tool_input})

    writer({"feedback_state": [
        {"feedback": prediction_result, "state": f"Predicting Price"}
    ]})

    return {
        "messages": [ToolMessage(content="Price prediction completed", tool_call_id=tool_call_id)],
        "price_prediction": [{"search_status": "completed", "result": {"prediction_result": prediction_result}}]
    }


async def risk_management_node(input: RiskManagementInputData, writer: StreamWriter):
    extracted = extract_nested_fields(input, ['account_id', 'features_df', 'prediction_result', 'tool_call_id'])
    account_id = extracted.get('account_id')
    features_df = extracted.get('features_df')
    prediction_result = extracted.get('prediction_result')
    tool_call_id = extracted.get('tool_call_id') or extracted.get('id')

    if not account_id or features_df is None or prediction_result is None:
        return {
            "messages": [ToolMessage(content=f"Missing required fields: account_id={account_id}, features_df={features_df}, prediction_result={prediction_result}", tool_call_id=tool_call_id)]
        }

    tool_input = {'account_id': account_id, 'features_df': features_df, 'prediction_result': prediction_result, 'tool_call_id': tool_call_id}
    risk_result = await risk_management_tool({'input': tool_input})
    writer({"feedback_state": [
        {"feedback": risk_result, "state": f"Managing Risk"}
    ]})
    return {
        "messages": [ToolMessage(content={"type": "json", "data": risk_result}, tool_call_id=tool_call_id)],
        "risk_management": [{"search_status": "completed", "result": {"risk_result": risk_result}}]
    }

async def get_active_trades_node(input: ActiveTradesInput, writer: StreamWriter):
    extracted = extract_nested_fields(input, ['account_id', 'tool_call_id'])
    account_id = extracted.get('account_id')
    tool_call_id = extracted.get('tool_call_id') or extracted.get('id')

    if not account_id:
        return {
            "messages": [ToolMessage(content="account_id required", tool_call_id=tool_call_id)]
        }
    active_trades = get_active_trades_tool({'account_id': account_id})
    writer({"feedback_state": [
        {"feedback": f"Retrieved {len(active_trades) if isinstance(active_trades, list) else 0} active trades", "state": f"Fetching active trades for account {account_id}"}
    ]})
    return {"messages": [ToolMessage(content={"type": "json", "data": active_trades}, tool_call_id=tool_call_id)], 
            "feedback_state": [{"feedback": "Fetched Active trades", "search_status": "", "result": active_trades}]}