from src.agents.dap import data_acquisition_tool
from src.agents.laa import engineer_features_tool
from src.agents.msc import classify_market_state_tool
from src.agents.pp import price_prediction_tool
from src.agents.rm import risk_management_tool
from src.bot.tools.common_tools import get_active_trades_tool
from src.bot.custom_types import ActiveTradesInput, AnalysisInputModel, FeatureEngineerData, MarketStateClassifierInput, PricePredictionInputData, RiskManagementInputData
from src.bot.utils import extract_nested_fields
from src.bot.tools.full_pipeline_tool import full_pipeline_tool
from langgraph.types import StreamWriter
from langgraph.prebuilt.tool_node import ToolMessage

# Utility to extract fields from possibly nested dicts (copied from trade_nodes.py)


async def full_pipeline_node(input: AnalysisInputModel, writer: StreamWriter):
    extracted = extract_nested_fields(input, ['symbol', 'timeframe', 'trader_account_id', 'id'])
    symbol = extracted.get('symbol')
    timeframe = extracted.get('timeframe')
    tool_call_id = extracted.get('id')
    trader_account_id = extracted.get('trader_account_id') or 1

    if not symbol or not timeframe or not trader_account_id:
        return {
            "messages": [
                {"content": f"Missing required fields: symbol={symbol}, timeframe={timeframe}, trader_account_id={trader_account_id}", "tool_call_id": tool_call_id}
            ]
        }

    tool_input = {
        'symbol': symbol,
        'timeframe': timeframe,
        'trader_account_id': trader_account_id
    }

    # result = await full_pipeline_tool({'input': tool_input})
    result = await full_pipeline_tool.ainvoke({'input': tool_input})
    writer({"feedback_state": [{"feedback": result, "state": f"Full pipeline for {symbol}"}]})

    content = {"type": "json", "pipeline_result": [result]}    
    return {
    "messages": [ToolMessage(content=content, tool_call_id=tool_call_id)],
    "pipeline_result": [result]
    }



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
    extracted = extract_nested_fields(input, ['symbol', 'timeframe', 'features_df', 'id'])
    symbol = extracted.get('symbol')
    timeframe = extracted.get('timeframe')
    features_df = extracted.get('features_df')
    tool_call_id = extracted.get('id')

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
    extracted = extract_nested_fields(input, ['symbol', 'timeframe', 'features_df', 'id'])
    symbol = extracted.get('symbol')
    timeframe = extracted.get('timeframe')
    features_df = extracted.get('features_df')
    tool_call_id =  extracted.get('id')

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
    extracted = extract_nested_fields(input, ['symbol', 'timeframe', 'features_df', 'market_state', 'id'])
    symbol = extracted.get('symbol')
    timeframe = extracted.get('timeframe')
    features_df = extracted.get('features_df')
    market_state = extracted.get('market_state')
    tool_call_id = extracted.get('id')

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
    extracted = extract_nested_fields(input, ['trader_account_id', 'features_df', 'prediction_result', 'id'])
    trader_account_id = extracted.get('trader_account_id')
    features_df = extracted.get('features_df')
    prediction_result = extracted.get('prediction_result')
    tool_call_id = extracted.get('id')

    if not trader_account_id or features_df is None or prediction_result is None:
        return {
            "messages": [ToolMessage(content=f"Missing required fields: trader_account_id={trader_account_id}, features_df={features_df}, prediction_result={prediction_result}", tool_call_id=tool_call_id)]
        }

    tool_input = {'trader_account_id': trader_account_id, 'features_df': features_df, 'prediction_result': prediction_result, 'tool_call_id': tool_call_id}
    risk_result = await risk_management_tool({'input': tool_input})
    writer({"feedback_state": [
        {"feedback": risk_result, "state": f"Managing Risk"}
    ]})
    return {
        "messages": [ToolMessage(content={"type": "json", "data": risk_result}, tool_call_id=tool_call_id)],
        "risk_management": [{"search_status": "completed", "result": {"risk_result": risk_result}}]
    }

async def get_active_trades_node(input: ActiveTradesInput, writer: StreamWriter):
    extracted = extract_nested_fields(input, ['trader_account_id', 'id'])
    trader_account_id = extracted.get('trader_account_id')
    tool_call_id = extracted.get('id')

    if not trader_account_id:
        return {
            "messages": [ToolMessage(content="trader_account_id required", tool_call_id=tool_call_id)]
        }
    active_trades = get_active_trades_tool({'trader_account_id': trader_account_id})
    writer({"feedback_state": [
        {"feedback": f"Retrieved {len(active_trades) if isinstance(active_trades, list) else 0} active trades", "state": f"Fetching active trades for account {trader_account_id}"}
    ]})
    return {"messages": [ToolMessage(content={"type": "json", "data": active_trades}, tool_call_id=tool_call_id)], 
            "feedback_state": [{"feedback": "Fetched Active trades", "search_status": "", "result": active_trades}]}


